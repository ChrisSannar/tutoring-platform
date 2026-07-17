import { type FormEvent, useRef, useState } from "react";

export function InquiryModal() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/inquiries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, message }),
    });
    if (!response.ok) {
      setConfirmation("We could not send your request. Please try again later.");
      return;
    }
    const accepted = await response.json();
    setConfirmation(accepted.message);
  }

  return (
    <>
      <button onClick={() => dialogRef.current?.showModal()}>
        Request tutoring
      </button>
      <dialog ref={dialogRef} aria-labelledby="inquiry-heading">
        <h2 id="inquiry-heading">Request tutoring</h2>
        {confirmation ? (
          <>
            <p role="status">{confirmation}</p>
            <button onClick={() => dialogRef.current?.close()}>Close</button>
          </>
        ) : (
          <form onSubmit={submit}>
            <label htmlFor="inquiry-email">Email address</label>
            <input
              id="inquiry-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <label htmlFor="inquiry-message">How can tutoring help?</label>
            <textarea
              id="inquiry-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              maxLength={2000}
              required
            />
            <div>
              <button type="submit">Send request</button>
              <button type="button" onClick={() => dialogRef.current?.close()}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </dialog>
    </>
  );
}
