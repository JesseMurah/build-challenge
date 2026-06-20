# Context

AI-powered Telegram bot for operational excellence (72-hour build challenge).
Core loop: **Information → Intelligence → Action** — capture Entries, classify and
summarize them into Insights and a daily Digest, and surface recommended next steps.

## Language

**Team**:
A single Telegram group chat the bot belongs to. The unit of tenancy: Entries are
submitted in the group, and the Digest is delivered back to that same group. One
group chat = one Team.
_Avoid_: Organization, Workspace, Group, Channel

**Sender**:
The team member who submitted an Entry — first-class, since the Digest attributes
items to who reported them.
_Avoid_: User, Author, Reporter, Member

**Entry**:
A candidate Update, submitted by a Sender in a Team, that the classifier judged
operational — a voice note, text message, or document. Stored for the Digest.
Carries three classified attributes: Modality, Category, and Priority.
_Avoid_: Update, Message, Item, Note, Submission

**Candidate**:
Any group Update (text, voice, or document) before classification. The classifier
either promotes it to an Entry or judges it noise. Noise candidates are discarded,
never persisted.
_Avoid_: Pending, Raw message

**Modality**:
The form an Entry arrived in — voice, text, or document. Mechanical; read
directly from the Telegram Update, no AI involved.
_Avoid_: Type, Format, Kind

**Content**:
The canonical text of an Entry that all classification and summarization operate
on, regardless of Modality: the message text (text), the **Transcription** (voice),
or the **Extraction** (document). Category, Priority, Insights, and the Digest all
derive from Content, never from the raw audio or original file.
_Avoid_: Body, Text, Payload, Transcript (use "Transcription" only for the voice→text step)

**Category**:
The operational kind of a Candidate, AI-assigned — the interesting classification
axis, and also the noise gate. One of:
- **request** — someone needs another person to *do* something
- **issue** — a problem, blocker, incident, or risk
- **decision** — a decision made, or one that's needed
- **update** — status / progress / FYI, no action needed
- **question** — an open question awaiting an answer
- **noise** — not operational (chatter, reactions); the Candidate is discarded,
  never promoted to an Entry
_Avoid_: Type, Class, Label

**Priority**:
How soon a human needs to act on an Entry, AI-assigned. Time-anchored and ordered,
independent of Category. One of:
- **now** — needs attention today; someone is blocked or it's time-sensitive
- **today** — should be handled within the day, not drop-everything urgent
- **whenever** — no time pressure; informational or backlog
_Avoid_: Urgency, Severity, Importance, High/Medium/Low

**Insight**:
An AI-generated summary, recommendation, or observation derived from one or more
stored Entries.
_Avoid_: Result, Output, Finding

**Digest**:
A scheduled roll-up of the Entries from a time window (default: the last day),
summarized and prioritized, delivered to the team on a cadence. Distinct from an
Insight by its time window, cadence, and delivery. One Digest per team (delivered
to the group chat), not per person.
_Avoid_: Summary, Report, Roundup, Briefing

**Action**:
A recommended next step surfaced inside an Insight or Digest (e.g. "reply to
Sarah's incident report today") — text, not execution. Closes the loop
*informationally*, not operationally. Triggered/automated operations are out of
scope.
_Avoid_: Task, Command

> "Update" is reserved for the raw Telegram Bot API event (message, callback
> query, etc.) — a framework term, not a domain term. Not every Update is an
> Entry (a button tap or `/start` is an Update but not an Entry).

> Use these exact terms in issue titles, hypotheses, and test names. If a concept
> isn't here yet, that's a signal to add it — don't drift to synonyms.
