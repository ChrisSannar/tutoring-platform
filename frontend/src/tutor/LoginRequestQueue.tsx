import { useEffect, useState } from "react";

type LoginRequest = { id: string; email: string; status: "pending" | "generated" };

export function LoginRequestQueue({ csrfToken }: { csrfToken: string }) {
  const [requests, setRequests] = useState<LoginRequest[]>([]);
  const [links, setLinks] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState("");

  useEffect(() => {
    void fetch("/api/tutor/login-requests").then(async (response) => {
      if (response.ok) setRequests((await response.json()).login_requests);
    });
  }, []);

  async function generate(request: LoginRequest) {
    const response = await fetch(`/api/tutor/login-requests/${request.id}/magic-link`, {
      method: "POST", headers: { "X-CSRF-Token": csrfToken },
    });
    if (!response.ok) return;
    const body = await response.json();
    setLinks((current) => ({ ...current, [request.id]: body.magic_link }));
    setRequests((current) => current.map((item) => item.id === request.id ? { ...item, status: "generated" } : item));
  }

  async function dismiss(request: LoginRequest) {
    const response = await fetch(`/api/tutor/login-requests/${request.id}`, {
      method: "DELETE", headers: { "X-CSRF-Token": csrfToken },
    });
    if (response.ok) setRequests((current) => current.filter((item) => item.id !== request.id));
  }

  return <section aria-labelledby="login-requests-heading"><h2 id="login-requests-heading">Login Requests</h2>{requests.length === 0 ? <p>No active Login Requests.</p> : requests.map((request) => <article key={request.id}><h3>{request.email}</h3><p>Status: {request.status}</p>{request.status === "pending" ? <button onClick={() => generate(request)}>Generate Login Link</button> : null}{links[request.id] ? <><label htmlFor={`login-link-${request.id}`}>Login Link</label><input id={`login-link-${request.id}`} value={links[request.id]} readOnly /><button onClick={async () => { await navigator.clipboard.writeText(links[request.id]); setCopied(request.id); }}>Copy Login Link</button>{copied === request.id ? <p role="status">Login Link copied</p> : null}</> : null}<button onClick={() => dismiss(request)}>Dismiss Login Request</button></article>)}</section>;
}
