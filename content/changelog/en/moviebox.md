<!--
English version of content/changelog/moviebox.md. Every version in the Chinese file must also appear here.
-->

## v0.1.68 · 2026-10-20
### New
- **Auto-update**: MovieBox now checks GitHub Releases on launch and installs new versions when you confirm it
- **Export / import settings**: move your preferences to another Mac in one click; exported files never contain API keys or network-drive credentials
- Homepage, privacy policy, security notes and changelog are now published at mackhan.github.io/MovieBox, linked from the About page
- Builds for Intel Macs in addition to Apple silicon
### Improved
- Quick scan verifies that cached files still exist, so videos restored from the Trash or added outside the app are found again
- Much faster scan when the cache hits: 300 folders / 60k records went from 1896 ms to 60 ms
- Folders that cannot be read (drive unplugged, network drive offline) keep their database entries instead of being deleted
- Network drives reconnect with exponential backoff and give up after a limit instead of retrying forever
### Fixed
- Duplicate detection missed encrypted videos whose hash fell in the 1 MB region
- Favourites leaked between videos that share the same file name
- The vault serialized encrypt/decrypt per file and recovers if it was interrupted mid-way, so files can no longer be corrupted by concurrent operations
- An unavailable drive no longer marks sibling mounts (e.g. /Volumes/NAS2) as unavailable
- Deleting a video also removes its favourite entry
- Missing Japanese translations

## v0.1.67 · 2026-09-23
### New
- **Unsorted videos are no longer dropped**: single videos that could not be grouped are collected in an “Unsorted” section with a suggested person name and the reason; add them to an existing group or create a new one in one click
- **Manual corrections are remembered**: after you rename, merge or exclude a group, the next sort keeps your changes
- Each group shows what it is based on (database, folder name, file name or faces) and how confident it is
- New “Deep sort” switch (off by default): more thorough recognition, but slower
### Improved
- If no face is found in a video the first time, more frames are sampled from a wider range and tried again
- When several frames are sampled from one video, only the person who appears most is kept, so supporting actors and passers-by no longer disturb the grouping

## v0.1.66 · 2026-09-22
### New
- **Move a whole group into a folder**: every group in the results can be moved into a subfolder named after the person in one click
### Improved
- Person names in file names are recognized more accurately, and several names in one file name are combined into one group
- When a folder contains only one person, the other videos in that folder are assigned to that person
- Stricter face merging, so different people are less often put in the same group
- Much faster sorting with many videos
- Generated folder names drop characters the system does not allow, so they can also be created on Windows
### Fixed
- No message when a batch move only partly succeeded
