import Link from "next/link";
import { SignOutButton } from "@/components/sign-out-button";

export function SiteHeader({ session }) {
  return (
    <header className="site-header">
      <Link className="brand" href="/">
        <span className="brand-mark">C</span>
        <span>Cyvora</span>
      </Link>

      <nav className="nav-pill">
        <Link href="/">Accueil</Link>
        {session ? <Link href="/dashboard">Dashboard</Link> : <Link href="/signin">Connexion</Link>}
        {session ? <Link href="/dashboard">Compte</Link> : <Link href="/signup">Essai gratuit</Link>}
        {session ? <SignOutButton /> : null}
      </nav>
    </header>
  );
}
