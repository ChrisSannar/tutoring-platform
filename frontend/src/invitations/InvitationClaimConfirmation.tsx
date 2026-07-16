import { useEffect, useState } from "react";

import { StudentWorkspace } from "../students/StudentWorkspace";
import type { Student } from "../students/types";
import type { InviteeInvitation } from "./types";

export function InvitationClaimConfirmation() {
  const token = new URLSearchParams(window.location.search).get("token") ?? "";
  const [invitation, setInvitation] = useState<InviteeInvitation | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [student, setStudent] = useState<Student | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    void fetch(
      `/api/invitation-claims/confirm?token=${encodeURIComponent(token)}`,
    ).then(async (response) => {
      if (!response.ok) {
        setUnavailable(true);
        return;
      }
      const confirmation = await response.json();
      setInvitation(confirmation);
      setDisplayName(confirmation.display_name);
    });
  }, [token]);

  async function confirmClaim() {
    const response = await fetch("/api/invitation-claims/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, display_name: displayName }),
    });
    if (!response.ok) {
      setUnavailable(true);
      return;
    }
    const claimed = await response.json();
    window.history.replaceState({}, "", "/student");
    setStudent(claimed);
  }

  if (student) return <StudentWorkspace initialStudent={student} />;
  if (unavailable) return <main><h1>Invitation Claim unavailable</h1></main>;
  if (!invitation) return <main><p>Loading Invitation Claim…</p></main>;
  return (
    <main><section className="hero">
      <h1>Confirm Invitation Claim</h1>
      <label htmlFor="claim-bound-email">Bound email</label>
      <input
        id="claim-bound-email"
        type="email"
        value={invitation.email}
        readOnly
      />
      <label htmlFor="claim-display-name">Display name</label>
      <input
        id="claim-display-name"
        value={displayName}
        onChange={(event) => setDisplayName(event.target.value)}
      />
      <button onClick={confirmClaim}>Confirm Invitation Claim</button>
    </section></main>
  );
}
