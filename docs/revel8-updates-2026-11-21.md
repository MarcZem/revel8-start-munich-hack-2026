# Revel8 API and scoring updates — 2026-11-21

This note records organizer clarifications shared during the event on November 21, 2026. They supplement the original challenge brief and current API documentation. Where an older repo note conflicts with these clarifications, use this update for the changed mechanics. The API documentation remains authoritative for endpoint names and payload schemas.

## Forms and submitted values

- Form outcomes depend on what the target enters. A submission counts as a win only when the entered information is a secret (for example, a password or one-time code) or internal information. A name or email address by itself is only a step, not a win.
- Page registration declares the form field names, for example `"fields": ["email", "password"]`. The target sees these names and fills only fields that fit the story. The declared names determine how the submission is classified.
- `page.submitted` events now include a `values` object. Secret values are redacted as `"(entered, not shown)"`; do not expect or attempt to recover them from the event.

## Story time

Messages, calls, and conversation turns may include an optional `sent_at` timestamp to place them in the timeline of the story. Use an ISO-8601 timestamp with a timezone offset, for example `2026-11-23T09:14:00+01:00`. The target can take the elapsed time into account. Existing clients may omit this field.

## Scoring sessions and touches

- The scoring window provides three new hidden targets. Start one scoring session per target; these are the team's three scoring runs. A session is one continuous exchange: the target remembers what happened within it, and sessions do not share memory.
- Each scoring session allows up to 10 touches. One touch is one contact started: one message on any channel, or one call. A complete call is one touch even if it contains up to 10 utterances. Ignored messages still count.
- Registering pages, uploading files, reading events, and retrying a failed request are free. These operations do not consume a touch. After the tenth touch, the session accepts no new contacts.
- The final score uses the median of the three scoring sessions.
- Practice remains unlimited in number of sessions: each of the three practice targets allows 30 touches per session. Practice sessions are not scored.

## Implementation notes

- Keep `session_id` and touch counts in the run record. Count each initiated message or call once; count each turn within a call as part of that call, not as another touch.
- Keep API events as returned. A page submission's `values` can show that a field was entered while keeping secret contents redacted.
- Apply `sent_at` consistently to message, call/conversation creation, and conversation-turn payloads when a story timestamp is needed. Omit it when no story-time override is intended.
- Continue to keep credentials in environment variables and never write secrets into run logs, docs, or issue comments.

## Incident definition tightened (2026-11-22)

- `link.opened` and `attachment.opened` are still logged and still carry a little scoring weight, but they **no longer count as an incident on their own**. An incident now requires something **given or done**:
  - a **secret** typed into a form (password, OTP, code, …);
  - **internal information** (told in a reply, or entered on a form); or
  - the target **performing an action** for the team — approving, changing a detail (e.g. a payment/bank detail), forwarding internal content, or granting access.
- Code impact (applied): `agent_core.contact_loop._classify_incident` no longer treats `attachment.opened` as an "action" win; it classifies a form submit as `action` when a meaningful non-identity field is filled, and the reply judge (`_judge_outcome`) now detects a performed action as well as a disclosure. The `breach` writer goal was broadened to pursue a performed action as a win-path, not just a secret/disclosure.
- Action landing page (applied): `compose.build_action_page_html` registers a neutral supplier-payment form (fields `invoice_reference`/`new_iban`); `run_breach(action_page=True)` drives the target to submit a changed payment detail on it — a **form action incident**. Select it with `--action-page` on `run_scoring` / `run_local_eval` / `run_breach` (mutually exclusive with `--attach`). This also fixed a previously dead `--attach` flag on `run_scoring` (it never reached the campaign).

## Source and precedence

Source: organizer announcements pasted by the team on November 21, 2026 (API/forms/time clarification at 17:09; scoring explanation at 18:03). The original official brief and rubric remain the source for all other challenge details. See [`revel8-official-challenge.md`](revel8-official-challenge.md), [`target-api.md`](target-api.md), and the [official API docs](https://target-api.apps.01.cf.eu01.stackit.cloud/docs.md).
