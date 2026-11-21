# How social-engineering messages get recognized (writer guidance)

Research note for issue #17. Source for the writer system prompt in
`agent_core/writer_prompt.py`. Simulation-only: this is about making the
*attacker twin's* copy realistic so the defender twins are trained against
current-quality lures, not toy spam.

## Key shift (2026)

Grammar and spelling are **no longer** reliable tells — LLMs produce flawless
copy in any language (CISA, Huntress). Detection has moved to behaviour,
context, and writing *fingerprint*. So the writer must not lean on polish; it
must avoid the signals below.

## Tells to avoid in the message text

1. **Artificial urgency / pressure / threats.** "within 24 hours", "account
   will be closed", "immediate action required". Core phishing signal.
2. **Secrecy / process-skip pressure.** "handle this quietly", "don't loop in
   compliance", "keep this between us". Designed to isolate from verification —
   defenders are trained on exactly this.
3. **Generic / contextless greeting.** "Dear Customer", "Dear Sir/Madam", or an
   opener with no real, specific reason for contact. Real senders have context;
   use the researched hook instead.
4. **Direct request for secrets.** passwords, MFA/OTP codes, full payment or
   bank data in the message body. Legitimate orgs don't ask this way; it's an
   instant flag (and out of scope for the sim's rules).
5. **AI-writing fingerprint** (stylometry + Mimecast word-frequency work):
   - stock openers: "I hope this message finds you well"
   - LLM-favoured words: "delve", "intricacies", "navigate the landscape",
     "tapestry", "testament to"
   - forced triads ("faster, cleaner, and more reliable"), em-dash pile-ups,
     over-polished uniform tone, over-structured bullet lists where a human
     would write two plain sentences.
6. **Over-formality / voice mismatch.** Tone that doesn't match the claimed
   sender or channel (a Slack ping written like a legal letter).

## What to do instead

- Open with a concrete, researched reason for contact (the angle's evidence).
- One natural, low-friction next step that fits the channel; no deadline unless
  a real one plausibly exists.
- Vary sentence length; let it read like one person typed it quickly.
- Keep the ask proportionate to the relationship implied by the evidence.

## Caveat

Fixed phrase lists decay as models change (Mimecast). Treat the word list as a
starting filter, not a guarantee; re-check against new model output.

## Sources

- Abnormal AI, *Phishing email red flags* (2026)
- Huntress, *How to spot a phishing email*
- Keepnet Labs, *How to spot phishing emails* (Nov 2026)
- Mimecast, *AI-generated messages* (stylistic markers, "delves" frequency)
- Opara, Modesti, Golightly, *Stylometric detection of GPT-4 phishing*,
  Expert Systems with Applications
- Eze & Shamir, *Analysis and prevention of AI-based phishing email attacks*,
  arXiv:2405.05435
