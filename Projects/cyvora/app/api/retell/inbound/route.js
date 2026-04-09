import { NextResponse } from "next/server";

function readRequiredEnv(name) {
  const value = process.env[name];

  if (!value || value.startsWith("replace-with-")) {
    throw new Error(`Missing ${name}.`);
  }

  return value;
}

export async function POST() {
  try {
    const companyId = readRequiredEnv("RETELL_INBOUND_COMPANY_ID");
    const agentId = process.env.RETELL_INBOUND_AGENT_ID || null;

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
