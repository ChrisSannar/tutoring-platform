# 08 — Tutor Deletes Collected Pilot Data

**What to build:** The Tutor can explicitly delete personal data collected by the pilot with predictable handling of related Invitations, Student Sessions, and Session Requests.

**Blocked by:** 07 — Student Submits a Session Request.

**Status:** claimed

- [ ] Only the Tutor can initiate deletion through a deliberate authenticated action.
- [ ] Related pilot records are removed or invalidated according to an explicit observable contract.
- [ ] Deleted identities and sessions cannot continue accessing protected resources.
- [ ] Responses and logs do not echo deleted personal or user-authored content.
- [ ] Browser and black-box tests prove success, authorization failure, and post-deletion behavior.
