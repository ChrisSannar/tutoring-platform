# Direct Booking and Tutoring Operations

Status: ready-for-agent

## Problem Statement

The current pilot proves a secure invite-only journey, but it stops at a pending Session
Request and does not yet function as the Tutor's operating system. A Prospect cannot
submit structured interest from the landing page, an Invitee must complete an
unnecessarily long two-link claim flow, and a returning account holder cannot use one
role-aware login surface. The Tutor has no searchable Student directory, availability
calendar, Inquiry queue, credit ledger, refund workflow, or lesson-note workspace.

Students likewise lack the tools needed for an ongoing tutoring relationship. They
cannot see true Tutor availability, confirm a funded Booking, reschedule or cancel under
a clear policy, export a Booking to their calendar, see their credit or promotion state,
or read and download Shared Lesson Notes. Payment, scheduling, notes, and account access
therefore remain disconnected manual processes.

The application must grow into a coherent single-Tutor workflow without becoming a
marketplace or generic SaaS product. It must preserve the pilot's security boundaries,
same-origin architecture, explicit migrations, and high-level test seams while keeping
manual email and downloadable calendar files where external integrations are not yet
worth their operational cost.

## Solution

Evolve the existing application in place into an invite-only direct-Booking platform.
The landing page keeps one primary **Request tutoring** action, which opens an Inquiry
modal for a required email and contextual message. The Tutor manages New and Invited
Inquiries, creates an encrypted and redisplayable seven-day Invitation Link, and sends
that link through normal email. The Invitee enters only a display name beside the
read-only bound email; selecting **Create Account** atomically claims the Invitation,
creates the Student account and Student Session, and grants the First Session Promotion.

Returning Tutor and Student accounts share one role-aware Login Request flow. Automated
email delivery remains deferred: eligible Student Login Requests appear in the Tutor
Dashboard, where the Tutor generates and copies a 15-minute Login Link for manual email.
A repository command generates a Tutor Login Link when the Tutor cannot access the
dashboard.

The Student Dashboard presents static welcome guidance, a weekly booking calendar, and
one Shared Lesson Notes accordion. Students choose among derived 60-minute Bookable
Slots in the Tutor Timezone, subject to a 24-hour minimum and eight-week horizon. Their
first Booking automatically uses the First Session Promotion; later Bookings redeem one
Session Credit or use Stripe-hosted Checkout at the Tutor-configured global USD Session
Price. A paid checkout holds the slot for 30 minutes, and only verified idempotent
webhook fulfillment confirms the Booking.

The Tutor Dashboard places a searchable Student list beside the weekly calendar and the
active Inquiry list beneath them. Calendar selection highlights and scrolls to the
associated Student; selecting the Student opens read-only identity, funding state, the
single Upcoming Booking, and lesson-note CRUD. The Tutor manages recurring Availability
Windows, Blocked Time, credits, complimentary Bookings, Meeting Details, Refund
Requests, Lesson Note Drafts, and publication from this privileged surface.

Direct Booking supersedes Session Request. The platform remains authoritative for
Booking time, funding, Meeting Details, and lifecycle. Downloadable `.ics` Calendar
Exports, manual email, and remote-first Meeting Details provide the initial external
workflow; calendar-provider synchronization, automated email, reminders, and a broader
service catalog remain deferred.

## User Stories

