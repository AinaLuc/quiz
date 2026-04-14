import Retell from "retell-sdk";

const COMPANY_PROMPT_SEPARATOR = "\n\n--- BASE PROMPT ---\n";

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

function getTemplateAgentId() {
  return (
    process.env.RETELL_TEMPLATE_AGENT_ID ||
    process.env.RETELL_INBOUND_AGENT_ID ||
    null
  );
}

function normalizeCompanyName(companyName) {
  const value = String(companyName || "").trim();
  return value || "Votre entreprise";
}

export function buildCompanyGeneralPrompt(companyName, basePrompt = "", isCalcomEnabled = false) {
  const safeCompanyName = normalizeCompanyName(companyName);
  const introParts = [
    `Vous êtes l'assistant vocal de ${safeCompanyName}.`,
    "Répondez toujours en français canadien, avec un ton professionnel, chaleureux et rassurant.",
    "Présentez l'entreprise sans mentionner les outils internes, l'infrastructure technique ou la plateforme qui vous héberge.",
    "Si l'appelant parle en anglais, continuez en français sauf s'il demande explicitement l'anglais.",
  ];

  if (isCalcomEnabled) {
    introParts.push(
      "Vous avez la capacité de vérifier les disponibilités et de prendre des rendez-vous directement sur notre calendrier.",
    );
  }

  const intro = introParts.join(" ");
  const normalizedBasePrompt = String(basePrompt || "").trim();

  return normalizedBasePrompt
    ? `${intro}${COMPANY_PROMPT_SEPARATOR}${normalizedBasePrompt}`
    : intro;
}

function extractBasePromptFromCompanyPrompt(prompt) {
  if (typeof prompt !== "string" || !prompt.length) {
    return "";
  }

  const separatorIndex = prompt.indexOf(COMPANY_PROMPT_SEPARATOR);

  if (separatorIndex === -1) {
    return prompt.trim();
  }

  return prompt.slice(separatorIndex + COMPANY_PROMPT_SEPARATOR.length).trim();
}

function stripReadonlyLlmFields(llm) {
  const {
    llm_id,
    last_modification_timestamp,
    is_published,
    version,
    ...cloneable
  } = llm || {};

  return cloneable;
}

function stripReadonlyAgentFields(agent) {
  const {
    agent_id,
    last_modification_timestamp,
    version,
    is_published,
    ...cloneable
  } = agent || {};

  return cloneable;
}

