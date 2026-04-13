import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { verifyRetellRequest } from "@/lib/retell";
import { normalizePhoneNumber, resolveInboundRetellConfig } from "@/lib/retell-inbound-config";

export async function POST(request) {
  try {
    const rawBody = await request.text();

    if (!(await verifyRetellRequest(rawBody, request.headers.get("x-retell-signature")))) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    let payload;

    try {
      payload = JSON.parse(rawBody || "{}");
    } catch {
      return NextResponse.json({ error: "Invalid JSON payload." }, { status: 400 });
    }

    const toNumber = payload?.call_inbound?.to_number;
    const supabase = createAdminClient();
    const normalizedToNumber = normalizePhoneNumber(toNumber);
    const { data: assignment } = normalizedToNumber
      ? await supabase
          .from("retell_phone_assignments")
          .select("company_id, inbound_agent_id")
          .eq("phone_number", normalizedToNumber)
          .maybeSingle()
      : { data: null };

    if (assignment?.company_id) {
      return NextResponse.json({
        call_inbound: {
          ...(assignment.inbound_agent_id ? { override_agent_id: assignment.inbound_agent_id } : {}),
          metadata: {
            companyId: assignment.company_id,
          },
        },
      });
    }

    const { companyId, agentId } = resolveInboundRetellConfig(toNumber);

    return NextResponse.json({
      call_inbound: {
        ...(agentId ? { override_agent_id: agentId } : {}),
        metadata: {
          companyId,
        },
      },
    });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