1. As a Prospect, I want to understand the Tutor's offer on a public landing page, so that I can decide whether to make contact.
2. As a Prospect, I want one clear Request tutoring action, so that the next step is obvious.
3. As a Prospect, I want Request tutoring to open a modal, so that I can make contact without navigating away.
4. As a Prospect, I want to submit my email and a required contextual message, so that the Tutor knows how they may help me.
5. As a Prospect, I want my Inquiry accepted without creating an account, so that I do not mistake contact for access.
6. As a Prospect, I want an on-page confirmation after submission, so that I know my Inquiry reached the dashboard.
7. As a Prospect, I want repeated submissions to remain separate, so that a later message does not overwrite earlier context.
8. As a Prospect, I want invalid or excessive input rejected safely, so that mistakes are clear without exposing internals.
9. As a Prospect, I want public submission responses to reveal no private business state, so that the Inquiry surface cannot be used for discovery.
10. As a returning account holder, I want the landing header to show Log In, so that I can request access without using the Inquiry form.
11. As an authenticated account holder, I want the landing header to show Dashboard, so that I can return directly to my role's workspace.
12. As a Tutor, I want New Inquiries listed in my dashboard, so that I can review prospective tutoring relationships.
13. As a Tutor, I want each Inquiry to retain its email and required message, so that I have the Prospect's original context.
14. As a Tutor, I want to archive an Inquiry, so that spam or inactive conversations leave my active work list.
15. As a Tutor, I want to permanently delete an Inquiry after confirmation, so that unnecessary personal information can be removed.
16. As a Tutor, I want to create an Invitation Link from an Inquiry with one action, so that onboarding does not expose draft and activation ceremony.
17. As a Tutor, I want creating an Invitation to mark the Inquiry as invited, so that its current state is obvious.
18. As a Tutor, I want an Invited Inquiry to expose applicable link actions, so that I can manage onboarding without searching elsewhere.
19. As a Tutor, I want to create an Invitation Link manually from an email, so that an Inquiry is not required for a known Prospect.
20. As a Tutor, I want manual Invitation creation to avoid manufacturing an Inquiry, so that the Inquiry list remains truthful.
21. As a Tutor, I want an Invitation Link to remain copyable until claim, so that I can retrieve it during a personal email conversation.
22. As a Tutor, I want Invitation Link material encrypted at rest, so that redisplay does not require plaintext token storage.
23. As a Tutor, I want to regenerate an Invitation Link, so that a lost or suspected link can be replaced.
24. As a Tutor, I want to revoke an Invitation Link, so that I can stop onboarding before account creation.
25. As an Invitee, I want an Invitation Link bound to my normalized email, so that the intended identity cannot be substituted during setup.
26. As an Invitee, I want opening the Invitation Link to be observational, so that an email scanner cannot create my account.
27. As an Invitee, I want the setup page to display my read-only bound email, so that I can verify the intended account identity.
28. As an Invitee, I want to enter only my display name, so that initial setup remains minimal.
29. As an Invitee, I want selecting Create Account to atomically claim the Invitation, so that concurrent attempts cannot create duplicate accounts.
30. As an Invitee, I want Create Account to start a Student Session and open my dashboard, so that onboarding has no second email link.
31. As a Student, I want my newly claimed account to receive the First Session Promotion, so that my earliest eligible Booking is free automatically.
32. As a Tutor, I want a claimed Invitee to appear in the Student list, so that account creation completes the role transition.
33. As a Tutor, I want the linked Inquiry to leave the active list after claim, so that the Student list becomes the authoritative relationship view.
34. As an account holder, I want a role-neutral Login Request form, so that Tutor and Student access use one public entry point.
35. As an account holder, I want a generic Login Request response, so that account existence cannot be enumerated.
36. As a returning Student, I want my eligible Login Request to appear for the Tutor, so that the Tutor can deliver my Login Link manually.
37. As a Tutor, I want to generate a Student Login Link on demand, so that its 15-minute lifetime starts when I am ready to send it.
38. As a Tutor, I want to copy the generated Login Link, so that I can send it through normal email.
39. As a Tutor, I want used, expired, and dismissed Login Requests removed from active work, so that the queue remains actionable.
40. As a Tutor, I want a repository command to generate my own Login Link, so that being logged out does not create a dashboard dependency loop.
41. As an account holder, I want opening a Login Link to require explicit confirmation, so that automated link scanners cannot authenticate me.
42. As an account holder, I want Login Links to be single-use and expire after 15 minutes, so that replay exposure remains narrow.
43. As an account holder, I want successful Login Link confirmation to rotate any prior browser session, so that authentication state is not fixed.
44. As an account holder, I want successful login to route by account role, so that I reach the correct dashboard.
45. As an account holder, I want ordinary return visits to reuse my active server-side session, so that I do not request a link every time.
46. As an account holder, I want to log out and revoke my current session, so that I can end access from a device.
47. As a Student, I want static welcome guidance above my dashboard, so that I understand how scheduling and notes work.
48. As a Student, I want my dashboard to place the weekly calendar and Shared Lesson Notes side by side on desktop, so that both ongoing workflows are visible.
49. As a Student on a smaller screen, I want the calendar followed by notes, so that the dashboard remains usable without a cramped two-column layout.
50. As a Student, I want one canonical Shared Lesson Notes accordion, so that past-session material is not duplicated in multiple lists.
51. As a Student, I want each Shared Lesson Note header to show the fixed tutoring date and Tutor-authored title, so that I can identify the session.
52. As a Student, I want selecting a note to expand safely rendered Markdown, so that the content is readable in the dashboard.
53. As a Student, I want expanded note content to scroll within a bounded area, so that a long note does not consume the entire dashboard.
54. As a Student, I want raw HTML in Markdown disabled or sanitized, so that lesson content cannot inject unsafe markup.
55. As a Student, I want to download the original Markdown source, so that I can keep a portable copy.
56. As a Student, I want the Markdown filename derived from session date and note title, so that downloaded files remain identifiable.
57. As a Student, I want to see only published Shared Lesson Notes, so that Tutor drafts never leak.
58. As a Student, I want to see my Session Credit balance, First Session Promotion status, and pending Refund Request status, so that my funding state is clear.
59. As a Student, I want my calendar to use the labeled Tutor Timezone, so that every displayed time follows the local-client policy.
60. As a Student, I want to see only my own Upcoming Booking and currently Bookable Slots, so that other Students' schedules remain private.
61. As a Student, I want other Bookings, Blocked Time, and Slot Holds to remove availability without revealing why, so that private occupancy is not disclosed.
62. As a Student, I want selectable time limited to Availability Windows, so that blank calendar space is not mistaken for Tutor availability.
63. As a Student, I want Bookable Slots to be consecutive 60-minute intervals anchored at the Availability Window start, so that scheduling choices are predictable.
64. As a Student, I want to book no sooner than 24 hours ahead, so that the Tutor receives minimum preparation notice.
65. As a Student, I want to book no farther than eight weeks ahead, so that the calendar does not promise distant availability.
66. As a Student, I want at most one Upcoming Booking, so that the initial scheduling model stays simple.
67. As a Student, I want selecting a Bookable Slot to activate Schedule session, so that selection and confirmation are distinct.
68. As a Student, I want the confirmation modal to show the exact time, 60-minute duration, Tutor Timezone, funding path, and policy warning, so that I understand the commitment.
69. As a Student, I want to add an optional Booking Focus of at most 500 plain-text characters, so that the Tutor can prepare for what I want to study.
70. As a Student, I want all self-service Bookings to be remote initially, so that meeting-mode configuration does not complicate scheduling.
71. As a Student, I want Meeting Details shown when the Tutor has supplied them, so that I know how to join the session.
72. As a Student, I want a Booking to remain valid while Meeting Details are pending, so that the Tutor can send a link later.
73. As a Student, I want my first confirmed Booking funded automatically by the First Session Promotion, so that I do not need a coupon or payment.
74. As a Student, I want the promotion applied to the earliest eligible Booking rather than saved, so that its rule is predictable.
75. As a Student, I want a later Booking to redeem one available Session Credit atomically, so that a retry cannot spend the same credit twice.
76. As a Student, I want paid scheduling to charge the exact Tutor-configured Session Price, so that the browser cannot alter the amount.
77. As a Student, I want paid scheduling to redirect to Stripe-hosted Checkout, so that card entry is handled by the payment provider.
78. As a Student, I want the selected slot held while I complete Checkout, so that another Student cannot take it during payment.
79. As a Student, I want an abandoned or expired Checkout to release its Slot Hold, so that the time becomes bookable again.
80. As a Student, I want successful verified payment to convert the Slot Hold into a Booking once, so that webhook retries cannot duplicate it.
81. As a Student, I want a confirmed Booking to offer a downloadable `.ics` Calendar Export, so that I can add it to my calendar.
82. As a Student, I want the Calendar Export available again from Booking details, so that losing the first download is harmless.
83. As a Student, I want a rescheduled Booking to produce an updated Calendar Export, so that I can replace the old snapshot.
84. As a Student, I want to reschedule repeatedly while at least 24 hours remain, so that a separate reschedule counter does not constrain me.
85. As a Student, I want early rescheduling to retain the original funding, so that I am not charged or debited twice.
86. As a Student, I want early cancellation of a credit-funded Booking to restore the Session Credit, so that I do not lose value.
87. As a Student, I want early cancellation of a promoted Booking to restore the First Session Promotion, so that a responsible cancellation preserves it.
88. As a Student, I want early cancellation of a paid Booking to grant one replacement Session Credit, so that value remains without an automatic refund.
89. As a Student, I want late cancellation to warn that payment, credit, or promotion will be forfeited, so that the consequence is explicit before confirmation.
90. As a Student, I want self-service rescheduling disabled inside 24 hours, so that I contact the Tutor for an exception.
91. As a Student, I want the late-reschedule interface to direct me to normal email, so that the personal exception conversation stays outside automated policy.
92. As a Student, I want to create a Refund Request for an early canceled paid Booking, so that I can ask for money instead of replacement credit.
93. As a Student, I want the replacement credit frozen during refund review, so that I cannot spend it and also receive a refund.
94. As a Student, I want a declined Refund Request to restore my credit, so that value is not lost.
95. As a Student, I want an approved Refund Request to issue a full Stripe refund and remove the frozen credit, so that I receive exactly one form of value.
96. As a Tutor, I want to configure one global USD Session Price in integer cents, so that every paid 60-minute Booking uses one authoritative amount.
97. As a Tutor, I want price changes to apply only to future Checkout Sessions, so that historical payment amounts do not change.
98. As a Tutor, I want to configure one Tutor Timezone, so that all first-release calendars use the same local time basis.
99. As a Tutor, I want to configure default remote Meeting Details, so that new Bookings begin with reusable instructions.
100. As a Tutor, I want each Booking to snapshot Meeting Details, so that later default changes do not rewrite existing sessions.
101. As a Tutor, I want to edit a Booking's Meeting Details after an email conversation, so that the Student sees current connection information.
102. As a Tutor, I want to replace Meeting Details with an address for an exceptional in-person session, so that rare local arrangements do not require a Meeting Mode system.
103. As a Tutor, I want to define recurring weekly Availability Windows from my calendar, so that Students can select only intended time.
104. As a Tutor, I want to add one-off Blocked Time, so that holidays and appointments remove otherwise recurring slots.
105. As a Tutor, I want to edit or delete availability through a small calendar modal, so that schedule maintenance remains direct.
106. As a Tutor, I want my weekly calendar to show all Bookings, so that I can operate the single tutoring business.
107. As a Tutor, I want selecting a Booking to highlight and scroll to its Student, so that the calendar acts as a wayfinder into the Student list.
108. As a Tutor, I want the calendar selection not to open the Student modal automatically, so that modal opening remains an explicit Student-list action.
109. As a Tutor, I want to search Students by identity, so that I can find a relationship quickly.
110. As a Tutor, I want selecting a Student to open one Student Detail modal, so that identity, funding, Booking, and note work share context.
111. As a Tutor, I want Student name and login email read-only, so that a casual edit cannot mutate login identity.
112. As a Tutor, I want the modal to display the Student's available credits, promotion state, Refund Requests, and Upcoming Booking, so that operational state is visible.
113. As a Tutor, I want to grant or deduct Session Credits with a required reason, so that balance changes are accountable.
114. As a Tutor, I want every credit event recorded in an immutable Credit Ledger, so that the balance has an auditable source.
115. As a Tutor, I want to create a Complimentary Booking, so that I can schedule without charging or consuming Student funding.
116. As a Tutor, I want complimentary funding recorded explicitly, so that it is not confused with a promotion or missing payment.
117. As a Tutor, I want to move a Booking to a free Bookable Slot without changing its funding, so that ordinary support edits are safe.
118. As a Tutor, I want a Tutor Override to use an otherwise-free time outside Availability Windows or horizon limits, so that I retain final scheduling authority.
119. As a Tutor, I want Tutor-initiated changes to preserve funding by default, so that the Student is not penalized for my edit.
120. As a Tutor, I want a warning before an override outside normal availability, so that exceptional scheduling remains intentional.
121. As a Tutor, I want to review Refund Requests, so that cash refunds remain deliberate.
122. As a Tutor, I want approving a Refund Request to issue only a full refund, so that partial-refund complexity remains out of the first release.
123. As a Tutor, I want to decline a Refund Request and restore the frozen credit, so that Student value remains available.
124. As a Tutor, I want a Past Booking to become note-eligible automatically after its end, so that I do not perform a separate completion action.
125. As a Tutor, I want canceled Bookings excluded from lesson-note creation, so that notes remain tied to sessions that could have occurred.
126. As a Tutor, I want to create and edit a Lesson Note Draft for one Past Booking, so that I can prepare shared material privately.
127. As a Tutor, I want Lesson Note Drafts labeled clearly, so that private drafts are not mistaken for published material.
128. As a Tutor, I want explicit Publish to create the Shared Lesson Note, so that saving a draft never leaks content.
129. As a Tutor, I want later edits to update the same Shared Lesson Note and download, so that corrections remain consistent.
130. As a Tutor, I want confirmed deletion to remove Student access to a Shared Lesson Note, so that CRUD behavior is complete.
131. As a Tutor, I want Lesson Notes capped at 100 KB with no attachments, so that the first release remains simple and bounded.
132. As a Tutor, I want Inquiry, Login Request, Student, Booking, payment, and note content excluded from normal logs, so that operational logging does not expose sensitive data.
133. As a Tutor, I want the active Inquiry list below the Student/calendar layout, so that acquisition work remains visible without displacing operations.
134. As a Tutor, I want automated Invitation and Login emails deferred, so that the first release avoids mail-service infrastructure.
135. As a Tutor, I want automated Booking reminders and change emails deferred, so that personal communication remains manual.
136. As an operator, I want Stripe secrets, webhook secrets, and Invitation encryption keys supplied through fail-closed configuration, so that insecure defaults cannot reach production.
137. As an operator, I want Invitation ciphertext erased at claim, revocation, expiration, or regeneration, so that retrievable access material does not outlive its purpose.
138. As an operator, I want processed Stripe webhook identifiers retained uniquely, so that duplicate delivery cannot duplicate fulfillment.
139. As an operator, I want Slot Hold expiration and Stripe reconciliation observable without logging payment details, so that failures can be repaired safely.
140. As a maintainer, I want direct Booking to replace Session Request, so that two competing scheduling models do not coexist.
141. As a maintainer, I want existing Session Request ownership, UTC, idempotency, and Tutor-query patterns reused where appropriate, so that proven security seams are not discarded.
142. As a maintainer, I want account, session, Invitation, and authorization invariants preserved during schema evolution, so that post-pilot growth does not weaken the baseline.
143. As a maintainer, I want unsafe cookie-authenticated mutations to require same-origin and CSRF validation, so that every new privileged workflow follows the established boundary.
144. As a maintainer, I want Student endpoints constrained to their own Booking, funding, and Shared Lesson Notes, so that cross-Student access fails closed.
145. As a maintainer, I want Tutor endpoints to use explicit response allowlists, so that private fields do not leak through model expansion.
146. As a maintainer, I want anonymous Inquiry and Login Request endpoints rate-limited, so that public write surfaces cannot be abused without bound.
147. As a maintainer, I want retries and concurrent submissions to produce one funding and Booking outcome, so that network behavior cannot corrupt the ledger.
148. As a developer, I want the full post-pilot journey exercised through Playwright, so that the browser workflow remains verifiable from a clean checkout.
149. As a developer, I want black-box HTTP tests for security, concurrency, funding, and webhooks, so that failures are observable without coupling to implementation structure.
150. As a developer, I want Stripe behavior testable without real external network access, so that the repository test command remains deterministic.

