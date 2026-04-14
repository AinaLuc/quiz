import Retell from "retell-sdk";
import { normalizePhoneNumber } from "@/lib/retell-inbound-config";

function getRetellApiKey() {
  const apiKey = process.env.RETELL_API_KEY;

  if (!apiKey || apiKey.startsWith("replace-with-")) {
    throw new Error("Missing API key.");
  }

  return apiKey;
}

function getRetellClient() {
  return new Retell({
    apiKey: getRetellApiKey(),
  });
}

export async function listRetellPhoneNumbers() {
  const client = getRetellClient();
  const response = await client.phoneNumber.list();
  const phoneNumbers = Array.isArray(response) ? response : [];

  return phoneNumbers
    .map((phoneNumber) => ({
      id: normalizePhoneNumber(phoneNumber.phone_number) || phoneNumber.phone_number,
      phoneNumber: normalizePhoneNumber(phoneNumber.phone_number) || phoneNumber.phone_number,
      displayNumber: phoneNumber.phone_number_pretty || phoneNumber.phone_number,
      name: phoneNumber.nickname || null,
      inboundAgentId: phoneNumber.inbound_agent_id || null,
      inboundAgents: Array.isArray(phoneNumber.inbound_agents) ? phoneNumber.inbound_agents : [],
      outboundAgentId: phoneNumber.outbound_agent_id || null,
      phoneNumberType: phoneNumber.phone_number_type || null,
      inboundWebhookUrl: phoneNumber.inbound_webhook_url || null,
      lastModifiedAt: phoneNumber.last_modification_timestamp || null,
      isAssigned:
        Boolean(phoneNumber.inbound_agent_id) ||
        (Array.isArray(phoneNumber.inbound_agents) && phoneNumber.inbound_agents.length > 0) ||
        Boolean(phoneNumber.inbound_webhook_url),
    }))
    .sort((left, right) => left.displayNumber.localeCompare(right.displayNumber));
}
