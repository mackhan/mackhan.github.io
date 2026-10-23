<!--
English version of content/changelog/promptledger.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
-->

## v0.6.15 · 2026-10-23

> Note: this is the first release recorded here; earlier versions had no user-facing notes.

### New
- Two shapes, switchable in Settings: **menu bar** (shows how much of this month's quota you've used, falling back to "turns today · tokens today" when the quota can't be read) and **notch panel** (per-project live status — who is generating, just used or still open, what was asked last; click to jump straight to that Agent / IDE)
- Turns and tokens for today and this week: total processed, new input, output, plus a 7-day bar chart
- Duplicate-question alerts: asking the same thing twice gets flagged
- A weekly report generated automatically; unassigned sessions can be pinned to a project with one click, and stay classified after that
- The mobile app is a web app (/pa/) showing the same data once paired

### Improved
- Feedback, sharing and copy-link now share one implementation, so all three behave the same