## Implementation Decisions

- The existing React/TypeScript/Bun/Vite frontend and FastAPI/SQLite backend remain in
  one application monorepo. Root tooling continues to orchestrate application layers.
- Browser and API remain on one origin. Frontend calls use relative API paths, local
  development proxies those paths, and the backend does not add CORS.
- Synchronous SQLAlchemy remains the persistence boundary and Alembic remains the sole
  schema authority. The API never applies migrations during startup.
- Existing liveness, readiness, sanitized errors, request IDs, browser headers, locked
  dependencies, and fail-closed non-development configuration remain mandatory.
- Direct Booking is the only user-facing scheduling model. Session Request endpoints,
  persistence, statuses, service selector, and UI are superseded and removed only after
  the direct-Booking journey is proven.
- No production deployment contains data that requires automatic conversion from
  Session Request to Booking. Existing Session Requests must never be inferred as paid
  or confirmed Bookings; local pilot data may be discarded through an explicit schema
  transition or reset.
- Existing Account identities, account roles, unique normalized email, and session
  security contracts remain authoritative through schema changes.
- Public landing content exposes one Request tutoring primary action and one role-aware
  Log In/Dashboard utility. Future promotional content and reviews must not be required
  for this spec.
- Inquiry requires a normalized valid email and a non-empty plain-text contextual
  message capped at 2,000 characters.
