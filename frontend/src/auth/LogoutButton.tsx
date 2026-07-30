import { useRef, useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";

export function LogoutButton() {
  const dialog = useRef<HTMLDialogElement>(null);
  const [failed, setFailed] = useState(false);

  async function logOut() {
    setFailed(false);
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfTokenFromCookie() },
      });
      if (!response.ok) throw new Error("Logout failed");
      window.location.assign("/");
    } catch {
      setFailed(true);
    }
  }

  return <>
    <button type="button" onClick={() => dialog.current?.showModal()}>Log out</button>
    <dialog ref={dialog} aria-labelledby="logout-heading">
      <h2 id="logout-heading">Log out?</h2>
      <p>You’ll need to request a new Login Link to sign in again.</p>
      {failed ? <p role="alert">Logout failed. Please try again.</p> : null}
      <div className="logout-actions">
        <button type="button" onClick={() => dialog.current?.close()}>Stay signed in</button>
        <button type="button" onClick={() => void logOut()}>Log out</button>
      </div>
    </dialog>
  </>;
}
