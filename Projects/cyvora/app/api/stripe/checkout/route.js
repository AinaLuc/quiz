import { NextResponse } from "next/server";
import { createClient as createServerSupabase } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { getStripe } from "@/lib/stripe";

export async function POST() {
  const supabase = await createServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.redirect(new URL("/signin", process.env.NEXT_PUBLIC_SITE_URL), 303);
  }

  if (!process.env.STRIPE_PRICE_ID) {
    return NextResponse.redirect(
      new URL("/dashboard?billingError=missing_price", process.env.NEXT_PUBLIC_SITE_URL),
      303,
    );
  }

  const admin = createAdminClient();
  const userId = user.id;
  const { data: profile } = await admin
    .from("profiles")
    .select("company_id, email, full_name")
    .eq("id", userId)
    .single();

  if (!profile?.company_id) {
    return NextResponse.redirect(
      new URL("/dashboard?billingError=missing_company", process.env.NEXT_PUBLIC_SITE_URL),
      303,
    );
  }

  const { data: company } = await admin
    .from("companies")
    .select("id, name, stripe_customer_id, billing_status, trial_ends_at")
    .eq("id", profile.company_id)
    .single();

  let stripe;
  try {
    stripe = getStripe();
  } catch (error) {
    return NextResponse.redirect(
      new URL(
        `/dashboard?billingError=${encodeURIComponent(error.message)}`,
        process.env.NEXT_PUBLIC_SITE_URL,
      ),
      303,
    );
  }

  let customerId = company?.stripe_customer_id;

  if (!customerId) {
    try {
      const customer = await stripe.customers.create({
        email: user.email,
        name: company?.name || profile.full_name || user.email,
        metadata: {
          companyId: profile.company_id,
          userId,
        },
      });
      customerId = customer.id;

      await admin
        .from("companies")
        .update({
          stripe_customer_id: customerId,
          billing_status: company?.billing_status || "trial_active",
        })
        .eq("id", profile.company_id);
    } catch (error) {
      return NextResponse.redirect(
        new URL(
          `/dashboard?billingError=${encodeURIComponent(error.message)}`,
          process.env.NEXT_PUBLIC_SITE_URL,
        ),
        303,
      );
    }
  }

  const trialEndUnix = company?.trial_ends_at
    ? Math.floor(new Date(company.trial_ends_at).getTime() / 1000)
    : undefined;
  const nowUnix = Math.floor(Date.now() / 1000);

  let checkoutSession;
  try {
    checkoutSession = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      line_items: [
        {
          price: process.env.STRIPE_PRICE_ID,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/dashboard?billing=success`,
      cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/dashboard?billing=canceled`,
      metadata: {
        companyId: profile.company_id,
        userId,
      },
      subscription_data: {
        metadata: {
          companyId: profile.company_id,
          userId,
        },
        ...(trialEndUnix && trialEndUnix > nowUnix ? { trial_end: trialEndUnix } : {}),
      },
    });
  } catch (error) {
    return NextResponse.redirect(
      new URL(
        `/dashboard?billingError=${encodeURIComponent(error.message)}`,
        process.env.NEXT_PUBLIC_SITE_URL,
      ),
      303,
    );
  }

  await admin
    .from("companies")
    .update({
      billing_status: "pending_checkout",
      plan: "starter",
    })
    .eq("id", profile.company_id);

  return NextResponse.redirect(checkoutSession.url, 303);
}