- Anonymous Inquiry submission is initially limited to five submissions per hashed IP
  per hour. CAPTCHA is not introduced unless observed abuse warrants it.
- Repeated submissions create separate Inquiry records. New, Invited, and Archived are
  distinct Inquiry concepts; archive retains a record and confirmed delete removes it.
- An Inquiry grants no access. Creating an Invitation from an Inquiry links the records
  and changes the Inquiry to Invited.
- Manual Invitation creation accepts only an email and creates no synthetic Inquiry.
- Invitation creation is one atomic Tutor action that creates a seven-day active link;
  draft and activation are not exposed in the product interface.
- Invitation Link lookup uses a hash. A separately encrypted copy supports Tutor
  redisplay until claim. Encryption keys come from typed secret configuration and no
  insecure non-development default is allowed.
- Invitation ciphertext is returned only to an authenticated Tutor and erased at claim,
  revocation, expiration, or regeneration. Regeneration invalidates the prior hash and
  ciphertext before returning the replacement.
- Invitation lifecycle is `created -> opened -> claimed`, with `revoked` and `expired`
  terminal alternatives. Opening records the first successful setup-data response but
  neither consumes nor extends the link.
- Invitation expiration remains seven days from creation. Lazy persistence may record
  expiration on the first later lookup or mutation; no background scheduler is needed.
