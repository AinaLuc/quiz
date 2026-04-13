import { redirect } from "next/navigation";
import { ActionSubmitButton } from "@/components/action-submit-button";
import { RetellDebugConsole } from "@/components/retell-debug-console";
import { SiteHeader } from "@/components/site-header";
import { UpgradeForm } from "@/components/upgrade-form";
import { assignRetellNumber, releaseRetellNumber, sendTrialLifecycleTest } from "@/app/actions";
import { getDisplayName, getTrialWindow } from "@/lib/auth";
import { formatIncludedMinutes, getBillingPlan } from "@/lib/billing-config";
import { ensureProfileRecords } from "@/lib/profile";
import { createAdminClient } from "@/lib/supabase/admin";
import { findInboundNumberForCompany } from "@/lib/retell-inbound-config";
import { listRetellPhoneNumbers } from "@/lib/retell-management";
import { createClient } from "@/lib/supabase/server";

function getTodayStartIso() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return start.toISOString();
}

function formatCallTime(value) {
  if (!value) {
    return "Maintenant";
  }

  return new Intl.DateTimeFormat("fr-CA", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatMinutes(value) {
  return new Intl.NumberFormat("fr-CA", {
    maximumFractionDigits: 0,
  }).format(Math.max(0, Math.round(value)));
}

function excerptText(value, maxLength = 180) {
  if (!value) {
    return null;
  }

  const normalized = value.replace(/\s+/g, " ").trim();

  if (!normalized) {
    return null;
  }

  return normalized.length > maxLength ? `${normalized.slice(0, maxLength - 1)}…` : normalized;
}

function getCurrentMonthStartIso() {
  const now = new Date();
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
  return start.toISOString();
}

function formatSetupError(error) {
  switch (error) {
    case "missing_retell_number":
      return "Choisissez un numéro Retell avant de continuer.";
    case "missing_company":
      return "Impossible de trouver l'entreprise liée à ce compte.";
    case "number_unavailable":
      return "Ce numéro est déjà réservé par un autre client.";
    case "trial_expired":
      return "L'essai est terminé. Activez le plan pour assigner un numéro.";
    case "Missing RETELL_API_KEY.":
      return "Ajoutez RETELL_API_KEY dans Vercel pour charger les numéros Retell.";
    default:
      return error ? `Erreur configuration: ${error}` : null;
  }
}

function formatSetupSuccess(value) {
  switch (value) {
    case "number_assigned":
      return "Numéro Retell assigné.";
    case "number_released":
      return "Numéro libéré.";
    default:
      return null;
  }
}

function formatEmailTestError(error) {
  switch (error) {
    case "invalid_kind":
      return "Type d'email de test invalide.";
    case "missing_company":
      return "Impossible de trouver une entreprise ou une adresse email pour ce compte.";
    default:
      return error ? `Erreur email: ${error}` : null;
  }
}

function formatEmailTestSuccess(value) {
  switch (value) {
    case "reminder":
      return "Email de rappel envoyé à votre adresse.";
    case "expired":
      return "Email d'expiration envoyé à votre adresse.";
    default:
      return null;
  }
}

export default async function DashboardPage({ searchParams }) {
  const supabase = await createClient();
  const admin = createAdminClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  const params = await searchParams;
  const billing = params?.billing;
  const billingError = params?.billingError;
  const setup = params?.setup;
  const setupError = params?.setupError;
  const emailTest = params?.emailTest;
  const emailTestError = params?.emailTestError;
  const page = Math.max(1, Number(params?.page || 1) || 1);

  let dataError = null;

  try {
    await ensureProfileRecords(supabase, user);
  } catch (error) {
    dataError = error.message;
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("id, company_id, email, full_name")
    .eq("id", user.id)
    .maybeSingle();

  const { data: company } = profile?.company_id
    ? await supabase
        .from("companies")
        .select(
          "id, name, trial_started_at, trial_ends_at, billing_status, plan, stripe_subscription_id",
        )
        .eq("id", profile.company_id)
        .maybeSingle()
    : { data: null };

  const todayStart = getTodayStartIso();
  const currentMonthStart = getCurrentMonthStartIso();
  const trial = getTrialWindow(
    company?.trial_started_at || user.user_metadata?.trial_started_at || user.created_at,
  );
  const companyName = company?.name || profile?.full_name || getDisplayName(user);
  const billingStatus = company?.billing_status || "trial_active";
  const isPaid = ["active", "trialing"].includes(billingStatus);
  const billingPlan = getBillingPlan(company?.plan);

  const [
    { count: callsToday },
    { count: appointmentsTotal },
    { data: latestCalls },
    { data: periodCalls },
    { data: companyAssignment },
    { data: assignedRows },
  ] = await Promise.all([
    profile?.company_id
      ? supabase
          .from("calls")
          .select("*", { count: "exact", head: true })
          .eq("company_id", profile.company_id)
          .gte("created_at", todayStart)
      : Promise.resolve({ count: 0 }),
    profile?.company_id
      ? supabase
          .from("appointments")
          .select("*", { count: "exact", head: true })
          .eq("company_id", profile.company_id)
      : Promise.resolve({ count: 0 }),
    profile?.company_id
      ? supabase
          .from("calls")
          .select(
            "external_call_id, customer_number, created_at, urgency, booking_status, status, summary, transcript",
          )
          .eq("company_id", profile.company_id)
          .order("created_at", { ascending: false })
          .limit(5)
      : Promise.resolve({ data: [] }),
    profile?.company_id
      ? supabase
          .from("calls")
          .select("duration_seconds")
          .eq("company_id", profile.company_id)
          .gte("created_at", currentMonthStart)
      : Promise.resolve({ data: [] }),
    profile?.company_id
      ? admin
          .from("retell_phone_assignments")
          .select("phone_number, phone_number_pretty, nickname, inbound_agent_id, outbound_agent_id, phone_number_type")
          .eq("company_id", profile.company_id)
          .maybeSingle()
      : Promise.resolve({ data: null }),
    admin
      .from("retell_phone_assignments")
      .select("phone_number, company_id"),
  ]);

  let retellNumbers = [];
  let retellNumbersError = null;

  try {
    retellNumbers = await listRetellPhoneNumbers();
  } catch (error) {
    retellNumbersError = error.message;
  }

  const assignedIds = new Set((assignedRows || []).map((row) => row.phone_number));
  const availableNumbers = retellNumbers.filter(
    (phoneNumber) =>
      phoneNumber.id === companyAssignment?.phone_number || !assignedIds.has(phoneNumber.id),
  );
  const numbersPageSize = 5;
  const totalPages = Math.max(1, Math.ceil(availableNumbers.length / numbersPageSize));
  const currentPage = Math.min(page, totalPages);
  const paginatedNumbers = availableNumbers.slice(
    (currentPage - 1) * numbersPageSize,
    currentPage * numbersPageSize,
  );

  const retellInboundNumber = findInboundNumberForCompany(profile?.company_id || null);
  const activeInboundNumber =
    companyAssignment?.phone_number_pretty || companyAssignment?.phone_number || retellInboundNumber || null;

  const statusPill = isPaid ? "Actif" : trial.isExpired ? "Essai terminé" : "Essai";
  const statusLabel = isPaid
    ? company?.plan === "starter"
      ? "Plan Starter"
      : company?.plan === "pro"
        ? "Plan Pro"
        : company?.plan === "growth"
          ? "Plan Growth"
          : "Plan actif"
    : `${trial.daysRemaining} jour${trial.daysRemaining > 1 ? "s" : ""} restants`;
  const canAssignNumber = isPaid || !trial.isExpired;
  const showTrialBanner = !isPaid && (trial.isExpired || trial.daysRemaining <= 3);
  const usedMinutesThisMonth = (periodCalls || []).reduce(
    (total, call) => total + (call?.duration_seconds || 0),
    0,
  ) / 60;
  const remainingMinutes =
    billingPlan && !billingPlan.isUnlimited
      ? Math.max(0, billingPlan.includedMinutesPerMonth - usedMinutesThisMonth)
      : null;
  const usageValue = !isPaid
    ? `${trial.daysRemaining} j`
    : billingPlan?.isUnlimited
      ? "Illimite"
      : `${formatMinutes(remainingMinutes)} min`;
  const usageNote = !isPaid
    ? "Temps restant sur l'essai"
    : billingPlan
      ? billingPlan.isUnlimited
        ? `Plan ${billingPlan.name} sans limite de minutes`
        : `${formatMinutes(usedMinutesThisMonth)} / ${formatIncludedMinutes(billingPlan)} utilisees`
      : "Plan actif";

  return (
    <div className="app-shell">
      <SiteHeader session={{ user }} />

      <main className="dashboard-main">
        <RetellDebugConsole calls={latestCalls || []} />

        <section className="dashboard-hero panel">
          <div>
            <p className="eyebrow">Opérations</p>
            <h1 className="title-lg">{companyName}</h1>
            <p className="text-muted">Numéro Retell, appels du jour et état du compte.</p>
          </div>

          <div className="hero-actions-compact">
            <div className="dashboard-badge">
              <span>{statusPill}</span>
              <strong>{statusLabel}</strong>
            </div>
            {!isPaid ? (
              <UpgradeForm
                disabled={!company?.id}
                label={trial.isExpired ? "Activer le plan" : "Passer au payant"}
              />
            ) : null}
          </div>
        </section>

        {billing === "success" ? (
          <div className="alert alert-success section-gap">
            Checkout Stripe lancé.
          </div>
        ) : null}

        {billing === "canceled" ? (
          <div className="alert section-gap">
            Paiement annulé.
          </div>
        ) : null}

        {billingError ? (
          <div className="alert alert-error section-gap">
            Erreur Stripe: {billingError}
          </div>
        ) : null}

        {formatSetupSuccess(setup) ? (
          <div className="alert alert-success section-gap">{formatSetupSuccess(setup)}</div>
        ) : null}

        {formatSetupError(setupError) ? (
          <div className="alert alert-error section-gap">{formatSetupError(setupError)}</div>
        ) : null}

        {formatEmailTestSuccess(emailTest) ? (
          <div className="alert alert-success section-gap">{formatEmailTestSuccess(emailTest)}</div>
        ) : null}

        {formatEmailTestError(emailTestError) ? (
          <div className="alert alert-error section-gap">{formatEmailTestError(emailTestError)}</div>
        ) : null}

        {dataError ? (
          <div className="alert alert-error section-gap">
            Exécutez <code>supabase/schema.sql</code> dans Supabase avant de continuer.
          </div>
        ) : null}

        {showTrialBanner ? (
          <section className="dashboard-banner section-gap">
            <div>
              <p className="eyebrow">{trial.isExpired ? "Essai terminé" : "Essai bientôt terminé"}</p>
              <h2 className="title-md">
                {trial.isExpired
                  ? "Activez votre plan pour réassigner un numéro et continuer l'onboarding."
                  : `Il reste ${trial.daysRemaining} jour${trial.daysRemaining > 1 ? "s" : ""} avant la fin de l'essai.`}
              </h2>
              <p className="text-muted">
                {trial.isExpired
                  ? "Le compte reste visible, mais les nouvelles assignations de numéros sont bloquées jusqu'à l'activation du plan."
                  : "Passez au plan payant maintenant pour éviter l'interruption du numéro Retell à la fin de l'essai."}
              </p>
            </div>
            <UpgradeForm
              disabled={!company?.id}
              label={trial.isExpired ? "Activer le plan" : "Passer au payant"}
            />
          </section>
        ) : null}

        <section className="dashboard-grid dashboard-grid-compact">
          <article className="metric-card metric-card-accent">
            <span>Appels aujourd&apos;hui</span>
            <strong>{callsToday || 0}</strong>
          </article>
          <article className="metric-card">
            <span>RDV confirmés</span>
            <strong>{appointmentsTotal || 0}</strong>
          </article>
          <article className="metric-card">
            <span>Numéro assigné</span>
            <strong>{activeInboundNumber || "Aucun"}</strong>
          </article>
          <article className="metric-card">
            <span>{isPaid ? "Minutes restantes" : "Temps restant"}</span>
            <strong>{usageValue}</strong>
            <small>{usageNote}</small>
          </article>
        </section>

        <section className="operations-grid">
          <article className="card operations-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">Retell</p>
                <h2>Numéro Retell</h2>
              </div>
            </div>

            <div className="assignment-box">
              <span>Actuel</span>
              <strong>{activeInboundNumber || "Non configuré"}</strong>
              <p className="text-muted">
                {companyAssignment
                  ? "Ce numéro est retiré de la liste Retell dès qu'il est assigné."
                  : retellInboundNumber
                    ? "Numéro inbound Retell configuré via l'environnement de production."
                    : "Choisissez un numéro Retell disponible pour l'associer à ce compte."}
              </p>
            </div>

            {companyAssignment ? (
              <form action={releaseRetellNumber}>
                <ActionSubmitButton
                  className="button button-secondary"
                  idleLabel="Libérer le numéro"
                  pendingLabel="Libération..."
                />
              </form>
            ) : null}
          </article>

          <article className="card operations-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">Inventaire</p>
                <h2>Numéros disponibles</h2>
              </div>
              <span className="pill pill-neutral">{availableNumbers.length}</span>
            </div>

            {retellNumbersError ? (
              <div className="alert alert-error">Erreur numéros: {retellNumbersError}</div>
            ) : null}

            {!retellNumbersError && !availableNumbers.length ? (
              <p className="text-muted">Aucun numéro libre pour le moment.</p>
            ) : null}

            {!canAssignNumber ? (
              <div className="alert section-gap">
                L&apos;assignation de numéro est désactivée après la fin de l&apos;essai. Activez le
                plan pour continuer.
              </div>
            ) : null}

            {!retellNumbersError && paginatedNumbers.length ? (
              <div className="number-list">
                {paginatedNumbers.map((phoneNumber) => (
                  <article
                    className={`number-row ${
                      companyAssignment?.phone_number === phoneNumber.id ? "number-row-active" : ""
                    }`}
                    key={phoneNumber.id}
                  >
                    <div>
                      <strong>{phoneNumber.displayNumber}</strong>
                      <span>{phoneNumber.name || "Sans nom"}</span>
                    </div>
                    <div className="number-row-actions">
                      <span className="pill pill-neutral">{phoneNumber.phoneNumberType || "Retell"}</span>
                      {companyAssignment?.phone_number === phoneNumber.id ? (
                        <span className="pill pill-neutral">Choisi</span>
                      ) : !canAssignNumber ? (
                        <span className="pill pill-neutral">Plan requis</span>
                      ) : (
                        <form action={assignRetellNumber} className="inline-action-form">
                          <input name="retellPhoneNumberId" type="hidden" value={phoneNumber.id} readOnly />
                          <ActionSubmitButton
                            className="button button-secondary button-inline"
                            idleLabel="Choisir"
                            pendingLabel="Attribution..."
                          />
                        </form>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            ) : null}

            {!retellNumbersError && totalPages > 1 ? (
              <div className="pagination-row">
                <a
                  className={`button button-secondary button-inline ${
                    currentPage <= 1 ? "button-disabled" : ""
                  }`}
                  href={currentPage > 1 ? `/dashboard?page=${currentPage - 1}` : "/dashboard"}
                  aria-disabled={currentPage <= 1}
                >
                  Précédent
                </a>
                <span className="text-muted">
                  Page {currentPage} / {totalPages}
                </span>
                <a
                  className={`button button-secondary button-inline ${
                    currentPage >= totalPages ? "button-disabled" : ""
                  }`}
                  href={
                    currentPage < totalPages ? `/dashboard?page=${currentPage + 1}` : `/dashboard?page=${totalPages}`
                  }
                  aria-disabled={currentPage >= totalPages}
                >
                  Suivant
                </a>
              </div>
            ) : null}
          </article>

          <article className="card operations-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">Appels</p>
                <h2>Derniers appels</h2>
              </div>
              <span className="pill pill-neutral">{latestCalls?.length || 0}</span>
            </div>

            {!latestCalls?.length ? (
              <p className="text-muted">Aucun appel reçu pour le moment.</p>
            ) : (
              <div className="number-list">
                {latestCalls.map((call) => (
                  <article className="number-row" key={call.external_call_id}>
                    <div>
                      <strong>{call.customer_number || "Numéro masqué"}</strong>
                      <span>
                        {formatCallTime(call.created_at)}
                        {call.status ? ` · ${call.status}` : ""}
                      </span>
                      {call.summary ? <span>{excerptText(call.summary, 140)}</span> : null}
                      {!call.summary && call.transcript ? (
                        <span>{excerptText(call.transcript, 140)}</span>
                      ) : null}
                      {call.transcript ? (
                        <details className="call-transcript">
                          <summary>Voir la transcription complète</summary>
                          <div className="call-transcript-body">{call.transcript}</div>
                        </details>
                      ) : null}
                    </div>
                    <span className="pill pill-neutral">
                      {call.booking_status || call.urgency || "reçu"}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </article>

          <article className="card operations-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">Emails</p>
                <h2>Tests cycle de vie</h2>
              </div>
            </div>

            <p className="text-muted">
              Envoyez-vous un email de rappel ou d&apos;expiration pour valider Resend et le contenu.
            </p>

            <div className="number-row-actions">
              <form action={sendTrialLifecycleTest}>
                <input name="kind" type="hidden" value="reminder" readOnly />
                <ActionSubmitButton
                  className="button button-secondary button-inline"
                  idleLabel="Tester rappel"
                  pendingLabel="Envoi..."
                />
              </form>
              <form action={sendTrialLifecycleTest}>
                <input name="kind" type="hidden" value="expired" readOnly />
                <ActionSubmitButton
                  className="button button-secondary button-inline"
                  idleLabel="Tester expiration"
                  pendingLabel="Envoi..."
                />
              </form>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
