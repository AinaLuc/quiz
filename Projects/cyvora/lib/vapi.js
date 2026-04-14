function toIsoDate(value) {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function pick(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

export function verifyVapiRequest(request) {
  const expectedSecret = process.env.VAPI_WEBHOOK_SECRET;

  if (!expectedSecret || expectedSecret.startsWith("replace-with-")) {
    return true;
  }

  const authorization = request.headers.get("authorization");
  const bearer = authorization?.startsWith("Bearer ")
    ? authorization.slice("Bearer ".length)
    : null;
  const legacySecret = request.headers.get("x-vapi-secret");

  return bearer === expectedSecret || legacySecret === expectedSecret;
}

export function extractCallPayload(payload) {
  const message = payload?.message || {};
  const call = payload?.call || message?.call || {};
  const artifact = payload?.artifact || message?.artifact || {};
  const analysis = payload?.analysis || artifact?.analysis || {};
  const customer = payload?.customer || call?.customer || {};
  const assistant = payload?.assistant || call?.assistant || {};

  const transcript =
    pick(artifact?.transcript, analysis?.transcript, message?.transcript, payload?.transcript) ||
    null;
  const structured =
    pick(analysis?.structuredData, artifact?.structuredData, payload?.structuredData) || {};

  return {
    externalCallId: pick(call?.id, payload?.callId, message?.callId),
    assistantId: pick(assistant?.id, call?.assistantId, payload?.assistantId),
    customerNumber:
      pick(
        customer?.number,
        customer?.phoneNumber,
        customer?.phone,
        call?.phoneNumber?.number,
        call?.phoneNumber,
      ) || null,
    startedAt: toIsoDate(pick(call?.startedAt, message?.startedAt, payload?.startedAt)),
    endedAt: toIsoDate(pick(call?.endedAt, message?.endedAt, payload?.endedAt)),
    durationSeconds:
      Number(pick(call?.durationSeconds, message?.durationSeconds, payload?.durationSeconds)) ||
      null,
    status: pick(message?.type, payload?.type, call?.status, "unknown"),
    endedReason: pick(call?.endedReason, message?.endedReason, payload?.endedReason) || null,
    summary: pick(analysis?.summary, artifact?.summary, message?.summary, payload?.summary) || null,
    transcript: typeof transcript === "string" ? transcript : transcript ? JSON.stringify(transcript) : null,
    recordingUrl:
      pick(
        artifact?.recordingUrl,
        artifact?.recording?.stereoUrl,
        artifact?.recording?.monoUrl,
        call?.recordingUrl,
      ) || null,
    urgency: pick(structured?.urgency, structured?.priority, analysis?.priority) || null,
    bookingStatus:
      pick(structured?.bookingStatus, structured?.appointmentStatus, structured?.status) || null,
    structuredData: structured && Object.keys(structured).length ? structured : null,
  };
}

export function extractAppointmentPayload(callRecord) {
  const structured = callRecord.structuredData || {};
  const scheduledFor = toIsoDate(
    pick(structured?.appointmentTime, structured?.appointmentDateTime, structured?.scheduledFor),
  );
  const rawStatus = (
    callRecord.bookingStatus ||
    (structured?.appointmentBooked ? "confirmed" : null) ||
    (structured?.booked ? "confirmed" : null) ||
    ""
  ).toString();
  const normalizedStatus = rawStatus.toLowerCase();
  const isBooked =
    ["confirmed", "booked", "scheduled"].includes(normalizedStatus) ||
    structured?.appointmentBooked === true ||
    structured?.booked === true;

  if (!isBooked) {
    return null;
  }

  return {
    status: normalizedStatus || "confirmed",
    scheduledFor,
    contactPhone: callRecord.customerNumber,
  };
}