- Account setup accepts only display name and the read-only Invitation email. The
  Invitation Link itself authorizes initial claim; no second verification link exists.
- Create Account atomically claims the Invitation, creates the Student account, creates
  a Student Session, and appends the First Session Promotion to the Credit Ledger.
- Claim remains concurrency-safe and one normalized email cannot belong to multiple
  Student accounts.
- Login Request is distinct from Inquiry. It accepts email publicly, returns the same
  response for eligible and ineligible addresses, and uses existing email/IP abuse
  limits without exposing account existence.
- Eligible Student Login Requests persist in a Tutor-only active queue. Public
  submission does not immediately create the Login Link.
- Tutor-triggered generation creates the Login Link and begins its 15-minute lifetime.
  The Tutor copies and manually emails it. Used, expired, and dismissed Login Requests
  leave the active queue.
- A repository command creates a short-lived Tutor Login Link without dashboard access.
  It prints sensitive output once and never logs or persists plaintext beyond the
  ordinary hashed Login Link record.
- Login Link confirmation is role-neutral. GET verifies active state without mutation;
  POST consumes once, rotates a prior browser session, creates the new session, and
  returns the authenticated role for dashboard routing.
- Opaque server-side sessions retain 30-day inactivity and 90-day absolute expiration,
  secure cookie properties, activity extension limits, rotation, logout, and revocation.
