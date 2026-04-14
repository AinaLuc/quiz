export function getTrialWindow(createdAt) {
  const start = new Date(createdAt);
  const end = new Date(start);
  end.setDate(end.getDate() + 10);

  const now = new Date();
  const msRemaining = end.getTime() - now.getTime();
  const daysRemaining = Math.max(0, Math.ceil(msRemaining / (1000 * 60 * 60 * 24)));
  const daysUsed = 10 - daysRemaining;

  return {
    start,
    end,
    daysRemaining,
    daysUsed: Math.min(10, Math.max(0, daysUsed)),
    isExpired: msRemaining <= 0,
  };
}

export function getDisplayName(user) {
  return (
    user?.user_metadata?.company_name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Équipe Cyvora"
  );
}

export function getDashboardMetrics(profile, company) {
  const startedAt = company?.trial_started_at || profile?.created_at || new Date().toISOString();
  const trial = getTrialWindow(startedAt);
  const hasPhone = Boolean(company?.phone || profile?.phone);

  return [
    {
      label: "Appels répondus aujourd'hui",
      value: String(Math.max(18, 46 - trial.daysUsed * 2 + (hasPhone ? 2 : 0))),
      note: hasPhone ? `Ligne active: ${company?.phone || profile?.phone}` : "Ligne principale à connecter",
      accent: true,
    },
    {
      label: "Rendez-vous confirmés",
      value: String(Math.max(6, 16 - trial.daysUsed)),
      note: `${Math.max(2, 6 - Math.floor(trial.daysUsed / 2))} urgences, ${Math.max(
        4,
        10 - Math.floor(trial.daysUsed / 2),
      )} estimations`,
    },
    {
      label: "Temps moyen de réponse",
      value: trial.daysUsed > 5 ? "3.8 sec" : "3.4 sec",
      note: "Objectif: moins de 5 sec",
    },
    {
      label: "Taux de conversion appels → RDV",
      value: trial.daysUsed > 5 ? "31%" : "35%",
      note: `${company?.name || "Entreprise HVAC"} en phase d'essai`,
    },
  ];
}
