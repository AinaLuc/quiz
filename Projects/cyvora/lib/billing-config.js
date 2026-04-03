export const BILLING_PLANS = {
  starter: {
    key: "starter",
    name: "Starter",
    includedMinutesPerMonth: 300,
    isUnlimited: false,
  },
  pro: {
    key: "pro",
    name: "Pro",
    includedMinutesPerMonth: 600,
    isUnlimited: false,
  },
  growth: {
    key: "growth",
    name: "Growth",
    includedMinutesPerMonth: null,
    isUnlimited: true,
  },
};

export function getBillingPlan(planKey) {
  return BILLING_PLANS[planKey] || null;
}
