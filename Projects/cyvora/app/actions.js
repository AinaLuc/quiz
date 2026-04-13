"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { listRetellPhoneNumbers } from "@/lib/retell-management";
import {
  buildTrialExpiredEmail,
  buildTrialReminderEmail,
  sendTransactionalEmail,
} from "@/lib/trial-notifications";

function getOrigin(headersList) {
  const forwardedHost = headersList.get("x-forwarded-host");
  const forwardedProto = headersList.get("x-forwarded-proto");

  if (forwardedHost) {
    return `${forwardedProto || "https"}://${forwardedHost}`;
  }

  return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
}

function isCompanyEligibleForNumberAssignment(company) {
  if (!company) {
    return false;
  }

  if (["active", "trialing"].includes(company.billing_status)) {
    return true;
  }

  if (!company.trial_ends_at) {
    return true;
  }

  return new Date(company.trial_ends_at).getTime() > Date.now();
}

export async function signInWithGoogle() {
  const supabase = await createClient();
  const headerStore = await headers();
  const origin = getOrigin(headerStore);

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${origin}/auth/callback?next=/dashboard`,
      queryParams: {
        access_type: "offline",
        prompt: "consent",
      },
    },
  });

  if (error) {
    redirect(`/signin?error=${encodeURIComponent(error.message)}`);
  }

  redirect(data.url);
}

export async function signInWithPassword(formData) {
  const supabase = await createClient();

  const email = formData.get("email");
  const password = formData.get("password");

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    redirect(`/signin?error=${encodeURIComponent(error.message)}`);
  }

  redirect("/dashboard");
}

export async function signUp(formData) {
  const supabase = await createClient();
  const headerStore = await headers();
  const origin = getOrigin(headerStore);

  const company = formData.get("company");
  const email = formData.get("email");
  const phone = formData.get("phone");
  const password = formData.get("password");

  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${origin}/auth/callback?next=/dashboard`,
      data: {
        company_name: company,
        phone,
        trial_started_at: new Date().toISOString(),
        trial_length_days: 10,
      },
    },
  });

  if (error) {
    redirect(`/signup?error=${encodeURIComponent(error.message)}`);
  }

  redirect("/dashboard?welcome=1");
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/");
}

export async function assignRetellNumber(formData) {
  const supabase = await createClient();
  const admin = createAdminClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  const retellPhoneNumberId = formData.get("retellPhoneNumberId")?.toString();

  if (!retellPhoneNumberId) {
    redirect("/dashboard?setupError=missing_retell_number");
  }

  const phoneNumbers = await listRetellPhoneNumbers();
  const selectedPhoneNumber = phoneNumbers.find((phoneNumber) => phoneNumber.id === retellPhoneNumberId);

  if (!selectedPhoneNumber?.phoneNumber) {
    redirect("/dashboard?setupError=missing_retell_number");
  }

  if (selectedPhoneNumber.isAssigned) {
    redirect("/dashboard?setupError=number_unavailable");
  }

  const { data: profile } = await admin
    .from("profiles")
    .select("company_id")
    .eq("id", user.id)
    .single();

  if (!profile?.company_id) {
    redirect("/dashboard?setupError=missing_company");
  }

  const { data: company } = await admin
    .from("companies")
    .select("billing_status, trial_ends_at")
    .eq("id", profile.company_id)
    .maybeSingle();

  if (!isCompanyEligibleForNumberAssignment(company)) {
    redirect("/dashboard?setupError=trial_expired");
  }

  const { data: existingAssignment } = await admin
    .from("retell_phone_assignments")
    .select("company_id")
    .eq("phone_number", retellPhoneNumberId)
    .maybeSingle();

  if (existingAssignment && existingAssignment.company_id !== profile.company_id) {
    redirect("/dashboard?setupError=number_unavailable");
  }

  const { error } = await admin.from("retell_phone_assignments").upsert(
    {
      company_id: profile.company_id,
      phone_number: selectedPhoneNumber.phoneNumber,
      phone_number_pretty: selectedPhoneNumber.displayNumber,
      nickname: selectedPhoneNumber.name,
      inbound_agent_id: selectedPhoneNumber.inboundAgentId,
      outbound_agent_id: selectedPhoneNumber.outboundAgentId,
      phone_number_type: selectedPhoneNumber.phoneNumberType,
    },
    { onConflict: "company_id" },
  );

  if (error) {
    redirect(`/dashboard?setupError=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/dashboard");
  redirect("/dashboard?setup=number_assigned");
}

export async function releaseRetellNumber() {
  const supabase = await createClient();
  const admin = createAdminClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  const { data: profile } = await admin
    .from("profiles")
    .select("company_id")
    .eq("id", user.id)
    .single();

  if (!profile?.company_id) {
    redirect("/dashboard?setupError=missing_company");
  }

  const { error } = await admin
    .from("retell_phone_assignments")
    .delete()
    .eq("company_id", profile.company_id);

  if (error) {
    redirect(`/dashboard?setupError=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/dashboard");
  redirect("/dashboard?setup=number_released");
}

export async function sendTrialLifecycleTest(formData) {
  const supabase = await createClient();
  const admin = createAdminClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  const kind = formData.get("kind")?.toString();

  if (!["reminder", "expired"].includes(kind || "")) {
    redirect("/dashboard?emailTestError=invalid_kind");
  }

  const { data: profile } = await admin
    .from("profiles")
    .select("company_id, email, full_name")
    .eq("id", user.id)
    .single();

  if (!profile?.company_id || !profile?.email) {
    redirect("/dashboard?emailTestError=missing_company");
  }

  const { data: company } = await admin
    .from("companies")
    .select("name, trial_ends_at")
    .eq("id", profile.company_id)
    .single();

  if (!company) {
    redirect("/dashboard?emailTestError=missing_company");
  }

  const dashboardUrl = `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/dashboard`;
  const email =
    kind === "reminder"
      ? buildTrialReminderEmail({
          companyName: company.name,
          trialEndsAt:
            company.trial_ends_at || new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          dashboardUrl,
        })
      : buildTrialExpiredEmail({
          companyName: company.name,
          dashboardUrl,
        });

  try {
    await sendTransactionalEmail({
      to: profile.email,
      subject: `[TEST] ${email.subject}`,
      html: email.html,
    });
  } catch (error) {
    redirect(`/dashboard?emailTestError=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/dashboard");
  redirect(`/dashboard?emailTest=${encodeURIComponent(kind)}`);
}
