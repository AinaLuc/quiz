import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  buildTrialExpiredEmail,
  buildTrialReminderEmail,
  getTrialNotificationState,
  sendTransactionalEmail,
} from "@/lib/trial-notifications";

function isAuthorized(request) {
  const secret = process.env.CRON_SECRET;

  if (!secret) {
    return true;
  }

  return request.headers.get("authorization") === `Bearer ${secret}`;
}

function getDashboardUrl() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  return `${siteUrl}/dashboard`;
}

export async function GET(request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const admin = createAdminClient();
  const now = new Date();
  const dashboardUrl = getDashboardUrl();

  const { data: companies, error: companiesError } = await admin
    .from("companies")
    .select(
      "id, name, billing_status, trial_ends_at, trial_reminder_sent_at, trial_expired_email_sent_at",
    );

  if (companiesError) {
    return NextResponse.json({ error: companiesError.message }, { status: 500 });
  }

  const companyIds = (companies || []).map((company) => company.id);

  if (!companyIds.length) {
    return NextResponse.json({ ok: true, processed: 0, sent: 0 });
  }

  const { data: profiles, error: profilesError } = await admin
    .from("profiles")
    .select("company_id, email, full_name, role")
    .in("company_id", companyIds);

  if (profilesError) {
    return NextResponse.json({ error: profilesError.message }, { status: 500 });
  }

  const ownerByCompanyId = new Map();

  for (const profile of profiles || []) {
    if (!profile?.company_id || !profile?.email) {
      continue;
    }

    const existingProfile = ownerByCompanyId.get(profile.company_id);

    if (!existingProfile || profile.role === "owner") {
      ownerByCompanyId.set(profile.company_id, profile);
    }
  }

  let processed = 0;
  let sent = 0;
  const errors = [];

  for (const company of companies || []) {
    const recipient = ownerByCompanyId.get(company.id);
    const notificationState = getTrialNotificationState(company, now);

    if (!recipient?.email) {
      continue;
    }

    if (!notificationState.shouldSendReminder && !notificationState.shouldSendExpired) {
      continue;
    }

    processed += 1;

    try {
      if (notificationState.shouldSendReminder) {
        const email = buildTrialReminderEmail({
          companyName: company.name,
          trialEndsAt: company.trial_ends_at,
          dashboardUrl,
        });

        await sendTransactionalEmail({
          to: recipient.email,
          subject: email.subject,
          html: email.html,
        });

        const { error: updateError } = await admin
          .from("companies")
          .update({ trial_reminder_sent_at: now.toISOString() })
          .eq("id", company.id);

        if (updateError) {
          throw updateError;
        }

        sent += 1;
      }

      if (notificationState.shouldSendExpired) {
        const email = buildTrialExpiredEmail({
          companyName: company.name,
          dashboardUrl,
        });

        await sendTransactionalEmail({
          to: recipient.email,
          subject: email.subject,
          html: email.html,
        });

        const { error: updateError } = await admin
          .from("companies")
          .update({ trial_expired_email_sent_at: now.toISOString() })
          .eq("id", company.id);

        if (updateError) {
          throw updateError;
        }

        sent += 1;
      }
    } catch (error) {
      errors.push({
        companyId: company.id,
        email: recipient.email,
        message: error.message,
      });
    }
  }

  return NextResponse.json({
    ok: errors.length === 0,
    processed,
    sent,
    errors,
  });
}
