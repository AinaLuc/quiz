export function UpgradeForm({ disabled = false, label = "Passer au plan payant" }) {
  return (
    <form action="/api/stripe/checkout" method="post">
      <button className="button button-primary" type="submit" disabled={disabled}>
        {label}
      </button>
    </form>
  );
}
