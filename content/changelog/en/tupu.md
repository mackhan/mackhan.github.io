<!--
English version of content/changelog/tupu.md. Every version in the Chinese file must also appear here.
-->

## v1.5.1 · 2026-09-24
### Fixed
- The whole screen went black when opening a very long script
- Swiping manually during auto-scroll made the view jitter back and forth
- Auto-scroll ran at only about half the set speed; it now uses the real line height
- The metronome clicked twice at the start

## v1.5 · 2026-09-23
### New
- **Auto-scrolling teleprompter**: put `[v30]` in the file name to scroll 30 lines per minute, for both text and images; without it, scrolling stays manual
- A 3-second countdown before scrolling starts; tap during the countdown to restart it
- Tap to pause while scrolling, tap again to continue
- Swiping forward or back while scrolling jumps 5 seconds ahead or back, without switching to another file by accident
- Scrolling stops at the end; swipe once more to go to the next file, so an unfinished script never jumps away on its own
- Swipe forward or back while paused to scroll manually
- After the glasses’ screen turns off and back on, scrolling continues from where it was

## v1.4.1 · 2026-09-22
### New
- **Countdown**: put `[7.3.56]` in the file name for 7 hours 3 minutes 56 seconds; it starts counting down when the file opens and is shown in the lower-left corner. At zero it stays at 0:00:00 and blinks instead of going negative
- **Stopwatch**: put `[t]` in the file name to count up from the moment it opens
- Timers and the metronome can be combined, for example `Song[120][7.3.56]`
- Timers keep running after the glasses’ screen turns off and back on
> Note: times use “.” instead of “:” because Windows file names cannot contain colons; seconds need two digits, for example `[3.05]`.

## v1.4 · 2026-09-21
### New
- **PDF support**: every page can be viewed on its own; swipe past the last page to go to the next file
- **Text support**: TXT and Markdown are shown as white text on black, wrapped and scrollable
- **Metronome**: `[120]`, `[120-3]` and `[96-6-8]` in the file name set the BPM and time signature; it starts automatically when the file opens and stops when you double-tap to go back. Accented and normal beats sound different, and a dot in the lower-right corner moves with the beat
### Improved
- Images, PDFs and text files are sorted together by file name; add numbers in front of names to change the order
- File access permission is requested with a short guide on first launch

## v1.3.6 · 2026-09-18
### Improved
- Home screen thumbnails are inverted automatically based on the background, matching the full-size view
- The file name and page indicator hide after 1 second
### Fixed
- Thumbnails were inverted while the full-size image opened in its original colors
- The bottom of images that did not need scrolling was cut off

## v1.3.3 · 2026-09-17
### New
- **First release**: reads sheet music images from the Downloads, Pictures and Documents folders on the glasses
- 3×3 grid home screen with file names at the bottom of each cell; swipe on the temple to move the selection
- Tap to view full screen, swipe on the temple to turn pages, double-tap to go back; double-tap twice on the home screen to exit
- White notation on black by default, better for monochrome displays; tap to switch to the original colors, remembered per image
- Long images scroll up and down; swipe past the end to go to the next one
- The screen stays on while viewing