- Tutor settings own one global USD Session Price stored as integer cents, one IANA Tutor
  Timezone, and one default remote Meeting Details value.
- Tutor setting changes affect only future snapshots. Existing paid amounts and Booking
  Meeting Details do not change retroactively.
- The first release has one 60-minute tutoring offering and no service catalog.
- Booking Focus is optional plain text capped at 500 characters.
- All self-service Bookings are remote. Meeting Details may be pending at confirmation
  and remain Tutor-controlled. Exceptional in-person arrangements use manually updated
  Meeting Details and ordinary availability controls, not Meeting Mode or travel logic.
- Availability Window is a recurring weekly interval in Tutor Timezone. Blocked Time is
  a date-specific exception. Both are managed through the Tutor weekly calendar.
- Bookable Slots are derived, not persisted inventory. They are consecutive 60-minute
  intervals anchored at each Availability Window's start and removed by conflicts.
- Student self-scheduling includes only slots at least 24 hours and at most eight weeks
  in the future. Tutor Overrides may schedule outside availability and horizon rules if
  the full time remains otherwise unoccupied.
- Other Students' Bookings, Blocked Time, and Slot Holds appear to a Student only as the
  absence of a Bookable Slot.
- Each Student may have at most one Upcoming Booking. The invariant is enforced in the
  same transaction that creates or reschedules a Booking.
- Selecting a slot is client state only. Schedule session opens the confirmation modal;
  it does not mutate availability or funding.
- A Student-created Booking requires exactly one funding source: First Session
  Promotion, Session Credit, or successful Stripe payment.
- First Session Promotion is a distinct one-time Credit Ledger entitlement and applies
  automatically to the earliest eligible Booking. A Student cannot pay to save it.
- Session Credit is a non-currency entitlement for one 60-minute Booking. Student credit
  balance is derived from immutable Credit Ledger entries.
- Credit Ledger records grants, deductions, redemptions, restorations, freezes, and
  forfeitures. Tutor adjustments and funding overrides require a short reason.
- Tutor may create a Complimentary Booking without payment or credit. Complimentary is
  an explicit funding kind and does not consume or create Student entitlement.
- Paid Booking uses Stripe-hosted Checkout. The server reads Session Price from Tutor
  settings and never accepts an amount from the browser.
- Starting paid Checkout creates one 30-minute Slot Hold and one Checkout Session. The
  Slot Hold blocks competing slot derivation until successful fulfillment or expiration.
- Verified Stripe webhook fulfillment is authoritative. Browser redirect may improve
  immediacy but cannot independently create a Booking.
- Webhook processing validates provider signatures, checks successful payment state,
  matches the expected Student, slot, currency, and snapshotted integer amount, and is
  idempotent under duplicate or concurrent delivery.
- Processed provider event and Checkout Session identifiers are unique. Payment details
  beyond necessary provider identifiers, amount, currency, status, and timestamps are
  not copied into application storage.
- Promotion and Session Credit Booking creation are immediate atomic transactions and
  do not create Slot Holds.
- Platform Booking state, not Stripe or a calendar file, remains authoritative for time,
  Student, funding, Meeting Details, and cancellation.
- At least 24 hours before start, Student rescheduling may repeat without a counter and
  preserves the original funding. Student cancellation restores promotion/credit or
  grants one Session Credit for an originally paid Booking.
- Inside 24 hours, Student rescheduling is disabled and the UI directs the Student to
  email the Tutor. Student cancellation remains possible only after explicit funding
  forfeiture confirmation.
- Tutor edits preserve funding by default. Tutor Override may use an otherwise-free time
  outside normal availability or horizon after warning.
- Refund Request is available only for an early canceled paid Booking whose replacement
  Session Credit exists. Creating the request freezes that exact value.
- Refund approval issues a full Stripe refund and removes the frozen credit. Decline
  restores it. Partial refunds and automatic cancellation refunds are not supported.
- Booking becomes a Past Booking by derived time after its non-canceled end. There is no
  explicit completion, attendance, or no-show state in this release.
- Calendar Export is a server-generated `.ics` snapshot. It includes the 60-minute time,
  Tutor Timezone, and current Meeting Details. It creates no synchronization authority.
- Student Dashboard has static welcome guidance above a responsive calendar/notes
  layout. Desktop uses notes left and calendar right; smaller screens stack calendar
  before notes.
- Tutor Dashboard uses searchable Student list left, weekly calendar right, and active
  Inquiry list below. Calendar selection highlights and scrolls to the Student but does
  not open the modal. Student selection opens Student Detail.
- Student Detail shows read-only name/email, funding status, the single Upcoming
  Booking, Refund Requests, Lesson Note Drafts, and Shared Lesson Notes.
- Lesson Note Draft and Shared Lesson Note are distinct visibility states. Saving does
  not publish. Explicit Publish makes the note Student-visible.
