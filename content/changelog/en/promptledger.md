<!--
English version of content/changelog/promptledger.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
Sourced from the English half of each release note in mackhan/promptledger-releases.
-->

## v0.6.16 · 2026-10-23

### Improved
- **The desktop pet (bubbles) is on by default** — it is the quickest way to see who is working right now, and shipping it off meant nobody ever saw it. Launch at login is registered on the first start too (and left alone once you have changed it yourself).
- **Collection hooks install themselves**: each start checks whether any are missing and installs them. On Windows this cannot be written while a client holds its own config file — a Windows limitation, not a failure — so the next start tries again; whenever that agent happens to be closed, it gets hooked automatically. All three can still be turned off in Settings.
- **Projects open in CodeBuddy are recognised now** (KVMini, for instance). The cause: the Windows build of CodeBuddy CN keeps **no conversation text locally** (it lives in the cloud; the local folders are empty) and its logs carry no workspace path, so only WorkBuddy ever showed up and CodeBuddy looked closed. It now reads the VS Code-family "recently opened workspaces" list (the same file on Windows and macOS), only while the app is actually running, and reports it as idle.
- **The tray icon is redrawn**: an amber speech bubble with three ascending bars. Windows used to show a shrunken copy of the app icon, which turned to mush at 16px; the geometry is now drawn for small sizes (snapped to a 2px grid) and reads on both dark and light taskbars. The macOS monochrome template was updated to match.

## v0.6.15 · 2026-10-23

### Improved
- **A way out when the mail client will not open.** Instead of just saying it failed, a "copy the address" button appears next to the message, so you can paste it into webmail and send from there.

## v0.6.14 · 2026-10-23

### Improved
- **The quota source switches only cover Cursor, Claude Code, Codex, Copilot and Gemini** — not the Tencent quota, which reads the company dashboard's own login and is this tool's primary quota anyway. Settings has always said "other sources"; the comments now say the same.

## v0.6.13 · 2026-10-23

### Improved
- **The three manuals are now maintained by you, in the conversation.** When a new session gets the project manuals, it also asks you to record what was decided, added or left undone once there is progress or before the session ends. A scheduled job used to open a separate session to write them — once a day, so always behind, and it cost an extra model budget. The session doing the work is the one that should write them down.
- The rules come along too: what something is comes from the code; why, and what is unfinished, comes from this conversation, and nothing is written without a source. Create a manual if it is missing, edit only the relevant entries, no need to rewrite the whole file. Projects with their own documentation rules (AGENTS.md, memory-bank and the like) are left to those rules.
- It can be turned off in Settings → Collection ("Let the AI maintain the manuals itself"); off means the manuals are read-only reference again.

## v0.6.12 · 2026-10-23

### Improved
- **Please install this Windows release by hand.** The update signing key is now shared by both platforms. The copy you already have trusts the old key, so it will reject every update from here on — it shows up as "updating never finishes". Install this one manually and automatic updates work again; there is nothing you need to do after that.
- Why share one key: each platform used to sign its own builds, while the version number is shared (the manifest holds a single version). That meant every release had to be built and signed on both machines, and if one side skipped a release it quietly stayed behind. With one key, the Windows installer can be signed on the Mac — the installer is just a file, signing does not need Windows — so that machine only has to build it.

## v0.6.11 · 2026-10-23

### Improved
- **Quota sources can be turned off.** Reading Cursor, Claude Code, Codex, Copilot and Gemini means sending this machine's credentials to them (Cursor's session cookie, Claude/Codex OAuth tokens, a GitHub PAT) every two minutes — and there was no way to stop it. Settings → Quota now has a master switch and one per source: off means nothing is read and no credential file is even touched.
- Also fixed: switching a source off and back on no longer inherits the failures it had piled up — switching it back on retries right away.

## v0.6.10 · 2026-10-23

### Improved
- **A test now guards it.** The Cargo version and the `pl` version must match, and the built-in changelog must carry an entry for the current version. Both used to rely on someone remembering; this release is what happens when one of them is forgotten.

## v0.6.9 · 2026-10-23

