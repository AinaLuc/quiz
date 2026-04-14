const DAY_IN_MS = 24 * 60 * 60 * 1000;

export function isCompanyPaid(company) {
  return ["active", "trialing"].includes(company?.billing_status);
}

export function getTrialNotificationState(company, now = new Date()) {
  if (!company?.trial_ends_at) {
    return {
      shouldSendReminder: false,
      shouldSendExpired: false,
      daysUntilExpiry: null,
      isExpired: false,
    };
  }

  const trialEndsAt = new Date(company.trial_ends_at);
  const msUntilExpiry = trialEndsAt.getTime() - now.getTime();
  const daysUntilExpiry = Math.ceil(msUntilExpiry / DAY_IN_MS);
  const isExpired = msUntilExpiry <= 0;

  return {
    shouldSendReminder:
      !isCompanyPaid(company) &&
      !company.trial_reminder_sent_at &&
      !isExpired &&
      daysUntilExpiry <= 3,
    shouldSendExpired:
      !isCompanyPaid(company) && !company.trial_expired_email_sent_at && isExpired,
    daysUntilExpiry,
    isExpired,
  };
}

function formatDate(value) {
  return new Intl.DateTimeFormat("fr-CA", {
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

export function buildTrialReminderEmail({ companyName, trialEndsAt, dashboardUrl }) {
  const formattedEndDate = formatDate(trialEndsAt);

  return {
    subject: "Votre essai Cyvora se termine bientôt",
    html: `
      <div style="font-family: Arial, sans-serif; color: #13261d; line-height: 1.6;">
        <h1 style="margin-bottom: 12px;">Votre essai se termine le ${formattedEndDate}</h1>
        <p style="margin: 0 0 16px;">
          Bonjour ${companyName},
        </p>
        <p style="margin: 0 0 16px;">
          Votre essai Cyvora arrive à sa fin. Activez votre plan pour garder votre numéro de transfert et continuer à convertir les appels en rendez-vous.
        </p>
        <p style="margin: 0 0 24px;">
          <a href="${dashboardUrl}" style="display: inline-block; padding: 12px 20px; border-radius: 999px; background: #0e766e; color: #ffffff; text-decoration: none; font-weight: 700;">
            Activer le plan
          </a>
        </p>
        <p style="margin: 0; color: #58675f;">
          Si vous avez des questions, répondez simplement à cet email.
        </p>
      </div>
    `,
  };
}

export function buildTrialExpiredEmail({ companyName, dashboardUrl }) {
  return {
    subject: "Votre essai Cyvora est terminé",
    html: `
      <div style="font-family: Arial, sans-serif; color: #13261d; line-height: 1.6;">
        <h1 style="margin-bottom: 12px;">Votre essai est terminé</h1>
        <p style="margin: 0 0 16px;">
          Bonjour ${companyName},
        </p>
        <p style="margin: 0 0 16px;">
          Votre essai gratuit Cyvora est terminé. L'assignation de nouveaux numéros est maintenant désactivée jusqu'à l'activation du plan payant.
        </p>
        <p style="margin: 0 0 24px;">
          <a href="${dashboardUrl}" style="display: inline-block; padding: 12px 20px; border-radius: 999px; background: #d96f32; color: #ffffff; text-decoration: none; font-weight: 700;">
            Réactiver l'accès
          </a>
        </p>
        <p style="margin: 0; color: #58675f;">
          Reconnectez-vous à votre dashboard pour activer le plan à tout moment.
        </p>
      </div>
    `,
  };
}

export async function sendTransactionalEmail({ to, subject, html }) {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM_EMAIL;

  if (!apiKey || !from) {
    throw new Error("Missing RESEND_API_KEY or RESEND_FROM_EMAIL.");
  }

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [to],
      subject,
      html,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Resend error: ${errorText}`);
  }

  return response.json();
}
