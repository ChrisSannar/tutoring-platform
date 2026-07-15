# 08 — Tutor Deletes Collected Pilot Data

**What to build:** The Tutor can explicitly delete personal data collected by the pilot with predictable handling of related Invitations, Student Sessions, and Session Requests.

**Blocked by:** 07 — Student Submits a Session Request.

**Status:** resolved

- [x] Only the Tutor can initiate deletion through a deliberate authenticated action.
- [x] Related pilot records are removed or invalidated according to an explicit observable contract.
- [x] Deleted identities and sessions cannot continue accessing protected resources.
- [x] Responses and logs do not echo deleted personal or user-authored content.
- [x] Browser and black-box tests prove success, authorization failure, and post-deletion behavior.

## Answer

Implemented deliberate Tutor-driven deletion of a Student's collected pilot data
through the black-box HTTP and Playwright seams. The Tutor must authenticate, satisfy
same-origin CSRF protection, and type `DELETE COLLECTED DATA`. One transaction removes
the Student's Invitations and claim tokens, Session Requests, Student Sessions,
authentication tokens and request events, then the Student account. The response is a
count-only receipt for Invitations, Student Sessions, and Session Requests; it does not
echo identity, private notes, shared messages, request messages, or tokens.

The browser journey proves a Student receives a safe authorization failure, the Tutor
can complete the deliberate deletion, removed content disappears from the Tutor view,
and the deleted Student's old browser can no longer use protected resources. Black-box
HTTP tests additionally prove exact confirmation, transaction results, safe errors,
and post-deletion denial.

Verification: `bun run test` passed 62 backend tests and 10 Playwright tests.
