import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  extractRetellAppointmentPayload,
  extractRetellCallPayload,
  verifyRetellRequest,
} from "@/lib/retell";

async function findDefaultCompanyId(supabase) {
  const { data, error } = await supabase
    .from("companies")
    .select("id")
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return data?.id || null;
}

export async function POST(request) {
  const rawBody = await request.text();

  if (!verifyRetellRequest(rawBody, request.headers.get("x-retell-signature"))) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let payload;

  try {
    payload = JSON.parse(rawBody || "{}");
  } catch {
    return NextResponse.json({ error: "Invalid JSON payload." }, { status: 400 });
  }

  const event = payload?.event;

  if (!["call_started", "call_ended", "call_analyzed"].includes(event || "")) {
    return NextResponse.json({ ignored: true, reason: `Unsupported Retell event: ${event || "unknown"}` });
  }

  const callRecord = extractRetellCallPayload(payload);

  if (!callRecord.externalCallId) {
    return NextResponse.json(
      { ignored: true, reason: "Missing call id in Retell payload." },
      { status: 202 },
    );
  }

  const supabase = createAdminClient();
  const companyId =
    payload?.call?.metadata?.companyId ||
    payload?.call?.metadata?.company_id ||
    (await findDefaultCompanyId(supabase));

  if (!companyId) {
    return NextResponse.json(
      { error: "No company found. Send companyId in Retell metadata or create a company first." },
      { status: 400 },
    );
  }

  const { data: callRow, error: callError } = await supabase
    .from("calls")
    .upsert(
      {
        company_id: companyId,
        external_call_id: callRecord.externalCallId,
        assistant_id: callRecord.assistantId,
        customer_number: callRecord.customerNumber,
        started_at: callRecord.startedAt,
        ended_at: callRecord.endedAt,
        duration_seconds: callRecord.durationSeconds,
        status: callRecord.status,
        ended_reason: callRecord.endedReason,
        summary: callRecord.summary,
        transcript: callRecord.transcript,
        recording_url: callRecord.recordingUrl,
        urgency: callRecord.urgency,
        booking_status: callRecord.bookingStatus,
        raw_payload: payload,
        structured_data: callRecord.structuredData,
      },
      { onConflict: "external_call_id" },
    )
    .select("id, external_call_id")
    .single();

  if (callError) {
    return NextResponse.json({ error: callError.message }, { status: 500 });
  }

  const appointment = extractRetellAppointmentPayload(callRecord);

  if (appointment) {
    const { error: appointmentError } = await supabase.from("appointments").upsert(
      {
        company_id: companyId,
        call_id: callRow.id,
        external_call_id: callRecord.externalCallId,
        contact_phone: appointment.contactPhone,
        scheduled_for: appointment.scheduledFor,
        status: appointment.status,
      },
      { onConflict: "external_call_id" },
    );

    if (appointmentError) {
      return NextResponse.json({ error: appointmentError.message }, { status: 500 });
    }
  }

  return new NextResponse(null, { status: 204 });
}
