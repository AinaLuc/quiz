import Link from "next/link";
import { redirect } from "next/navigation";
import { SiteHeader } from "@/components/site-header";
import { GoogleAuthButton } from "@/components/google-auth-button";
import { signUp } from "@/app/actions";
import { createClient } from "@/lib/supabase/server";

export default async function SignUpPage({ searchParams }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/dashboard");
  }

  const params = await searchParams;
  const error = params?.error;

  return (
    <div className="app-shell">
      <SiteHeader session={user ? { user } : null} />

      <main className="auth-layout">
        <section className="auth-grid">
          <div>
            <p className="eyebrow">Inscription</p>
            <h1 className="title-lg">Activez Cyvora en moins de 3 minutes.</h1>
            <p className="text-muted">
              Démarrez votre essai gratuit de 10 jours pour tester l&apos;accueil
              téléphonique IA avec votre équipe CVAC.
            </p>
          </div>

          <div className="auth-card">
            <form className="auth-form" action={signUp}>
              <GoogleAuthButton mode="signup" />

              <div className="auth-divider">
                <span>ou créer un compte avec courriel</span>
              </div>

              {error ? <div className="alert alert-error">{error}</div> : null}

              <label>
                Nom de l&apos;entreprise
                <input name="company" type="text" placeholder="Climatisation Tremblay" required />
              </label>

              <label>
                Courriel
                <input name="email" type="email" placeholder="info@entreprise.ca" required />
              </label>

              <label>
                Téléphone principal
                <input name="phone" type="tel" placeholder="(514) 555-0148" required />
              </label>

              <label>
                Mot de passe
                <input name="password" type="password" placeholder="Créez un mot de passe" required />
              </label>

              <button className="button button-primary" type="submit">
                Commencer l&apos;essai gratuit
              </button>

              <p className="text-muted" style={{ margin: 0 }}>
                Déjà inscrit?{" "}
                <Link className="inline-link" href="/signin">
                  Se connecter
                </Link>
              </p>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}