### Improved
- **Quota is no longer a single number.** The panel used to show one "monthly quota" — the internal spending pool. Cursor, Claude Code, Codex, Copilot and Gemini each have their own quota, and they are not even in the same unit: money, request counts, or time-window percentages like "5-hour / 7-day". Each now gets its own card drawn its own way: money reads "¥used / ¥total", request counts read "150 / 500", and time windows get one bar each with its own reset time.
- **Only what can actually be read is listed.** A source appears when the tool is installed and signed in, and disappears entirely otherwise — no empty card taking up space. These endpoints are internal and undocumented, so a failure to read one can never affect the rest of the panel.
- **The menu bar still shows one line**, picked money-first and falling back otherwise: the spending pool when it is available, and another source — named — when it is not (for example "Claude Code: 61% used").
- **Copilot needs a PAT once.** Its own OAuth token cannot read the billing API; a fine-grained PAT with Plan read permission is required. Fill it in under Settings → Quota; leave it empty and the card simply does not appear.
- **Gemini is an estimate.** Google exposes no public quota endpoint, so it counts today's local sessions and tokens. The card is labelled an estimate and no denominator is invented — the account tier is unknown, so writing "1000/day" would be making it up.

## v0.6.8 · 2026-10-23

### Improved
- **CodeBuddy sessions now have an identifier**: on Windows that field was always empty. It looked like a missing column, but it actually made "Assign to project" and "Hide session" unusable for CodeBuddy — an empty identifier is rejected, so clicking either only produced "invalid session identifier". The identifier now comes from the request id in the log (one per question, shared by the steps of that question).
- **Project naming revisited**: a project really can be called `a`, but single-letter directory names were being discarded as a drive letter; conversely, UUID-shaped directories (the kind Cursor creates) were being shown as project names. Both fixed.
- **Tests added on the collection side**: how a project name is derived, how the macOS and Windows log formats are recognized, whether usage is attributed to the new project after a window switch, whether duplicate lines are de-duplicated. None of this had a single test, and everything one review pass turned up lived in exactly this area.

## v0.6.7 · 2026-10-22

### Improved
- **Windows finally has data**: the collector looked for CodeBuddy usage logs at the macOS path (`CodeBuddyExtension/Logs/...`), which does not exist on Windows, so the CodeBuddy section was always empty and the panel looked broken. It now reads the real Windows location (CodeBuddy CN `logs/<launch>/window1/exthost/*.log`) and projects resolve properly — projects like KVMini show up for the first time.
- **Active sessions count too**: a session file used to wait until it had been idle for 30 minutes before being parsed, so the session you were actually using always read 0 for today. It now parses whatever is already written, re-reading at most once a minute.
- **Project names are no longer a full path**: from a workspace directory like `c-Users-nierhan-WorkBuddy-<project>` only the meaningful tail is kept (timestamps and session ids are skipped); when there is none it falls back to WorkBuddy instead of showing the whole path in the project list.
- **CodeBuddy workspace tracking**: switching windows/projects in the log re-attributes later usage to the new project; previously the whole log landed on the first workspace.

## v0.6.6 · 2026-10-22

### Improved
- One reader per agent: WorkBuddy reads the tail of its transcript, CodeBuddy reads its own index.json (whether the current request is running or complete). Only one format used to be understood, so CodeBuddy always fell back to file timestamps — a still-running sub-agent looked finished.
- "Waiting for your approval" no longer shows as grey: an unfinished turn stays "generating". If the transcript says running but nothing was written for two minutes it reads "generating · quiet" — either waiting for your click, or a long command is running.
- The completion chime is stricter: only generating → waiting rings it. Idle, stuck or app-quit no longer count.
- The desktop pet's hover label is multi-line: project name up to two lines, state and agent on one. It used to be one non-wrapping line with an ellipsis, so long names collapsed to "…".
- Status wording and ordering are one table shared by all three windows.

## v0.6.5 · 2026-10-22

