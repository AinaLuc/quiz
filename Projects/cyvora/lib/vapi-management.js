function getVapiApiKey() {
  const apiKey = process.env.VAPI_API_KEY;

  if (!apiKey) {
    throw new Error("Missing VAPI_API_KEY.");
  }

  return apiKey;
}

export async function listVapiPhoneNumbers() {
  const apiKey = getVapiApiKey();

  const response = await fetch("https://api.vapi.ai/phone-number", {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Vapi phone-number fetch failed (${response.status}).`);
  }

  const payload = await response.json();
  const phoneNumbers = Array.isArray(payload) ? payload : [];

  return phoneNumbers.map((phoneNumber) => ({
    id: phoneNumber.id,
    number: phoneNumber.number || null,
    name: phoneNumber.name || null,
    assistantId: phoneNumber.assistantId || null,
    status: phoneNumber.status || "unknown",
    serverUrl: phoneNumber.server?.url || null,
  }));
}
