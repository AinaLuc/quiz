import { NextResponse } from "next/server";
import { verifyRetellRequest } from "@/lib/retell";
import { resolveInboundRetellConfig } from "@/lib/retell-inbound-config";

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
