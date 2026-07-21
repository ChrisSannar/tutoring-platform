import { useState } from "react";

import "./style-prototype.css";

type Variant = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

type StylePrototypeProps = {
  variant: number;
};

const schedule = [
  { time: "9:00", period: "AM", student: "Maya Chen", focus: "Calculus · Related rates" },
  { time: "11:30", period: "AM", student: "Noah Williams", focus: "Physics · Momentum" },
  { time: "3:00", period: "PM", student: "Sofia Patel", focus: "Algebra II · Polynomials" },
];

const students = [
  { name: "Maya Chen", detail: "Today, 9:00 AM", mark: "MC" },
  { name: "Noah Williams", detail: "Today, 11:30 AM", mark: "NW" },
  { name: "Sofia Patel", detail: "Today, 3:00 PM", mark: "SP" },
  { name: "Eli Thompson", detail: "Thu, 4:30 PM", mark: "ET" },
];

const requests = [
  { kind: "New inquiry", name: "Jordan Lee", age: "18 min" },
  { kind: "Login request", name: "Amara Brooks", age: "1 hr" },
  { kind: "Refund request", name: "Leo Martin", age: "Yesterday" },
];

const variantNames = [
  "Quiet Editorial",
  "Tutor Control Room",
  "Learning Studio",
  "Swiss Planner",
  "Night Observatory",
  "Lunar Console",
  "Signal Timeline",
  "Mission Ledger",
  "Eclipse Command",
  "Constellation Grid",
];

function Navigator({ variant, theme, onThemeChange }: { variant: Variant; theme?: "light" | "dark"; onThemeChange?: () => void }) {
  const first = variant > 5 ? 6 : 1;
  const last = variant > 5 ? 10 : 5;
  const previous = variant === first ? last : variant - 1;
  const next = variant === last ? first : variant + 1;

  return (
    <nav className="prototype-nav" aria-label="Style prototypes">
      <a href={`/style-prototype/${previous}`} aria-label={`Previous prototype: ${variantNames[previous - 1]}`}>←</a>
      <div>
        <span>{variant - first + 1} / 5 · Round {first === 1 ? 1 : 2}</span>
        <strong>{variantNames[variant - 1]}</strong>
      </div>
      <a href={`/style-prototype/${next}`} aria-label={`Next prototype: ${variantNames[next - 1]}`}>→</a>
      <div className="prototype-dots" aria-label="Choose a prototype">
        {variantNames.slice(first - 1, last).map((name, index) => (
          <a
            key={name}
            href={`/style-prototype/${index + first}`}
            aria-label={name}
            aria-current={variant === index + first ? "page" : undefined}
          />
        ))}
      </div>
      {theme && <button className="prototype-theme" type="button" onClick={onThemeChange} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
        {theme === "dark" ? "☼" : "◐"}
      </button>}
    </nav>
  );
}

