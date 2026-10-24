<!--
English version of content/changelog/lifetree.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
Generated from the in-app changelog with tools/import_changelog.py --lang en, then edited.
-->

## v1.8.0 · 2026-10-24

### New

- Every check-in now follows an explicit rule: meet it and you earn packs; miss it and it's still logged, with a note on exactly what fell short. All four rules, with their sources, are listed under Me → Check-in rules
- The meal checklist is far more granular: vegetables split into dark leafy greens, red/orange/purple, fresh beans & fruiting veg, mushrooms & seaweed, and roots & aquatic; fruit into citrus, pome, berries, stone fruit and tropical & melon — plus four habits that don't count as servings

### Improved

- Meals are counted in servings: 3 of vegetables plus 2 of fruit to count (1 serving ≈ 100 g), with a live "current / target" badge on each group that turns green when you're there. Juice doesn't count as fruit
- Sleeping longer than 9 hours no longer fails the rule: the consensus is that the risk above 9 hours is uncertain, so you still earn packs and simply get a note
- High stress still counts if you actually did a relaxation practice (meditation, breathing, a walk). The rule exists to stop "tap and earn", not to punish honest logging
- Activity is weighted by intensity: light ×0.5, vigorous ×2, and short bouts add up — since 2020 the WHO no longer requires bouts of 10 minutes
- Sources are in the app: sleep from the AASM/SRS 2015 consensus and the US National Sleep Foundation 2015 range, diet from the Chinese Dietary Guidelines (2022), activity from the WHO 2020 guidelines
- The tree's packs are stated in seconds throughout, and the explainer no longer uses "lifespan" as a positive claim. Birthday is required at setup and locked afterwards — changing it means deleting your profile and starting over
- Challenges that can be judged objectively now mark themselves done, but only when you actually met them; ones we can't judge keep a manual button rather than pretending

## v1.7.0 · 2026-10-23

### New
- New "Share my anonymous progress with groups" switch: turn it off and we stop uploading and delete the row you already sent; leaving a group deletes it too

### Improved
- You can now see other members' anonymous progress inside a group: just a random code (like a3f1) and three numbers — whether they logged today, their streak, and how long they've been in. No names, no photos, no way to write text or post images, and no Health data at all
- Tap ⋯ next to a code to report it (pick a preset reason) or hide it. Hidden codes can be restored with one tap, and our contact address sits at the bottom of the page
- When you set your birthday during setup, the line under the date shows "counting from this date, your tree has been growing for N years", so the default date can't quietly take effect
- Dish recognition: the same ingredient no longer appears twice (mushroom and squash used to show up as two separate candidates), and a failed model copy no longer breaks recognition
- Permission prompts now show English text in English; the widget got its own privacy manifest

### Fixed
- Fixed: after upgrading from 1.6.0, the Live Activity on the Lock Screen / Dynamic Island could get stuck and stop updating
- Fixed: the "add your birthday" prompt could be pushed aside by the changelog and never appear, and dismissing it by swiping made it come back every time. Now it shows on every launch until you fill in your birthday

## v1.6.1 · 2026-10-23

### Improved
- Dish recognition finally works: an on-device model (MobileNetV2, 6 MB) ships with the app. Photos are recognized on your phone and never leave it — point at ingredients and it names bananas, broccoli, corn, bread and more; you still set the portion
- Eight recognizable ingredients joined the food library: cauliflower, bell pepper, mushroom, zucchini, potato, lemon, strawberry and pineapple
- Refreshing Apple Health, applying Health data with one tap, and submitting or editing a check-in all return you to the tree now (only some paths did before, and they often didn't move at all)
- Voice check-in starts recording as soon as it opens — no tap needed. The Finish button moved to the bottom of the screen where one thumb reaches it
- The voice check-in card moved to the bottom of the check-in page, right above the tab bar. The mic button next to the reminders bell in the top-right corner is gone
- Birthday is now required: remaining packs = total packs − years lived, counted from your birthday. If you joined earlier without one, the tree asks for it once

## v1.6.0 · 2026-10-23

### New
- Habit groups: quit smoking, drink less, cut sugar, sleep earlier, daily steps, drink enough, daily calm, regular meals — join one and tap "done" each day
- Four new studies: irregular sleep and biological age, ultra-processed food, the payoff from quitting smoking, and 2–6 strength sessions a week — all with full citations

### Improved
- Groups are yours alone: no posting, no other people, no likes or follows — just a goal for yourself and a count of how long you've kept it
- Reach 7 / 30 / 100 days and a new fruit appears on your tree — fruit already grows through bud, young and ripe stages
- Research articles now update remotely: new studies no longer wait for a release, and you keep the last copy when offline
- Research expanded to 51 articles covering sleep, diet, exercise, stress, cardiovascular and metabolic health, each with its journal and full citation
- Research now rotates daily: a fresh batch each day with unseen articles first, and read ones resurface later. A counter shows how many you haven't seen, and you can expand the full list

## v1.5.0 · 2026-10-23

### New
- Added an optional birthday: the remaining-pack countdown starts from it and drops by one day's worth each day (1 day = 86,400 packs) — check-ins add it back

### Improved
- "Remaining = total packs − time elapsed": no longer identical to the total; it recalculates at midnight and whenever you return to the app
- Dropped the "tree age" wording in favour of "time elapsed"; it's gone from your profile too
- Fruit now has three stages: a bud when unlocked, a young fruit after a day, a ripe fruit after seven — each with its own size and colour
- Submitting a check-in takes you straight to the tree: the pack count animates up and the fruit swells
- Voice check-in has its own card at the top of Check-in — no more hunting for the small mic in the corner

## v1.4.0 · 2026-10-22

### New
- Voice check-in: tap the mic in Check-in, say how your day went, and your iPhone turns it into text on-device to pre-fill the form — you confirm before anything is saved
- Added an on-device meal photo recognition hook: with a bundled model, a photo suggests candidates and you set the portion (no model is bundled in this version, so the entry stays hidden)

### Improved
- Recognition runs entirely on your phone; audio and text are never uploaded. Results are only a draft and are never written automatically
- One sentence mentioning several dimensions opens a form for each, one at a time; water gets its own confirmation

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
