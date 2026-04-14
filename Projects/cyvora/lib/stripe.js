import Stripe from "stripe";

let stripeClient;

export function getStripe() {
  const apiKey = process.env.STRIPE_SECRET_KEY;

  if (!apiKey) {
    throw new Error("Missing STRIPE_SECRET_KEY.");
  }

  if (!apiKey.startsWith("sk_")) {
    throw new Error("Invalid STRIPE_SECRET_KEY format.");
  }

  if (!stripeClient) {
    stripeClient = new Stripe(apiKey);
  }

  return stripeClient;
}
