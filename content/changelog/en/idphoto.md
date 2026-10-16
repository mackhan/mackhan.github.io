<!--
English version of content/changelog/idphoto.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
-->

## v0.1.0 · 2026-09-02
### New
- **Specs for 16 countries**: adding a country means adding one config entry — no code changes
- **High-quality cutout**: MODNet as the main model (hair-level in testing), with macOS Vision person segmentation and face detection as two fallbacks
- **Compliance check**: size, DPI and head-ratio are checked against each country's official spec, with a clear note on what is off
- **Print layout**: automatic tiling on 6-inch photo paper and A4
- Export uses the native system save dialog
- **Fully local**: photos never leave the Mac — no network, no upload
- **Bilingual**: every string goes through i18n (Chinese / English)
### Fixed
- Freezes and memory leaks when processing several photos in a row
