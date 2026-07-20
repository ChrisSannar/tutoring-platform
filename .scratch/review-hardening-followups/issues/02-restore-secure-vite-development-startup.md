# 02 — Restore secure Vite development startup

**What to build:** Let contributors run the development frontend with React Refresh while retaining the restrictive browser-security policy on production-like preview responses.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The documented development command renders the application instead of being blocked by the React Refresh inline preamble.
- [x] Preview and production-like serving retain the required same-origin content policy, frame denial, MIME-sniffing protection, strict referrer policy, and disabled unused permissions.
- [x] Development and preview security-header configuration share one clear policy definition where their requirements are identical without forcing the production script policy onto development.
- [x] Browser coverage proves both successful development rendering and the production-preview security-header contract.
- [x] The authoritative repository test command remains green.

## Answer

The production `script-src 'self'` policy was being sent by the Vite development
server even though React Refresh injects an inline preamble. Development now retains
the security headers it shares with preview without receiving the production-only
content security policy. Preview continues to send the exact restrictive CSP and the
shared frame, MIME-sniffing, referrer, and permissions protections.

Playwright now starts an isolated Vite development server alongside the existing
production preview. Browser tests prove that the documented development startup
renders and that a production-preview navigation returns the full security-header
contract.

Verification:

- Targeted regression: 2 passed.
- Authoritative suite: 99 backend tests and 14 Playwright tests passed.
