const routes = [
  ["Landing page", "/"],
  ["Account sign-in", "/sign-in"],
  ["Account sign-in confirmation", "/sign-in/confirm?token=dev-token"],
  ["Student workspace", "/student"],
  ["Checkout return", "/checkout/return?session_id=dev-session"],
  ["Fake checkout", "/checkout/fake/dev-session"],
  ["Invitation", "/invite/dev-token"],
  ["Tutor workspace", "/tutor"],
  ["Tutor sign-in", "/tutor/sign-in"],
  ["Tutor sign-in confirmation", "/tutor/sign-in/confirm?token=dev-token"],
] as const;

export function DevTools() {
  return (
    <details className="dev-tools">
      <summary>Dev tools</summary>
      <label htmlFor="dev-route">Route</label>
      <select
        id="dev-route"
        defaultValue=""
        onChange={(event) => window.location.assign(event.target.value)}
      >
        <option value="" disabled>Choose a route</option>
        {routes.map(([label, path]) => <option key={path} value={path}>{label}</option>)}
      </select>
    </details>
  );
}