### Improved
- Fixed a long-standing language bug: the SDK never asked for the system language on init (its default is English), so the changelog, share text and feedback template were always English even on a Chinese system. It follows the system now, and Settings → General → Language lets you pick follow-system / 中文 / English.
- Theme: light / dark / follow system in Settings → Appearance, applied immediately. In follow mode it tracks the system live.
- Feedback is now written in the app first: type, hit Send, and your mail client opens with the text already in the body. Before, one click opened an empty compose window with a placeholder, which looked like a test email.
- "Privacy Policy" now points at an actual policy page. The data-boundary note (what leaves the machine) stays in the Phone section — they are not the same thing.
- Settings layout fixed: the back button and the group title used to sit on top of each other. Segmented controls, buttons and fields now share one interaction style: subtle press scale, consistent focus ring, and a readable selected state in dark mode.
- Jump logic is one module now, shared by the desk pet, the notch panel and the project cards (double clicks count once, failures say something useful).
- **First Windows release**: lives in the tray — hover for today's turns and tokens, click to open the panel (Today / This week / Projects / Settings), right-click for refresh, reports, version and quit. No admin rights needed; shortcuts on the desktop and in the Start menu.
- About the update signing key: it was rotated (the old one was unavailable on this Windows machine; the new public key is compiled in). This Mac build was signed before the rotation, so your current Mac install still auto-updates to it — no manual install needed. The rotation only bites from the next Mac build onwards: installs predating it will need one manual install then. Fresh Windows installs are unaffected.

## v0.6.4 · 2026-10-22

### Improved
- "Done" now means done: WorkBuddy also sends notifications while it is still working, and those were counted as "the AI stopped", so the app showed finished while tools were still running. State is now read from the last record in the session transcript — still thinking or calling a tool means "working"; only an actual reply counts as "waiting for you". Bonus: a three-minute command no longer drops out of "working" halfway.
- Clicking a project in the desk pet or the notch now switches to that exact conversation inside WorkBuddy (it keeps several tasks as separate spaces in one window; before, only the app was brought forward).
- Mobile: today / this week / this month / this year, and when several computers work on one project, tap the card to see each machine's own numbers.
- "Sync now" now reports a clear result: which repo and branch on success, and what to do next on failure.
- Fixed a nasty bug: running `pl install` after it was already installed overwrote `pl` with an empty file (reading and writing the same path truncates it first), after which every command exited silently. It now recognises itself and does nothing.

## v0.6.3 · 2026-10-22

### Improved
- The desk pet now shows agents that are running but idle: an open CodeBuddy that has not touched a project for 30 minutes gets one sleeping pet (one slot per agent, so it never floods the row).

## v0.6.2 · 2026-10-22

### Improved
- Agent-colored bubbles: each pet's bubble now uses its agent's color as the background, so a column of agents is identifiable by color at a glance (dango, tanghulu, keychain, tower, and avatar stacks).
- Overview gained a code row: total lines plus lines added today, this week, and this month, next to the token numbers. The range switch also has a new "This month" option.

## v0.6.1 · 2026-10-22

### Improved
- Pairing no longer requires scanning: the link is shown under the QR code, copy it and open it on your phone
- New "rotate key" action: invalidate the old key if the QR code ever leaks, and push a fresh bundle right away
- The phone section now spells out what a public repo exposes: metadata only (machine model, sync time, payload size); prompt content stays encrypted

## v0.6.0 · 2026-10-21

### Improved
- Quota countdown: days until reset, when it will run out at this rate, and how many dry days that leaves. Reset day defaults to the 1st and is editable
- MCP: `pl mcp serve` lets AI clients read your own archive (search prompts, usage, project manuals) — read-only, no network
- Phone: search your prompt history, quota countdown, instant sync on state changes, and pairing no longer needs a read-only token
- Settings redesigned into 6 collapsible groups with a search box at the top
- Export CSV / JSON to Downloads; data-boundary page and an offline self-check button

## v0.5.2 · 2026-10-21

### Improved
- The notch panel now animates open and closed: the window grows smoothly, corners follow, content fades in just after the frame, rows stagger in
- Collapsing fades the content out first and then retracts the window, instead of snapping shut
- When the list has more rows below, the bottom edge fades instead of cutting a row in half

## v0.5.1 · 2026-10-21

### Improved
- Auto-update: checks on launch and every 4 hours; manual check, skip this version and remind later in Settings
- Fixed: hovering the notch panel or the desktop pet did nothing until you clicked once
- The desktop pet's hover label moved to the bottom so it no longer covers the pet
