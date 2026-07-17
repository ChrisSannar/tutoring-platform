# Product boundaries

## Required direct-Booking slice

`Inquiry -> Invitation -> Create Account -> funded Booking -> Tutor operation -> Shared Lesson Note`

The application is for one Tutor, not a marketplace. Access is invite-only. The server
owns identity, availability, funding, Booking state, payment/refund evidence, and note
publication. Student-visible occupancy never reveals another Student or private Tutor
calendar detail.

## External-service boundary

- Email and Invitation/Login Link delivery remain manual.
- Calendar integration is a downloadable `.ics` snapshot.
- Stripe hosts card entry; verified signed webhooks, not redirects, create paid Bookings.
- Tests replace Stripe with deterministic fakes and require no external network.

## Historical pilot boundary

Session Request was the original pilot scheduling proposal. It is superseded and is not
a product concept or API. Migration `20260717_0017` explicitly discards its disposable
rows without inferring payment or confirmation.
