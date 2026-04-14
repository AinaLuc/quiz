import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { extractAppointmentPayload, extractCallPayload, verifyVapiRequest } from "@/lib/vapi";

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
  if (!verifyVapiRequest(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = await request.json();
  const callRecord = extractCallPayload(payload);

  if (!callRecord.externalCallId) {
    return NextResponse.json(
      { ignored: true, reason: "Missing call id in Vapi payload." },
      { status: 202 },
    );
  }

  const supabase = createAdminClient();
  const companyId =
    payload?.metadata?.companyId ||
    payload?.message?.metadata?.companyId ||
    payload?.call?.metadata?.companyId ||
    (await findDefaultCompanyId(supabase));

  if (!companyId) {
    return NextResponse.json(
      { error: "No company found. Send companyId in Vapi metadata or create a company first." },
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

  const appointment = extractAppointmentPayload(callRecord);

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

  return NextResponse.json({ ok: true, callId: callRow.external_call_id });
}
