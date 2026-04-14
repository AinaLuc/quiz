import Link from "next/link";
import { redirect } from "next/navigation";
import { SiteHeader } from "@/components/site-header";
import { GoogleAuthButton } from "@/components/google-auth-button";
import { signInWithPassword } from "@/app/actions";
import { createClient } from "@/lib/supabase/server";

export default async function SignInPage({ searchParams }) {
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
            <p className="eyebrow">Connexion</p>
            <h1 className="title-lg">Reconnectez-vous à votre centre d&apos;opérations Cyvora.</h1>
            <p className="text-muted">
              Suivez vos appels, vos rendez-vous et vos performances depuis un tableau
              de bord simple.
            </p>
          </div>

          <div className="auth-card">
            <form className="auth-form" action={signInWithPassword}>
              <GoogleAuthButton mode="signin" />

              <div className="auth-divider">
                <span>ou continuer avec courriel</span>
              </div>

              {error ? <div className="alert alert-error">{error}</div> : null}

              <label>
                Courriel professionnel
                <input name="email" type="email" placeholder="operations@entreprise.ca" required />
              </label>

              <label>
                Mot de passe
                <input name="password" type="password" placeholder="Votre mot de passe" required />
              </label>

              <button className="button button-primary" type="submit">
                Se connecter
              </button>

              <p className="text-muted" style={{ margin: 0 }}>
                Pas encore de compte?{" "}
                <Link className="inline-link" href="/signup">
                  Commencer l&apos;essai gratuit
                </Link>
              </p>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}
