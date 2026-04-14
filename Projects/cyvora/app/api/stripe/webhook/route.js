import Stripe from "stripe";
import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { getStripe } from "@/lib/stripe";

function mapStripeStatus(status) {
  switch (status) {
    case "active":
    case "trialing":
      return "active";
    case "past_due":
    case "unpaid":
      return "past_due";
    case "canceled":
    case "incomplete_expired":
      return "canceled";
    default:
      return status || "inactive";
  }
}

async function syncCompanyFromSubscription(subscription) {
  const admin = createAdminClient();
  const companyId = subscription.metadata?.companyId;

  if (!companyId) {
    return;
  }

  const periodStart = subscription.current_period_start
    ? new Date(subscription.current_period_start * 1000).toISOString()
    : null;
  const periodEnd = subscription.current_period_end
    ? new Date(subscription.current_period_end * 1000).toISOString()
    : null;
  const stripeStatus = mapStripeStatus(subscription.status);

  await admin.from("subscriptions").upsert(
    {
      company_id: companyId,
      stripe_customer_id: subscription.customer,
      stripe_subscription_id: subscription.id,
      stripe_price_id: subscription.items.data[0]?.price?.id || null,
      status: stripeStatus,
      current_period_start: periodStart,
      current_period_end: periodEnd,
      cancel_at_period_end: subscription.cancel_at_period_end,
    },
    { onConflict: "stripe_subscription_id" },
  );

  await admin
    .from("companies")
    .update({
      stripe_customer_id: subscription.customer,
      stripe_subscription_id: subscription.id,
      billing_status: stripeStatus,
      plan: subscription.items.data[0]?.price?.id ? "starter" : "trial",
    })
    .eq("id", companyId);
}

export async function POST(request) {
  if (!process.env.STRIPE_WEBHOOK_SECRET) {
    return NextResponse.json({ error: "Missing STRIPE_WEBHOOK_SECRET" }, { status: 500 });
  }

  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
  }

  const body = await request.text();
  const stripe = getStripe();

  let event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  if (
    event.type === "checkout.session.completed" &&
    event.data.object.mode === "subscription" &&
    event.data.object.subscription
  ) {
    const subscription = await stripe.subscriptions.retrieve(event.data.object.subscription, {
      expand: ["items.data.price"],
    });
    await syncCompanyFromSubscription(subscription);
  }

  if (
    event.type === "customer.subscription.created" ||
    event.type === "customer.subscription.updated" ||
    event.type === "customer.subscription.deleted"
  ) {
    await syncCompanyFromSubscription(event.data.object);
  }

  return NextResponse.json({ received: true });
}
