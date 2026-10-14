<!--
English version of content/changelog/moviebox.md. Every version in the Chinese file must also appear here.
-->

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
