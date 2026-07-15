# 04 — Tutor Creates a Personalized Invitation

**What to build:** The authenticated Tutor can create and activate a secure personalized Invitation for a known Invitee without leaking Private Tutor Notes.

**Blocked by:** 03 — Invite-Only Tutor Authentication.

**Status:** ready-for-agent

- [ ] Invitation creation binds a normalized email and separates private and shared content.
- [ ] Activation returns the raw seven-day token once while storing only its hash.
- [ ] Anonymous and Student callers cannot create or inspect Tutor Invitation records.
- [ ] Public response models cannot serialize Private Tutor Notes.
- [ ] The Tutor UI and black-box negative paths are tested through confirmed seams.
