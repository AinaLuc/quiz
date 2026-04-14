"use client";

import { useTransition } from "react";
import { signOut } from "@/app/actions";

export function SignOutButton() {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() => {
        startTransition(async () => {
          await signOut();
        });
      }}
    >
      {isPending ? "Déconnexion..." : "Déconnexion"}
    </button>
  );
}
