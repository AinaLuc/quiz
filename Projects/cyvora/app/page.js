import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import { createClient } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const session = user ? { user } : null;

  return (
    <div className="app-shell">
      <SiteHeader session={session} />

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">IA réceptionniste CVAC | Québec | Français d&apos;abord</p>
            <h1 className="title-xl">Ne manquez plus aucun appel CVAC.</h1>
            <p className="text-muted" style={{ maxWidth: "60ch", marginTop: 22, fontSize: "1.08rem" }}>
              Cyvora répond, qualifie les urgences, planifie les rendez-vous et convertit
              vos appels entrants en opportunités concrètes, 24/7.
            </p>

            <div className="hero-actions">
              <Link className="button button-primary" href="/signup">
                Démarrer 10 jours gratuits
              </Link>
              <Link className="button button-secondary" href="/signin">
                Se connecter
              </Link>
            </div>

            <ul className="hero-points">
              <li>Accueil téléphonique naturel en français québécois</li>
              <li>Qualification des urgences chauffage, ventilation et climatisation</li>
              <li>Prise de rendez-vous connectée à votre équipe terrain</li>
            </ul>
          </div>

          <div className="hero-card panel">
            <div className="row">
              <span className="pill pill-success">Essai gratuit 10 jours</span>
              <span className="pill pill-neutral">Google + courriel</span>
            </div>

            <div className="call-card">
              <p className="eyebrow" style={{ marginBottom: 8 }}>
                Appel entrant
              </p>
              <h2 style={{ margin: 0, fontSize: "1.65rem" }}>Résidentiel | Laval</h2>
              <p className="text-muted">
                “Ma thermopompe ne démarre plus. J&apos;ai besoin d&apos;un rendez-vous
                aujourd&apos;hui.”
              </p>
            </div>

            <div className="snapshot-grid">
              <article>
                <span>Temps de réponse</span>
                <strong>3 sec</strong>
              </article>
              <article>
                <span>RDV réservés</span>
                <strong>+41%</strong>
              </article>
              <article>
                <span>Appels traités</span>
                <strong>24/7</strong>
              </article>
              <article>
                <span>Langue</span>
                <strong>FR d&apos;abord</strong>
              </article>
            </div>
          </div>
        </section>

        <section className="metrics-band panel">
          <article>
            <strong>92%</strong>
            <span>des appels répondus automatiquement</span>
          </article>
          <article>
            <strong>2.8x</strong>
            <span>plus de rendez-vous après les heures d&apos;ouverture</span>
          </article>
          <article>
            <strong>10 jours</strong>
            <span>d&apos;essai gratuit pour tester Cyvora avec votre équipe</span>
          </article>
        </section>

        <section className="section-gap">
          <div style={{ maxWidth: 680 }}>
            <p className="eyebrow">Pensé pour les entreprises CVAC du Québec</p>
            <h2 className="title-md">
              Seulement l&apos;essentiel pour capter, qualifier et convertir.
            </h2>
          </div>

          <div className="feature-grid section-gap">
            <article className="feature-card">
              <h3 style={{ marginTop: 0, fontSize: "1.35rem" }}>
                Réception d&apos;appels intelligente
              </h3>
              <p className="text-muted">
                Cyvora prend les appels en continu, filtre les urgences, collecte
                l&apos;adresse, l&apos;équipement et le niveau de priorité.
              </p>
            </article>
            <article className="feature-card">
              <h3 style={{ marginTop: 0, fontSize: "1.35rem" }}>
                Prise de rendez-vous automatisée
              </h3>
              <p className="text-muted">
                Propose des créneaux, confirme le client et transmet le tout à votre
                équipe sans friction.
              </p>
            </article>
            <article className="feature-card">
              <h3 style={{ marginTop: 0, fontSize: "1.35rem" }}>
                Suivi des conversions
              </h3>
              <p className="text-muted">
                Gardez en vue les appels manqués récupérés, les urgences créées et les
                nouveaux clients signés.
              </p>
            </article>
          </div>
        </section>

        <section className="cta-panel section-gap">
          <div>
            <p className="eyebrow">Prêt à lancer votre réceptionniste IA</p>
            <h2 className="title-md">
              Configurez Cyvora et activez votre essai gratuit de 10 jours.
            </h2>
          </div>
          <Link className="button button-primary" href={session ? "/dashboard" : "/signup"}>
            {session ? "Ouvrir le dashboard" : "Créer un compte"}
          </Link>
        </section>
      </main>
    </div>
  );
}
