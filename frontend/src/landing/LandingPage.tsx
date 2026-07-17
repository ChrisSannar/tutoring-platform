import { InquiryModal } from "./InquiryModal";

export function LandingPage() {
  return (
    <main>
      <section className="hero" aria-labelledby="hero-heading">
        <p className="eyebrow">One-to-one learning</p>
        <h1 id="hero-heading">Personal tutoring, thoughtfully planned.</h1>
        <p className="intro">
          Focused sessions shaped around your goals, your questions, and the way
          you learn best.
        </p>
        <InquiryModal />
      </section>
    </main>
  );
}
