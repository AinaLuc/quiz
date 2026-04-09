"use client";

import { useEffect } from "react";

export function RetellDebugConsole({ calls }) {
  useEffect(() => {
    if (!Array.isArray(calls) || !calls.length) {
      console.info("[Cyvora][Retell] No call data available in dashboard payload.");
      return;
    }

    console.log("[Cyvora][Retell] Dashboard call data", calls);
  }, [calls]);

  return null;
}
