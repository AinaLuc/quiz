"use client";

import { useEffect } from "react";

function normalizeCallForConsole(call) {
  return {
    externalCallId: call?.external_call_id || null,
    customerNumber: call?.customer_number || null,
    urgency: call?.urgency || null,
    bookingStatus: call?.booking_status || null,
    transcript: call?.transcript || null,
    createdAt: call?.created_at || null,
  };
}

export function RetellDebugConsole({ calls }) {
  useEffect(() => {
    if (!Array.isArray(calls) || !calls.length) {
      console.info("[Cyvora][Retell] No call data available in dashboard payload.");
      return;
    }

    console.log("[Cyvora][Retell] Dashboard call data", calls.map(normalizeCallForConsole));
  }, [calls]);

  return null;
}
