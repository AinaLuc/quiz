"use client";

import { useTransition } from "react";
import { signInWithGoogle } from "@/app/actions";

export function GoogleAuthButton({ mode = "signin" }) {
  const [isPending, startTransition] = useTransition();

  const label =
    mode === "signup" ? "S'inscrire avec Google" : "Continuer avec Google";

  return (
    <button
      className="button button-google"
      type="button"
      disabled={isPending}
      onClick={() => {
        startTransition(async () => {
          await signInWithGoogle();
        });
      }}
    >
      <span className="google-mark" aria-hidden="true">
        G
      </span>
      {isPending ? "Redirection..." : label}
    </button>
  );
}