export async function ensureCompanyRetellAgent({
  companyName,
  existingAgentId,
  existingLlmId,
  existingBasePrompt,
  calcomApiKey,
  calcomEventTypeId,
}) {
  const client = getRetellClient();
  const safeCompanyName = normalizeCompanyName(companyName);

  const calcomTools =
    calcomApiKey && calcomEventTypeId
      ? [
          {
            type: "check_availability_cal",
            name: "check_availability",
            description: "Vérifier les disponibilités pour les 7 prochains jours.",
            cal_api_key: calcomApiKey,
            event_type_id: Number(calcomEventTypeId),
            timezone: "America/Toronto",
          },
          {
            type: "book_appointment_cal",
            name: "book_appointment",
            description: "Prendre un rendez-vous une fois qu'un créneau est confirmé.",
            cal_api_key: calcomApiKey,
            event_type_id: Number(calcomEventTypeId),
            timezone: "America/Toronto",
          },
        ]
      : [];

  if (existingAgentId) {
    const agent = await client.agent.retrieve(existingAgentId);
    const agentLlmId =
      existingLlmId ||
      (agent.response_engine?.type === "retell-llm" ? agent.response_engine.llm_id : null);

    if (!agentLlmId) {
      throw new Error("The existing Retell agent is not attached to a Retell LLM.");
    }

    const llm = await client.llm.retrieve(agentLlmId);
    const basePrompt =
      existingBasePrompt || extractBasePromptFromCompanyPrompt(llm.general_prompt || "");
    const nextPrompt = buildCompanyGeneralPrompt(safeCompanyName, basePrompt, Boolean(calcomApiKey && calcomEventTypeId));
    const nextDefaultVariables = {
      ...(llm.default_dynamic_variables || {}),
      company_name: safeCompanyName,
    };

    // Filter out existing calcom tools before adding new ones to avoid duplicates
    const otherTools = (llm.general_tools || []).filter(
      (t) => t.type !== "check_availability_cal" && t.type !== "book_appointment_cal",
    );
    const nextTools = [...otherTools, ...calcomTools];

    // Basic comparison to avoid unnecessary updates
    const hasToolsChanged = JSON.stringify(llm.general_tools || []) !== JSON.stringify(nextTools);

    if (
      (llm.general_prompt || "") !== nextPrompt ||
      llm.default_dynamic_variables?.company_name !== safeCompanyName ||
      hasToolsChanged
    ) {
      await client.llm.update(agentLlmId, {
        general_prompt: nextPrompt,
        default_dynamic_variables: nextDefaultVariables,
        general_tools: nextTools,
      });
    }

    const desiredAgentName = `${safeCompanyName} - Assistant`;

    if ((agent.agent_name || "") !== desiredAgentName) {
      await client.agent.update(existingAgentId, {
        agent_name: desiredAgentName,
      });
    }

    return {
      agentId: existingAgentId,
      basePrompt,
      llmId: agentLlmId,
      sourceAgentId: existingAgentId,
      wasCreated: false,
    };
  }

  const templateAgentId = getTemplateAgentId();

  if (!templateAgentId) {
    throw new Error("Missing Retell template agent ID.");
  }

  const templateAgent = await client.agent.retrieve(templateAgentId);

  if (templateAgent.response_engine?.type !== "retell-llm") {
    throw new Error("Retell template agent must use a Retell LLM.");
  }

  const templateLlm = await client.llm.retrieve(templateAgent.response_engine.llm_id);
  const basePrompt = String(templateLlm.general_prompt || "").trim();
  const nextPrompt = buildCompanyGeneralPrompt(safeCompanyName, basePrompt, Boolean(calcomApiKey && calcomEventTypeId));
  
  const templateTools = (templateLlm.general_tools || []).filter(
    (t) => t.type !== "check_availability_cal" && t.type !== "book_appointment_cal",
  );

  const clonedLlm = await client.llm.create({
    ...stripReadonlyLlmFields(templateLlm),
    general_prompt: nextPrompt,
    general_tools: [...templateTools, ...calcomTools],
    default_dynamic_variables: {
      ...(templateLlm.default_dynamic_variables || {}),
      company_name: safeCompanyName,
    },
  });

  const clonedAgent = await client.agent.create({
    ...stripReadonlyAgentFields(templateAgent),
    agent_name: `${safeCompanyName} - Assistant`,
    response_engine: {
      type: "retell-llm",
      llm_id: clonedLlm.llm_id,
    },
  });

  return {
    agentId: clonedAgent.agent_id,
    basePrompt,
    llmId: clonedLlm.llm_id,
    sourceAgentId: templateAgentId,
    wasCreated: true,
  };
}

export async function bindRetellPhoneNumber({
  phoneNumber,
  agentId,
  displayName,
  webhookUrl,
}) {
  const client = getRetellClient();

  return client.phoneNumber.update(phoneNumber, {
    inbound_agent_id: agentId,
    outbound_agent_id: agentId,
    inbound_agents: null,
    outbound_agents: null,
    inbound_webhook_url: webhookUrl || null,
    nickname: displayName || null,
  });
}

export async function unbindRetellPhoneNumber(phoneNumber) {
  const client = getRetellClient();

  return client.phoneNumber.update(phoneNumber, {
    inbound_agent_id: null,
    outbound_agent_id: null,
    inbound_agents: null,
    outbound_agents: null,
    inbound_webhook_url: null,
  });
}

export async function cleanupRetellAgent({ agentId, llmId }) {
  const client = getRetellClient();

  if (agentId) {
    try {
      await client.agent.delete(agentId);
    } catch {
      // Best-effort cleanup only.
    }
  }

  if (llmId) {
    try {
      await client.llm.delete(llmId);
    } catch {
      // Best-effort cleanup only.
    }
  }
}
