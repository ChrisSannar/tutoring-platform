# 01 — Public Inquiry intake and Tutor queue

**What to build:** Give a Prospect one clear way to request tutoring from the landing page, and give the Tutor a private queue for reviewing and disposing of those Inquiries without granting application access.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The public landing page presents one primary **Request tutoring** action that opens an Inquiry modal without navigating away.
- [ ] A Prospect can submit a normalized valid email and a required plain-text contextual message no longer than 2,000 characters.
- [ ] Successful submission creates a separate Inquiry for every request and shows an on-page confirmation without creating an account or revealing private state.
- [ ] Anonymous submissions are limited to five per hashed IP per hour, and validation, rate-limit, and unexpected errors use safe public responses.
- [ ] Anonymous and Student callers cannot list or mutate Inquiries.
- [ ] The Tutor Dashboard lists active New and Invited Inquiries with safely rendered email, message, and state.
- [ ] The Tutor can archive an Inquiry and can permanently delete one only after explicit confirmation.
- [ ] Black-box HTTP tests cover validation, normalization, repetition, rate limiting, authorization, archive, delete, and sensitive-data response boundaries.