- Every Lesson Note belongs to exactly one Past Booking and inherits the fixed session
  date. It contains a required Tutor-authored title and Markdown source capped at 100 KB.
- Student rendering uses sanitized Markdown with raw HTML disabled or sanitized.
  Download returns original Markdown with a stable date/title filename.
- Confirmed delete removes Student access to the Shared Lesson Note. Attachments are not
  supported.
- Private Tutor Notes are not mixed into lesson-note history or CRUD in this release.
- Identity fields remain read-only in Tutor operations. Student/Tutor email change needs
  a separate future verified identity workflow.
- Automated Invitation email, Login Link email, Booking changes, and reminders are
  deferred. Manual email is an accepted temporary operational boundary.
- Automated calendar-provider synchronization is deferred. No Calendar Projection or
  Sync Drift model is introduced.
- Authorization remains deny-by-default. Public and role-specific responses use
  explicit allowlists; Student reads and mutations are constrained by account ownership.
- Every cookie-authenticated unsafe request requires active role session, same-origin
  Origin, and CSRF token.
- Logs retain the established allowlist and exclude emails, bodies, query strings,
  tokens, ciphertext, cookies, lesson notes, Booking Focus, Meeting Details, payment
  details, Inquiry messages, and Login Requests.
- Existing collected-pilot-data deletion behavior cannot be blindly extended to
  financial records. Retention and deletion rules for payment and Credit Ledger evidence
  must be explicit before production payment data is accepted.
- Existing architecture ADRs remain in force. Two follow-up ADRs should record encrypted
  Invitation redisplay and Stripe-webhook/Slot-Hold authority before their slices land.

## Testing Decisions

- Tests assert externally observable behavior, persisted domain outcomes, and security
  boundaries rather than private call ordering, ORM shape, React component structure,
  SQL string layout, or provider SDK internals.
- The primary seam is one Playwright critical journey using isolated migrated state and
  both application processes: Prospect submits Inquiry; Tutor creates and copies the
  Invitation Link; Invitee opens setup and creates the account; Student uses the First
  Session Promotion to confirm a Booking; Tutor sees the Booking; Tutor publishes a
  lesson note after the Booking becomes past; Student reads and downloads it.
- The Playwright journey uses the manual Login Request workflow where returning access
  is needed. It does not rely on a real mail service, Stripe network, or calendar
  provider.
- The supporting seam is black-box HTTP testing against the FastAPI application. This is
  existing repository prior art and remains the authoritative seam for authorization,
  atomicity, concurrency, expiration, idempotency, and sanitized response behavior.
- Public Inquiry tests cover required message, normalized email, 2,000-character limit,
  five-per-hashed-IP limit, separate repeat records, generic errors, safe rendering,
  anonymous inability to list, Tutor list access, archive, delete, and Invitation link.
- Invitation tests cover direct active creation, manual creation, encrypted redisplay,
  ciphertext exclusion from responses/logs, seven-day expiration, first-open evidence,
  scanner-safe GET, regeneration, revocation, terminal-state erasure, read-only email,
  minimal setup, atomic claim, duplicate email, and concurrent one-winner behavior.
- Login Request tests cover enumeration-safe public responses, email/IP limits, no token
  before Tutor action, Tutor-only queue, generation-time TTL, copy response boundaries,
  dismissal, expiry, used cleanup, role-neutral confirmation, session rotation, replay,
  role routing, and repository Tutor-link command behavior.
- Session tests preserve prior coverage for secure cookie settings, inactivity expiry,
  absolute expiry, activity extension, logout, revocation, and cross-role denial.
- Tutor settings tests cover fail-closed currency/timezone/secret validation, integer
  price storage, snapshot behavior, and non-retroactive changes.
- Availability tests cover recurrence across dates, Tutor Timezone boundaries, window
  start anchoring, partial leftover exclusion, Blocked Time, Booking and Slot Hold
  conflicts, 24-hour minimum, eight-week maximum, Tutor Overrides, and no private
  occupancy details in Student responses.
- Availability and Booking time tests use an injected or controlled clock rather than
  wall-clock sleeps.
- Booking tests cover the one-Upcoming invariant, per-Student idempotency, concurrent
  slot competition, optional Booking Focus length, remote Meeting Details, pending
  details, complimentary funding, promotion funding, credit funding, and Student/Tutor
  authorization.
- Credit Ledger tests cover automatic promotion grant, balance derivation, Tutor reason
  requirement, grants, deductions, atomic redemption, retry, restoration, freeze,
  unfreeze, forfeiture, and impossibility of negative or double-spent value.
- Cancellation and rescheduling tests cover before/at/inside the 24-hour boundary,
  unlimited early reschedules, original funding retention, paid-to-credit conversion,
  promotion/credit restoration, late forfeiture, Tutor preservation default, override
  warning contract, and conflict rejection.
