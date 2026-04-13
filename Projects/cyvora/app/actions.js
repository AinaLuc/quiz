"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { listRetellPhoneNumbers } from "@/lib/retell-management";
import {
  bindRetellPhoneNumber,
  cleanupRetellAgent,
  ensureCompanyRetellAgent,
  unbindRetellPhoneNumber,
} from "@/lib/retell-provisioning";
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

function isCompanyEligibleForNumberAssignment(company, { hadPreviousAssignment = false } = {}) {
  if (!company) {
    return false;
  }

  // A company that already has a Retell agent configured can always reassign a number.
  if (company.retell_agent_id || company.retell_llm_id) {
    return true;
  }

  // A company that completed onboarding (had a number assigned at least once) can reassign.
  if (company.first_number_assigned_at || hadPreviousAssignment) {
    return true;
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
  const headerStore = await headers();
  const origin = getOrigin(headerStore);
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
    .select("company_id, full_name")
    .eq("id", user.id)
    .single();

  if (!profile?.company_id) {
    redirect("/dashboard?setupError=missing_company");
  }

  const { data: company } = await admin
    .from("companies")
    .select("name, billing_status, trial_ends_at, retell_agent_id, retell_llm_id, retell_base_general_prompt, first_number_assigned_at")
    .eq("id", profile.company_id)
    .maybeSingle();

  // Check if the company has ever had a phone assignment (even if already released),
  // which means they had completed onboarding during an active trial.
  const { count: previousAssignmentCount } = await admin
    .from("retell_phone_assignments")
    .select("*", { count: "exact", head: true })
    .eq("company_id", profile.company_id);
  const hadPreviousAssignment = (previousAssignmentCount || 0) > 0;

  if (!isCompanyEligibleForNumberAssignment(company, { hadPreviousAssignment })) {
    redirect("/dashboard?setupError=trial_expired");
  }

  const { data: existingAssignment } = await admin
    .from("retell_phone_assignments")
    .select("company_id, phone_number, inbound_agent_id, outbound_agent_id")
    .eq("phone_number", retellPhoneNumberId)
    .maybeSingle();

  if (existingAssignment && existingAssignment.company_id !== profile.company_id) {
    redirect("/dashboard?setupError=number_unavailable");
  }

  const { data: existingCompanyAssignment } = await admin
    .from("retell_phone_assignments")
    .select("phone_number, inbound_agent_id, outbound_agent_id")
    .eq("company_id", profile.company_id)
    .maybeSingle();

  const companyAssignmentRow = existingCompanyAssignment || null;
  const companyRetellAgentId =
    company?.retell_agent_id ||
    companyAssignmentRow?.inbound_agent_id ||
    companyAssignmentRow?.outbound_agent_id ||
    null;

  const companyRetellLlmId = company?.retell_llm_id || null;
  const companyBasePrompt = company?.retell_base_general_prompt || "";
  const companyDisplayName = company?.name || profile.full_name || "Votre entreprise";
  const previousCompanyRetellState = {
    retell_agent_id: company?.retell_agent_id || null,
    retell_llm_id: company?.retell_llm_id || null,
    retell_base_general_prompt: company?.retell_base_general_prompt || null,
  };

  let retellAgent;

  try {
    retellAgent = await ensureCompanyRetellAgent({
      companyName: companyDisplayName,
      existingAgentId: companyRetellAgentId,
      existingLlmId: companyRetellLlmId,
      existingBasePrompt: companyBasePrompt,
    });
  } catch (error) {
    redirect(`/dashboard?setupError=${encodeURIComponent(error.message)}`);
  }

  const previousPhoneNumber = companyAssignmentRow?.phone_number || null;

  try {
    await bindRetellPhoneNumber({
      phoneNumber: selectedPhoneNumber.phoneNumber,
      agentId: retellAgent.agentId,
      displayName: companyDisplayName,
      webhookUrl: `${origin}/api/retell/inbound`,
    });
  } catch (error) {
    if (retellAgent.wasCreated) {
      await cleanupRetellAgent({
        agentId: retellAgent.agentId,
        llmId: retellAgent.llmId,
      });
    }

    redirect(`/dashboard?setupError=${encodeURIComponent(error.message)}`);
  }

  const { error: companyUpdateError } = await admin
    .from("companies")
    .update({
      retell_agent_id: retellAgent.agentId,
      retell_llm_id: retellAgent.llmId,
      retell_base_general_prompt: retellAgent.basePrompt,
      // Permanently mark that this company completed onboarding by assigning a number.
      ...(!company?.first_number_assigned_at ? { first_number_assigned_at: new Date().toISOString() } : {}),
    })
    .eq("id", profile.company_id);

  if (companyUpdateError) {
    await unbindRetellPhoneNumber(selectedPhoneNumber.phoneNumber).catch(() => null);
    if (retellAgent.wasCreated) {
      await cleanupRetellAgent({
        agentId: retellAgent.agentId,
        llmId: retellAgent.llmId,
      });
    }

    redirect(`/dashboard?setupError=${encodeURIComponent(companyUpdateError.message)}`);
  }

  const { error } = await admin.from("retell_phone_assignments").upsert(
    {
      company_id: profile.company_id,
      phone_number: selectedPhoneNumber.phoneNumber,
      phone_number_pretty: selectedPhoneNumber.displayNumber,
      nickname: selectedPhoneNumber.name || companyDisplayName,
      inbound_agent_id: retellAgent.agentId,
      outbound_agent_id: retellAgent.agentId,
      phone_number_type: selectedPhoneNumber.phoneNumberType,
    },
    { onConflict: "company_id" },
  );

  if (error) {
    await unbindRetellPhoneNumber(selectedPhoneNumber.phoneNumber).catch(() => null);
    await admin
      .from("companies")
      .update(previousCompanyRetellState)
      .eq("id", profile.company_id)
      .catch(() => null);
    if (retellAgent.wasCreated) {
      await cleanupRetellAgent({
        agentId: retellAgent.agentId,
        llmId: retellAgent.llmId,
      });
    }

    redirect(`/dashboard?setupError=${encodeURIComponent(error.message)}`);
  }

  if (previousPhoneNumber && previousPhoneNumber !== selectedPhoneNumber.phoneNumber) {
    await unbindRetellPhoneNumber(previousPhoneNumber).catch(() => null);
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

  const { data: assignment } = await admin
    .from("retell_phone_assignments")
    .select("phone_number")
    .eq("company_id", profile.company_id)
    .maybeSingle();

  if (assignment?.phone_number) {
    await unbindRetellPhoneNumber(assignment.phone_number).catch(() => null);
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
