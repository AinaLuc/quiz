function isPlaceholder(value) {
  return typeof value === "string" && value.startsWith("replace-with-");
}

export function normalizePhoneNumber(value) {
  if (!value) {
    return null;
  }

  const normalized = String(value).replace(/[^\d+]/g, "");
  return normalized || null;
}

function readRequiredEnv(name) {
  const value = process.env[name];

  if (!value || isPlaceholder(value)) {
    throw new Error(`Missing ${name}.`);
  }

  return value;
}

function parseInboundNumberMap() {
  const rawValue = process.env.RETELL_INBOUND_NUMBER_MAP;

  if (!rawValue || isPlaceholder(rawValue)) {
    return [];
  }

  let parsed;

  try {
    parsed = JSON.parse(rawValue);
  } catch {
    throw new Error("Invalid RETELL_INBOUND_NUMBER_MAP. Expected valid JSON.");
  }

  const entries = Array.isArray(parsed) ? parsed : Object.entries(parsed).map(([phoneNumber, value]) => ({
    phoneNumber,
    ...(typeof value === "string" ? { companyId: value } : value),
  }));

  return entries
    .map((entry) => ({
      phoneNumber: normalizePhoneNumber(entry?.phoneNumber || entry?.to_number),
      companyId: entry?.companyId || entry?.company_id || null,
      agentId: entry?.agentId || entry?.agent_id || null,
    }))
    .filter((entry) => entry.phoneNumber && entry.companyId);
}

export function resolveInboundRetellConfig(toNumber) {
  const normalizedToNumber = normalizePhoneNumber(toNumber);
  const mappedEntry = parseInboundNumberMap().find((entry) => entry.phoneNumber === normalizedToNumber);

  if (mappedEntry) {
    return mappedEntry;
  }

  return {
    phoneNumber: normalizePhoneNumber(process.env.RETELL_INBOUND_PHONE_NUMBER),
    companyId: readRequiredEnv("RETELL_INBOUND_COMPANY_ID"),
    agentId: process.env.RETELL_INBOUND_AGENT_ID || null,
  };
}

export function findInboundNumberForCompany(companyId) {
  if (!companyId) {
    return null;
  }

  const mappedEntry = parseInboundNumberMap().find((entry) => entry.companyId === companyId);

  if (mappedEntry?.phoneNumber) {
    return mappedEntry.phoneNumber;
  }

  return normalizePhoneNumber(process.env.RETELL_INBOUND_PHONE_NUMBER);
}