- Stripe tests run through a provider boundary with deterministic fakes plus signed
  webhook fixtures. They cover server-owned amount, USD currency, 30-minute hold,
  checkout failure, abandonment, expiration, signature rejection, wrong amount or
  Student, async/delayed success if supported, duplicate events, concurrent delivery,
  one Booking, and reconciliation-safe persisted evidence.
- Refund tests cover eligibility, freezing the exact replacement credit, inability to
  spend frozen value, approval, decline, provider failure, retry, one full refund, and
  impossibility of retaining both refunded money and spendable credit.
- Calendar Export tests validate content type, stable UID, 60-minute duration, Tutor
  Timezone, escaped Meeting Details, stable filename, rescheduled values, Student
  ownership, and lack of synchronization claims.
- Lesson Note tests cover Past Booking derivation, canceled Booking rejection, draft
  privacy, explicit publication, cross-Student denial, title and 100 KB limits, safe
  Markdown rendering, raw Markdown download, stable filename, edit consistency, and
  confirmed deletion.
- Tutor Dashboard browser behavior covers search, read-only identity, calendar-to-list
  highlight and scrolling, explicit modal opening, availability modal, Inquiry list,
  Login Request queue, Refund Request review, and lesson-note publication.
- Student Dashboard browser behavior covers responsive ordering, static welcome,
  calendar selection, confirmation content, private occupancy, funding display,
  Booking details, cancellation/rescheduling warnings, `.ics` download, note accordion,
  scrollable content, and `.md` download.
- Existing liveness/readiness, error-envelope, CSP, security header, dependency, build,
  type, lint, audit, and secret-scanning checks remain part of the completion gate.
- The root test command must remain deterministic from a clean checkout, own isolated
  database migration and process lifecycle, avoid persistent data, and require no
  pre-running services or external network availability.

## Out of Scope

- Multiple Tutors, organizations, tenants, Tutor discovery, matching, or a marketplace.
- Public Student signup detached from a Tutor-created Invitation.
- Public Tutor registration or a dashboard-based Tutor-account creation flow.
- Automated email provider integration for Invitations, Login Links, Booking changes,
  reminders, or lesson-note publication.
- SMS, push notifications, or automated reminders.
- Google, Apple, GitHub, or other social login.
- Password-based authentication.
- Student or Tutor self-service email-identity changes.
- Multiple tutoring services, variable durations, packages, bundles, subscriptions,
  credit purchases, credit expiration, or a general stored-value wallet.
- Multiple simultaneous Upcoming Bookings per Student or recurring Booking series.
- Student-selected timezones or cross-timezone display conversion.
- In-person Meeting Mode, Student-proposed locations, travel buffers, mapping, or
  location validation. Exceptional in-person sessions remain manual.
- Google Calendar, Apple Calendar, Outlook, or other provider OAuth and two-way sync.
- Calendar Projection, Sync Drift detection, or external-calendar busy-time imports.
- Lesson-note attachments, general file/resource sharing, private-note UI, comments,
  collaboration, or note version history.
- Attendance, explicit completion, no-show, or partial-session states.
- Partial refunds, automatic cash refunds on cancellation, disputes, chargebacks,
  taxes, invoices, subscriptions, connected accounts, payouts, commissions, or revenue
  splitting.
- Automatic conversion of historical Session Requests into Bookings.
- Visual browser grading, deployment availability, or real third-party network services
  as repository test gates.
- Promotional reviews, testimonials, and broader landing-page marketing content.
- Architecture justified only by hypothetical future SaaS scale.

## Further Notes

- Shared understanding for this flow was confirmed on 2026-07-17 after product grilling.
- Canonical domain vocabulary is maintained in the root context glossary; this spec
  intentionally uses Tutor rather than Admin and distinguishes Invitation Link, Login
  Link, Student Session, Booking, Session Credit, and Shared Lesson Note.
- The resolved secure pilot spec remains historical evidence. This spec supersedes its
  Session Request user journey but preserves its security and test contracts.
- The implementation should follow dependency-ordered, commit-sized TDD slices rather
  than one integrated rewrite. Stripe follows a working promotion/credit Booking path,
  Refund Request follows Stripe, and Session Request removal follows proven direct
  Booking.
- The expected persistence surface includes Inquiries, Login Requests, Tutor settings,
  expanded Invitations, Availability Windows, Blocked Time, Slot Holds, Bookings,
  processed Stripe events, Credit Ledger entries, Refund Requests, and Lesson Notes.
- The hardest invariant is one atomic and auditable answer to slot availability, Booking
  funding, and value restoration/forfeiture/refund under retries and concurrency.
- Two short ADRs should precede their implementation slices: encrypted redisplay of
  Invitation Links and Stripe webhook authority with 30-minute Slot Holds.
- The highest accepted test seams are one Playwright critical journey plus black-box
  HTTP/security tests. No lower seam should be introduced unless behavior cannot be
  observed reliably through those contracts.
