import { useEffect, useState } from "react";

type TutorSessionRequest = {
  id: string;
  service: string;
  preferred_start: string;
  timezone: string;
  message: string | null;
  status: "pending";
  student: {
    id: string;
    email: string;
    display_name: string;
  };
};

export function PendingSessionRequests({ csrfToken }: { csrfToken: string }) {
  const [sessionRequests, setSessionRequests] = useState<TutorSessionRequest[]>(
    [],
  );
  const [deletionStudentId, setDeletionStudentId] = useState("");
  const [deletionConfirmation, setDeletionConfirmation] = useState("");
  const [deletionMessage, setDeletionMessage] = useState("");

  useEffect(() => {
    void fetch("/api/tutor/session-requests").then(async (response) => {
      if (!response.ok) return;
      const result = await response.json();
      setSessionRequests(result.requests);
    });
  }, []);

  async function deleteCollectedPilotData() {
    const response = await fetch(
      `/api/tutor/students/${deletionStudentId}/pilot-data`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({ confirmation: deletionConfirmation }),
      },
    );
    if (!response.ok) return;
    setSessionRequests((requests) =>
      requests.filter(
        (sessionRequest) =>
          sessionRequest.student.id !== deletionStudentId,
      ),
    );
    setDeletionStudentId("");
    setDeletionConfirmation("");
    setDeletionMessage("Collected pilot data deleted");
    window.dispatchEvent(new Event("students-changed"));
  }

  return (
    <>
      <section>
        <h2>Pending Session Requests</h2>
        {sessionRequests.map((sessionRequest) => (
          <article key={sessionRequest.id}>
            <h3>{sessionRequest.student.display_name}</h3>
            <p>{sessionRequest.student.email}</p>
            <p>{sessionRequest.service}</p>
            {sessionRequest.message ? <p>{sessionRequest.message}</p> : null}
            <button
              onClick={() => setDeletionStudentId(sessionRequest.student.id)}
            >
              Delete collected data
            </button>
          </article>
        ))}
      </section>
      {deletionStudentId ? (
        <section>
          <p>This permanently removes the Student's collected pilot data.</p>
          <label htmlFor="deletion-confirmation">
            Type DELETE COLLECTED DATA to confirm
          </label>
          <input
            id="deletion-confirmation"
            value={deletionConfirmation}
            onChange={(event) => setDeletionConfirmation(event.target.value)}
          />
          <button
            disabled={deletionConfirmation !== "DELETE COLLECTED DATA"}
            onClick={deleteCollectedPilotData}
          >
            Permanently delete collected data
          </button>
        </section>
      ) : null}
      {deletionMessage ? <p>{deletionMessage}</p> : null}
    </>
  );
}
