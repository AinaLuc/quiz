import crypto from "node:crypto";

function toIsoDate(value) {
  if (!value && value !== 0) {
    return null;
  }

  const numericValue =
    typeof value === "number" || /^\d+$/.test(String(value)) ? Number(value) : value;
  const date = new Date(numericValue);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function pick(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

function isPlaceholder(value) {
  return typeof value === "string" && value.startsWith("replace-with-");
}

function parseSignature(headerValue) {
  if (!headerValue) {
    return null;
  }

  const match = /^v=(\d+),d=([a-fA-F0-9]+)$/.exec(headerValue.trim());
  if (!match) {
    return null;
  }

  return {
    timestamp: match[1],
    digest: match[2].toLowerCase(),
  };
}

export function verifyRetellRequest(rawBody, signatureHeader) {
  const apiKey = process.env.RETELL_API_KEY;

  if (!apiKey || isPlaceholder(apiKey)) {
    return true;
  }

  const signature = parseSignature(signatureHeader);

  if (!signature) {
    return false;
  }

  const now = Date.now();
  const timestamp = Number(signature.timestamp);

  if (!Number.isFinite(timestamp) || Math.abs(now - timestamp) > 5 * 60 * 1000) {
    return false;
  }

  const digest = crypto
    .createHmac("sha256", apiKey)
    .update(`${rawBody}${signature.timestamp}`, "utf8")
    .digest("hex");
  const expectedBuffer = Buffer.from(digest, "hex");
  const receivedBuffer = Buffer.from(signature.digest, "hex");

  if (expectedBuffer.length !== receivedBuffer.length) {
    return false;
  }

  return crypto.timingSafeEqual(expectedBuffer, receivedBuffer);
}

export function extractRetellCallPayload(payload) {
  const call = payload?.call || {};
  const analysis = call?.call_analysis || {};
  const structured =
    pick(analysis?.custom_analysis_data, call?.collected_dynamic_variables, call?.metadata) || {};

  return {
    externalCallId: call?.call_id || null,
    assistantId: pick(call?.agent_id, call?.agent_name) || null,
    customerNumber: pick(call?.from_number, call?.to_number) || null,
    startedAt: toIsoDate(call?.start_timestamp),
    endedAt: toIsoDate(call?.end_timestamp),
    durationSeconds:
      Number.isFinite(Number(call?.duration_ms)) && Number(call?.duration_ms) > 0
        ? Math.round(Number(call.duration_ms) / 1000)
        : null,
    status: pick(payload?.event, call?.call_status, "unknown"),
    endedReason: call?.disconnection_reason || null,
    summary: pick(analysis?.call_summary, analysis?.summary) || null,
    transcript:
      typeof call?.transcript === "string"
        ? call.transcript
        : call?.transcript
          ? JSON.stringify(call.transcript)
          : null,
    recordingUrl:
      pick(
        call?.recording_url,
        call?.recording_multi_channel_url,
        call?.scrubbed_recording_url,
        call?.scrubbed_recording_multi_channel_url,
      ) || null,
    urgency:
      pick(
        structured?.urgency,
        structured?.priority,
        structured?.niveau_urgence,
        structured?.urgence,
      ) || null,
    bookingStatus:
      pick(
        structured?.bookingStatus,
        structured?.appointmentStatus,
        structured?.status,
        structured?.reservation_status,
      ) || null,
    structuredData: structured && Object.keys(structured).length ? structured : null,
  };
}

export function extractRetellAppointmentPayload(callRecord) {
  const structured = callRecord.structuredData || {};
  const scheduledFor = toIsoDate(
    pick(
      structured?.appointmentTime,
      structured?.appointmentDateTime,
      structured?.scheduledFor,
      structured?.scheduled_at,
      structured?.appointment_start,
      structured?.creneau,
    ),
  );
  const rawStatus = (
    callRecord.bookingStatus ||
    (structured?.appointmentBooked ? "confirmed" : null) ||
    (structured?.booked ? "confirmed" : null) ||
    (structured?.reservation_confirmee ? "confirmed" : null) ||
    ""
  ).toString();
  const normalizedStatus = rawStatus.toLowerCase();
  const isBooked =
    ["confirmed", "booked", "scheduled", "confirme", "confirmé"].includes(normalizedStatus) ||
    structured?.appointmentBooked === true ||
    structured?.booked === true ||
    structured?.reservation_confirmee === true;

  if (!isBooked) {
    return null;
  }

  return {
    status: normalizedStatus || "confirmed",
    scheduledFor,
    contactPhone: callRecord.customerNumber,
  };
}