function QuietEditorial() {
  return (
    <main className="prototype prototype-editorial">
      <header className="editorial-header">
        <a className="editorial-brand" href="/style-prototype/1">Arden <i>Learning</i></a>
        <p>Monday, July 20</p>
        <span className="editorial-avatar">AR</span>
      </header>

      <section className="editorial-lead">
        <p className="prototype-kicker">Tutor workspace · Daily briefing</p>
        <h1>Good morning,<br />Alexandra.</h1>
        <p className="editorial-deck">Three thoughtful conversations await you today. Here is the shape of your Monday.</p>
      </section>

      <section className="editorial-day">
        <div className="editorial-heading">
          <p>Today</p>
          <h2>Your sessions</h2>
        </div>
        <div className="editorial-sessions">
          {schedule.map((session, index) => (
            <article key={session.student}>
              <time><strong>{session.time}</strong> {session.period}</time>
              <div>
                <p>0{index + 1}</p>
                <h3>{session.student}</h3>
                <span>{session.focus}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="editorial-lower">
        <div>
          <p className="prototype-kicker">A note for the day</p>
          <blockquote>“The art of teaching is the art of assisting discovery.”</blockquote>
          <p>— Mark Van Doren</p>
        </div>
        <div className="editorial-requests">
          <span>Needs your attention</span>
          <strong>3</strong>
          <p>Two new messages and one refund request are waiting.</p>
          <a href="#requests">Review requests →</a>
        </div>
      </section>

      <a className="editorial-action" href="#plan">Plan the week <span>→</span></a>
    </main>
  );
}

function ControlRoom() {
  return (
    <main className="prototype prototype-control">
      <aside className="control-sidebar">
        <div className="control-logo">A<span>/</span>R</div>
        <nav aria-label="Workspace">
          <a className="active" href="#overview"><b>01</b> Overview</a>
          <a href="#calendar"><b>02</b> Calendar</a>
          <a href="#students"><b>03</b> Students</a>
          <a href="#requests"><b>04</b> Requests <i>3</i></a>
          <a href="#settings"><b>05</b> Settings</a>
        </nav>
        <div className="control-profile"><span>AR</span><p>Alexandra Reed<small>Tutor · CST</small></p></div>
      </aside>

      <section className="control-main">
        <header><div><span>Workspace / Overview</span><h1>MON · 20 JUL</h1></div><button type="button">+ PLAN SESSION</button></header>
        <div className="control-stats">
          <div><span>Sessions today</span><strong>03</strong><small>5.0 hrs teaching</small></div>
          <div><span>Active students</span><strong>12</strong><small>+2 this month</small></div>
          <div><span>Open requests</span><strong>03</strong><small>Oldest: 1 day</small></div>
          <div><span>Week booked</span><strong>78%</strong><small>14 of 18 slots</small></div>
        </div>
        <div className="control-grid">
          <section className="control-schedule">
            <div className="control-title"><h2>Today’s schedule</h2><span>Central Time</span></div>
            <div className="control-hours">
              {["08", "09", "10", "11", "12", "13", "14", "15", "16"].map((hour) => <span key={hour}>{hour}:00</span>)}
              <article className="slot slot-one"><b>09:00</b><strong>Maya Chen</strong><small>Calculus · Related rates</small></article>
              <article className="slot slot-two"><b>11:30</b><strong>Noah Williams</strong><small>Physics · Momentum</small></article>
              <article className="slot slot-three"><b>15:00</b><strong>Sofia Patel</strong><small>Algebra II · Polynomials</small></article>
            </div>
          </section>
          <section className="control-queue">
            <div className="control-title"><h2>Request queue</h2><span>3 open</span></div>
            {requests.map((request) => <article key={request.name}><i /> <div><b>{request.kind}</b><strong>{request.name}</strong></div><time>{request.age}</time></article>)}
            <a href="#all">VIEW ALL REQUESTS →</a>
          </section>
        </div>
        <section className="control-table">
          <div className="control-title"><h2>Students</h2><span>Last activity</span></div>
          {students.map((student, index) => <div key={student.name}><span>{student.mark}</span><strong>{student.name}</strong><small>{["Calculus", "Physics", "Algebra II", "Geometry"][index]}</small><time>{student.detail}</time><b>•••</b></div>)}
        </section>
      </section>
    </main>
  );
}

function LearningStudio() {
  return (
    <main className="prototype prototype-studio">
      <header className="studio-header">
        <a href="/style-prototype/3" className="studio-brand"><span>al</span> Arden Learning</a>
        <nav><a className="active" href="#home">Home</a><a href="#students">Students</a><a href="#calendar">Calendar</a></nav>
        <div className="studio-person"><span>3</span><b>AR</b></div>
      </header>
      <section className="studio-welcome">
        <div><span className="studio-spark">✦</span><p>Monday, July 20</p><h1>Ready for a bright day,<br />Alexandra?</h1></div>
        <button type="button">Plan a session <span>↗</span></button>
      </section>
      <section className="studio-grid">
        <article className="studio-today">
          <div className="studio-title"><div><span>01</span><h2>Today</h2></div><p>3 sessions · 5 hours</p></div>
          {schedule.map((session, index) => <div className="studio-session" key={session.student}><time>{session.time}<small>{session.period}</small></time><span className={`studio-dot dot-${index + 1}`} /><div><strong>{session.student}</strong><p>{session.focus}</p></div><b>→</b></div>)}
        </article>
        <article className="studio-students">
          <div className="studio-title"><div><span>02</span><h2>Your crew</h2></div><a href="#all">See all</a></div>
          <div className="studio-faces">
            {students.map((student, index) => <div key={student.name}><span className={`face-${index + 1}`}>{student.mark}</span><strong>{student.name.split(" ")[0]}</strong></div>)}
            <button type="button">+</button>
          </div>
          <p>12 active students are learning with you.</p>
        </article>
        <article className="studio-request-card">
          <span>03</span><div><p>Things that need you</p><strong>3 requests</strong><small>One has been waiting since yesterday.</small></div><a href="#requests">Take a look →</a>
        </article>
        <article className="studio-note">
          <span>THIS WEEK</span><strong>14</strong><p>sessions on the books</p><div><i /><i /><i /><i /><i /></div>
        </article>
      </section>
    </main>
  );
}

function SwissPlanner() {
  return (
    <main className="prototype prototype-swiss">
      <header className="swiss-header">
        <a href="/style-prototype/4">ARDEN<br />LEARNING</a>
        <nav><a className="active" href="#today">TODAY</a><a href="#students">STUDENTS</a><a href="#requests">REQUESTS <sup>3</sup></a></nav>
        <span>AR</span>
      </header>
      <section className="swiss-date">
        <p>WEEK 30 / 2026</p><h1>MONDAY<br /><em>20.07</em></h1><div><span>CENTRAL TIME</span><b>08:42</b></div>
      </section>
      <section className="swiss-agenda">
        <header><h2>TODAY’S<br />AGENDA</h2><div><b>03</b><span>SESSIONS<br />SCHEDULED</span></div></header>
        {schedule.map((session, index) => <article key={session.student}><span>0{index + 1}</span><time>{session.time} {session.period}</time><div><h3>{session.student.toUpperCase()}</h3><p>{session.focus.toUpperCase()}</p></div><a href="#session">↗</a></article>)}
      </section>
      <section className="swiss-bottom">
        <div className="swiss-action"><p>NEXT MOVE</p><h2>SHAPE<br />THE WEEK.</h2><a href="#plan">PLAN SESSIONS <span>→</span></a></div>
        <div className="swiss-roster"><header><h2>STUDENTS</h2><a href="#all">ALL 12 ↗</a></header>{students.slice(0, 3).map((student, index) => <div key={student.name}><span>0{index + 1}</span><strong>{student.name.toUpperCase()}</strong><small>{student.detail.toUpperCase()}</small></div>)}</div>
        <div className="swiss-inbox"><span>INBOX</span><strong>03</strong><p>OPEN REQUESTS<br />NEED A RESPONSE</p><a href="#requests">REVIEW ↗</a></div>
      </section>
    </main>
  );
}

function NightObservatory() {
  return (
    <main className="prototype prototype-night">
      <div className="night-glow" />
      <header className="night-header">
        <a href="/style-prototype/5"><i /> ARDEN</a>
        <nav><a className="active" href="#orbit">Orbit</a><a href="#students">Students</a><a href="#signals">Signals <sup>3</sup></a></nav>
        <span className="night-avatar">AR</span>
      </header>
      <section className="night-intro"><p>MONDAY · JULY 20 · 08:42 CST</p><h1>Your day is<br />in alignment.</h1><span>3 SESSIONS · 5 HOURS OF FOCUS</span></section>
      <section className="night-timeline">
        <div className="night-line" />
        {schedule.map((session, index) => <article key={session.student} className={`night-event event-${index + 1}`}><time>{session.time}<small>{session.period}</small></time><i /><div><span>0{index + 1}</span><strong>{session.student}</strong><p>{session.focus}</p></div></article>)}
        <div className="night-now"><i /><span>NOW</span></div>
      </section>
      <section className="night-panels">
        <article className="night-students"><header><span>STUDENT CONSTELLATION</span><a href="#all">VIEW ALL →</a></header><div>{students.map((student, index) => <span className={`night-student ns-${index + 1}`} key={student.name}><i>{student.mark}</i><b>{student.name}</b></span>)}</div></article>
        <article className="night-signals"><header><span>INCOMING SIGNALS</span><b>03</b></header>{requests.map((request) => <div key={request.name}><i /><span><strong>{request.kind}</strong><small>{request.name} · {request.age}</small></span><b>→</b></div>)}</article>
        <article className="night-plan"><span>NEXT HORIZON</span><h2>Make space<br />for discovery.</h2><a href="#plan">Plan the week <b>↗</b></a></article>
      </section>
    </main>
  );
}

function LunarConsole() {
  return (
    <main className="prototype next-prototype lunar-console">
      <aside className="next-rail">
        <a className="next-mark" href="/style-prototype/6">A<span>●</span>R</a>
        <nav aria-label="Workspace"><a className="active" href="#today">Today</a><a href="#calendar">Calendar</a><a href="#students">Students</a><a href="#requests">Requests <b>3</b></a></nav>
        <span className="next-avatar">AR</span>
      </aside>
      <section className="lunar-main">
        <header className="next-header"><div><span>MONDAY · JUL 20</span><h1>Good morning, Alexandra.</h1></div><button type="button">+ Plan session</button></header>
        <section className="lunar-now"><div><span>NOW · 08:42 CST</span><h2>Your teaching day<br />is ready.</h2></div><div className="lunar-orbit"><i /><b>3</b><span>sessions<br />in orbit</span></div></section>
        <section className="lunar-agenda"><header><h2>Today’s trajectory</h2><span>08:00 — 17:00</span></header><div className="lunar-track">{schedule.map((session, index) => <article key={session.student} className={`lunar-stop stop-${index + 1}`}><i /><time>{session.time} {session.period}</time><strong>{session.student}</strong><small>{session.focus}</small></article>)}</div></section>
        <section className="lunar-bottom"><article><header><h2>Incoming</h2><b>03</b></header>{requests.map((request) => <div key={request.name}><i /><span><strong>{request.kind}</strong><small>{request.name}</small></span><time>{request.age}</time></div>)}</article><article className="lunar-capacity"><span>WEEK CAPACITY</span><strong>78%</strong><div><i /></div><small>14 of 18 sessions booked</small></article></section>
      </section>
    </main>
  );
}

function SignalTimeline() {
  return (
    <main className="prototype next-prototype signal-timeline">
      <header className="signal-header"><a href="/style-prototype/7">ARDEN / CONTROL</a><nav><a className="active" href="#today">Today</a><a href="#roster">Roster</a><a href="#signals">Signals <b>03</b></a></nav><span>AR</span></header>
      <section className="signal-summary"><div><p>MON / 20 JUL / 2026</p><h1>Three sessions.<br />One clear trajectory.</h1></div><button type="button">PLAN THE WEEK ↗</button></section>
      <section className="signal-band"><header><span>DAILY SIGNAL</span><b>LIVE · CST</b></header><div className="signal-hours">{["08", "09", "10", "11", "12", "13", "14", "15", "16", "17"].map(hour => <span key={hour}>{hour}:00</span>)}</div><div className="signal-line" />{schedule.map((session, index) => <article className={`signal-event signal-${index + 1}`} key={session.student}><i /><span>0{index + 1}</span><strong>{session.student}</strong><small>{session.focus}</small></article>)}</section>
      <section className="signal-lower"><article className="signal-next"><span>NEXT UP · 09:00</span><strong>Maya Chen</strong><p>Calculus · Related rates</p><a href="#prepare">OPEN SESSION NOTES →</a></article><article className="signal-roster"><header><h2>Students in range</h2><a href="#all">ALL 12 ↗</a></header>{students.map(student => <div key={student.name}><span>{student.mark}</span><strong>{student.name}</strong><time>{student.detail}</time></div>)}</article><article className="signal-inbox"><header><h2>Signals</h2><b>03</b></header>{requests.map(request => <div key={request.name}><i /><span><strong>{request.kind}</strong><small>{request.name} · {request.age}</small></span></div>)}</article></section>
    </main>
  );
}

function MissionLedger() {
  return (
    <main className="prototype next-prototype mission-ledger">
      <aside className="ledger-sidebar"><a href="/style-prototype/8">AR_</a><div><span>WORKSPACE</span><strong>MON 20 JUL</strong><small>08:42:16 CST</small></div><nav><a className="active" href="#overview">OVERVIEW <b>01</b></a><a href="#schedule">SCHEDULE <b>02</b></a><a href="#students">STUDENTS <b>12</b></a><a href="#requests">REQUESTS <b>03</b></a></nav><p>SYSTEM<br /><b>ALL CLEAR</b></p></aside>
      <section className="ledger-main"><header><div><span>TUTOR OPERATIONS / DAILY LEDGER</span><h1>MONDAY<br />CONTROL LOG</h1></div><button type="button">NEW SESSION +</button></header><div className="ledger-stats"><div><span>TEACHING HOURS</span><b>05.0</b></div><div><span>SESSIONS</span><b>03</b></div><div><span>OPEN CAPACITY</span><b>22%</b></div><div><span>REQUESTS</span><b>03</b></div></div>
        <section className="ledger-table"><header><span>TIME</span><span>STUDENT / SUBJECT</span><span>STATUS</span><span>ACTION</span></header>{schedule.map((session, index) => <article key={session.student}><time>{session.time} {session.period}</time><div><strong>{session.student}</strong><small>{session.focus}</small></div><span><i />{index === 0 ? "READY" : "SCHEDULED"}</span><a href="#open">OPEN ↗</a></article>)}</section>
        <section className="ledger-bottom"><article><header><h2>STUDENT INDEX</h2><a href="#students">VIEW ALL</a></header>{students.map((student, index) => <div key={student.name}><b>{String(index + 1).padStart(2, "0")}</b><span>{student.mark}</span><strong>{student.name}</strong><small>{student.detail}</small></div>)}</article><article><header><h2>REQUEST LOG</h2><b>03 OPEN</b></header>{requests.map((request, index) => <div key={request.name}><b>R-{120 + index}</b><span><strong>{request.kind}</strong><small>{request.name}</small></span><time>{request.age}</time></div>)}</article></section>
      </section>
    </main>
  );
}

function EclipseCommand() {
  return (
    <main className="prototype next-prototype eclipse-command">
      <header className="eclipse-header"><a href="/style-prototype/9"><i />ARDEN</a><nav><a className="active" href="#command">Command</a><a href="#students">Students</a><a href="#requests">Requests <b>3</b></a></nav><button type="button">+ PLAN</button></header>
      <section className="eclipse-hero"><div className="eclipse-copy"><span>MONDAY · 20 JULY</span><h1>Keep today<br />in focus.</h1><p>Three sessions are aligned. Your first begins in 18 minutes.</p></div><div className="eclipse-dial"><div><span>NEXT SESSION</span><strong>00:18</strong><small>MAYA CHEN · CALCULUS</small></div>{schedule.map((_, index) => <i key={index} className={`eclipse-node node-${index + 1}`} />)}</div></section>
      <section className="eclipse-board"><article className="eclipse-agenda"><header><h2>Today / 03</h2><span>CST</span></header>{schedule.map((session, index) => <div key={session.student}><b>0{index + 1}</b><time>{session.time}<small>{session.period}</small></time><span><strong>{session.student}</strong><small>{session.focus}</small></span><i>↗</i></div>)}</article><article className="eclipse-students"><header><h2>Student field</h2><a href="#all">12 ACTIVE ↗</a></header><div>{students.map((student, index) => <span key={student.name} className={`eclipse-person person-${index + 1}`}><i>{student.mark}</i><b>{student.name}</b></span>)}</div></article><article className="eclipse-requests"><header><span>INCOMING</span><b>03</b></header>{requests.map(request => <div key={request.name}><i /><span><strong>{request.kind}</strong><small>{request.name} · {request.age}</small></span></div>)}<a href="#requests">REVIEW QUEUE →</a></article></section>
    </main>
  );
}

function ConstellationGrid() {
  return (
    <main className="prototype next-prototype constellation-grid">
      <header className="grid-header"><a href="/style-prototype/10">ARDEN<span>✦</span>OPS</a><div><span>MON 20 JUL</span><b>08:42 CST</b></div><button type="button">+ PLAN SESSION</button><span className="next-avatar">AR</span></header>
      <section className="grid-title"><div><p>TUTOR CONTROL ROOM</p><h1>Today, at a glance.</h1></div><span>3 sessions · 12 students · 3 requests</span></section>
      <section className="constellation-board"><article className="grid-agenda"><header><h2>Today’s orbit</h2><a href="#calendar">CALENDAR ↗</a></header>{schedule.map((session, index) => <div key={session.student}><time>{session.time}<small>{session.period}</small></time><i className={`grid-dot grid-dot-${index + 1}`} /><span><strong>{session.student}</strong><small>{session.focus}</small></span><b>0{index + 1}</b></div>)}</article><article className="grid-focus"><span>NEXT SESSION</span><strong>09:00</strong><h2>Maya Chen</h2><p>Calculus · Related rates</p><button type="button">OPEN NOTES ↗</button></article><article className="grid-capacity"><span>WEEK LOAD</span><strong>78<small>%</small></strong><div><i /></div><p>4 open slots remain</p></article><article className="grid-roster"><header><h2>Students</h2><a href="#students">ALL 12</a></header><div>{students.map(student => <span key={student.name}><i>{student.mark}</i><b>{student.name.split(" ")[0]}</b></span>)}</div></article><article className="grid-requests"><header><h2>Request queue</h2><b>03</b></header>{requests.map(request => <div key={request.name}><i /><span><strong>{request.kind}</strong><small>{request.name} · {request.age}</small></span><b>→</b></div>)}</article><article className="grid-action"><span>NEXT HORIZON</span><h2>Shape the rest<br />of your week.</h2><a href="#plan">PLAN THE WEEK <b>↗</b></a></article></section>
    </main>
  );
}

export function StylePrototype({ variant }: StylePrototypeProps) {
  const selected = variant as Variant;
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const concepts = [<QuietEditorial />, <ControlRoom />, <LearningStudio />, <SwissPlanner />, <NightObservatory />, <LunarConsole />, <SignalTimeline />, <MissionLedger />, <EclipseCommand />, <ConstellationGrid />];

  return (
    <div className={`style-prototype style-prototype-${selected}${selected > 5 ? ` next-theme-${theme}` : ""}`}>
      {concepts[selected - 1]}
      <Navigator variant={selected} theme={selected > 5 ? theme : undefined} onThemeChange={() => setTheme(current => current === "dark" ? "light" : "dark")} />
    </div>
  );
}
