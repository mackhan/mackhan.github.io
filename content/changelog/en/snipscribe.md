<!--
English version of content/changelog/snipscribe.md. Every version in the Chinese file must also appear here.
-->

## v1.0.63 · 2026-07-07
### Fixed
- On some Macs (especially Intel models), pressing ⌘⌥C after copying a system screenshot said “no image in the clipboard”. Several image formats are now tried in turn

## v1.0.62 · 2026-06-23
### Improved
- The interface language follows the system (English on English systems, Chinese on Chinese systems); you can also switch it in Settings → Preferences → Interface language

## v1.0.61 · 2026-06-18
### Improved
- The purchase status follows the record on this Mac, and purchases are no longer restored automatically at launch; use “Restore Purchase” on the About page when needed

## v1.0.60 · 2026-06-15
### Improved
- While Apple is still processing a payment, the app says “Waiting for Apple — no need to buy again” to avoid duplicate orders
### Fixed
- A misleading red error when an account that already purchased clicked Buy again

## v1.0.59 · 2026-06-14
### Fixed
- The license status shown on the General and About pages did not match for paid users; both now show “Pro · Unlimited”

## v1.0.57 · 2026-06-13
### Improved
- **Every feature is available in the free version**: 10 recognitions per day, reset at midnight; a one-time purchase (¥8 / $2.99) only removes the daily limit — no subscription, no ads
- Previous buyers are recognized automatically after reinstalling
- Smaller download and faster launch

## v1.0.52 · 2026-06-04
### Improved
- The app is now called **SnipScribe**; the menu bar, About page, window titles and notifications all use the new name

## v1.0.50 · 2026-05-28
### Improved
- ⌘⇧V brings back one-step “Snip to text”: with no image in the clipboard, the system screenshot tool opens, and the selected area is recognized and copied right away — press ⌘V to paste
- Pressing Esc to cancel a screenshot no longer shows a “failed” message
- The hotkey is now named “Snip to text”

## v1.0.46 · 2026-05-22
### Improved
- The preview after recognition shows 60 characters instead of 20, in a wider box, so long passages are no longer cut off

## v1.0.45 · 2026-05-21
### Improved
- When automatic pasting fails, you are always told the first 3 times instead of nothing happening

## v1.0.38 · 2026-05-13
### Fixed
- The first hotkey paste after a screenshot put nothing into the target app; it took a second press
- ⌘⌥V (paste without formatting) did nothing after the Settings window had been opened

## v1.0.32 · 2026-05-08
### Improved
- **Intel Mac support**: now a universal app that installs on both Apple silicon and Intel Macs
### Fixed
- The global hotkey stopped working in some cases

## v1.0.28 · 2026-05-07
### Improved
- Permission prompts are now a gentle amber banner that stays readable in dark mode
- Permission names match the ones in System Settings (“Input Monitoring”)
### Fixed
- After a fresh install the global hotkey did nothing at all, and the app was missing from the Input Monitoring list in System Settings
- Permissions only took effect after restarting the app; they are now retried automatically
- The hotkey list stayed in Chinese in the English interface

## v1.0.22 · 2026-05-02
### Fixed
- After a successful purchase the app had to be restarted to unlock; it now takes effect immediately

## v1.0.20 · 2026-05-01
### New
- **Free + one-time purchase**: 10 free recognitions per day, reset at local midnight
- Settings shows “X / 10 left today” and the time until the next reset
### Fixed
- The remaining count in Settings did not refresh after a recognition

## v1.0.12 · 2026-04-28
### Improved
- The tray menu items Settings / Quit follow the interface language
### Fixed
- Permission prompts kept appearing after permissions were granted

## v1.0.7 · 2026-04-24
### Improved
- The whole interface, including permission prompts, is available in Chinese and English

## v1.0.6 · 2026-04-23
### Improved
- When launch at login cannot be set, the actual reason is shown

## v1.0.1 · 2026-04-22
### New
- **1.0 release**: lives in the menu bar; press a hotkey, select part of the screen, and Apple’s on-device recognition puts the text straight into the clipboard — fully offline
- Launch at login
- Light / dark / system theme
