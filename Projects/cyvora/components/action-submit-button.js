"use client";

import { useFormStatus } from "react-dom";

export function ActionSubmitButton({
  idleLabel,
  pendingLabel,
  className = "button button-secondary",
  disabled = false,
}) {
  const { pending } = useFormStatus();
  const isDisabled = pending || disabled;

  return (
    <button className={className} type="submit" disabled={isDisabled}>
      {pending ? pendingLabel : idleLabel}
    </button>
  );
}
