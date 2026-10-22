<!--
English version of content/changelog/lifetree.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
Generated from the in-app changelog with tools/import_changelog.py --lang en, then edited.
-->

## v1.3.0 · 2026-10-21

### New
- Move and water reminders: set the interval, timing and active hours; reminders at the same time are merged. Defaults: move at :45 every hour, water at 1 h 45 min every 2 hours
- Smart move reminder: walk 250 steps in the hour and the reminder moves to the next hour; Check-in shows this hour's steps live
- Water log: default goal 1700 ml a day (1500 ml for women) per the Chinese Dietary Guidelines, with a pack reward on goal days; stored on this device only
- Dynamic Island & Lock Screen Live Activity: today's check-ins, water and next reminder, with +1 glass right there; can be turned off in Reminders
- Focus filters: pause move / water reminders automatically during meetings or sleep
- Streak repair: fix yesterday the day after a miss — one free repair a month, then it costs packs
- Weekly, monthly and yearly reports: check-ins, dimensions, packs, water and stand-ups, with history and sharing
- New challenges "14 Days Without Long Sitting" and "21 Days of Enough Water", each linked to its reminder

### Improved
- Act right from the notification: +1 glass (200 ml) or +1 bottle (500 ml) for water, "I stood up" for move, or remind me in 15 minutes
- Every check-in, challenge, achievement and water log now gets the same little-tree feedback animation
- Meal check-ins can take a photo or choose one from the library; the meal form now puts today's checklist first
- Pull to refresh Health data; one-tap check-ins can be updated with new data, while manual or edited ones are never changed

## v1.2.0 · 2026-10-20

### New
- New Home / Lock Screen widgets, plus a Control Center "Quick check-in" button on iOS 18+
- Check-in reminders: master switch, alarm or notification, sound, message and rest days; defaults 8:00 / 12:00 / 18:00 / 22:00
- iCloud sync for nickname, packs, challenges and notes across your devices; health data stays on this device

### Improved
- The app now opens on Check-in; tap a done card to review or edit it — packs are recalculated
- Check-in cards show what you logged, with a small "From Health" tag; one-tap completion lists the data it used
- The feed shows each check-in in full (meal photos and nutrition included), grouped by day; all multi-user content removed
- Long-press the app icon for quick check-ins, generated from today's open items and active challenges
- "About" merged into Me → Support & updates alongside feedback; added a Health data read/write guide

### Fixed
- Fixed dimension score bars all appearing full

## v1.1.0 · 2026-10-20

### New
- Added "Share with friends", "Check for updates" and "What's new"

### Improved
- The changelog now opens once after each update (never on a fresh install)
- "Community" became a private "Feed": likes, reporting and groups removed; built-in content no longer invents other users
- The feed holds only your own notes and built-in content — no social interaction at all

## v1.0.0 · 2026-10-19

### Improved
- Quiz expanded to 50 questions, split by dimension; scores normalised to a 0–100 health score
- "Tree lifespan" fully decoupled from any person's lifespan
- HealthKit sync: resting HR, HRV, steps, flights and food logs, with one-tap check-in
- Meal photos plus an on-device food library that computes calories, protein, fat and carbs
- Research rewritten as 2-minute reads with the conclusion up top and full citations
- Check-ins can auto-post to your feed (disable in Me)

## v1.0 · 2026-10-16

### New
- **Health ArborType**: four dimensions — sleep R/P, diet N/J, activity A/I, stress C/T. A 16-question survey places you in one of 16 tree types, with suggestions for that type
- **Tree lifespan**: set only by the tree type baseline, your four dimension scores and nutrient packs — never by age, gender, region, genes, smoking or drinking; the algorithm page explains it
- **The life tree**: each tree type looks different; four branches map to the four dimensions, foliage density follows your scores and the last 7 days of check-ins, achievements appear as fruit. Tap foliage for details, long-press the trunk for the algorithm
- **Four-dimension check-in**: once per dimension per day, earning nutrient packs, with a bonus for the focus dimension; plus special challenges and a 7-day chart
- **Community**: posts prioritised by the same tree type, likes and reports, on-device content review; research updates; interest groups (no leaderboards)
- **Profile**: profile, four-dimension score chart, achievements, nutrient pack history, mental health hotline, erase all data
- **Fully local and offline**: health data never leaves the device — no network, no upload
- **Bilingual**: Chinese / English, switchable under Profile → Language
