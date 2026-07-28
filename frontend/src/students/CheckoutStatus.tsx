import { useEffect, useState } from "react";

type Checkout = {
  checkout_session_id: string;
  checkout_url: string;
  amount_cents: number;
  currency: "USD";
  status: "pending" | "fulfilled" | "expired" | "mismatch";
};

export function CheckoutStatus() {
  const pathId = window.location.pathname.startsWith("/checkout/fake/")
    ? window.location.pathname.split("/").at(-1)
    : null;
  const sessionId = pathId || new URLSearchParams(window.location.search).get("session_id");
  const [checkout, setCheckout] = useState<Checkout | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    if (!sessionId) { setUnavailable(true); return; }
    void fetch(`/api/student/checkouts/${encodeURIComponent(sessionId)}`).then(async (response) => {
      if (!response.ok) { setUnavailable(true); return; }
      setCheckout(await response.json());
    });
  }, [sessionId]);

  if (unavailable) return <main className="login-authentication"><h1>Checkout unavailable</h1></main>;
  if (!checkout) return <main className="login-authentication"><p>Loading checkout status…</p></main>;
  const amount = new Intl.NumberFormat("en-US", { style: "currency", currency: checkout.currency }).format(checkout.amount_cents / 100);
  const fake = window.location.pathname.startsWith("/checkout/fake/");
  return <main className="login-authentication" aria-labelledby="checkout-heading"><p className="eyebrow">Secure payment</p><h1 id="checkout-heading">{fake ? "Test Checkout" : "Payment status"}</h1><p>Exact session price: {amount}</p><p role="status">Status: {checkout.status}</p>{fake ? <p>This deterministic test provider never marks payment complete from the browser.</p> : null}<a href={fake ? `/checkout/return?session_id=${encodeURIComponent(checkout.checkout_session_id)}` : "/student"}>{fake ? "Return to tutoring platform" : "Return to Student workspace"}</a></main>;
}
