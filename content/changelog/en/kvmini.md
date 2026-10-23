<!--
English version of content/changelog/kvmini.md. Every version in the Chinese file must also appear here
(the build fails otherwise). Keep the same versions and dates; newest first.
-->

## v0.4.10 · 2026-10-23

### Improved

- An incomplete certificate or private key now fails immediately instead of being loaded as a corrupt one — it used to surface as a handshake failure or a fingerprint mismatch, pointing at the wrong cause

### Fixed

- Fixed minimizing on macOS still not collapsing to the tray (the 0.4.9 fix never actually worked: the check ran outside the main-thread task and always read the initial value; both the check and the hide now run on the main thread)
- Fixed two edge cases when pressing Ctrl+Space on a Windows keyboard to switch input source: holding Space no longer switches repeatedly, and releasing Ctrl before Space no longer leaves a stuck Command on the Mac
- Fixed "synced" being reported and the edge detector being rebuilt when saving the peer's layout actually failed: the direction that really made it to disk is now used
- Fixed "Restart" (on the permission guide) leaving the other computer under remote control when clicked while sharing: control is now handed back and local input restored before restarting
- Fixed files dropped across screens often not being transferred: the "what is being dragged" lookup happened after the cursor had been pinned back inside the screen, and once the cursor leaves the screen edge the system stops telling us what is being dragged — we now ask proactively at the moment of crossing

## v0.4.9 · 2026-10-23

### New

- New "Ctrl+Space switches input source" setting (on by default): pressing Ctrl+Space on a Windows keyboard now reaches the Mac as Control+Space (switches input source) instead of being remapped to Cmd+Space (Spotlight). Other combos such as Ctrl+C still arrive as Cmd+C

### Improved

- On macOS, minimizing now collapses to the tray and shows the desktop bubble, and clicking the Dock icon brings the main window back

### Fixed

- Fixed the controlled PC's keyboard going completely dead with dual-keyboard control: it was forwarded to the peer and swallowed locally, but the controlled side never sends frames and the controlling side never injects them, so neither computer received anything. The keyboard now really follows the cursor — both keyboards type on whichever computer the cursor is on
- Fixed the screen-crossing direction not following a layout change: the edge detector is rebuilt immediately after saving, and layouts synced from the peer are mirrored before being stored
- Fixed the layout preview never showing the other computer's monitors: the monitor list is now synced on connect and when monitors are plugged in or removed
- Fixed a single click on the desktop bubble not opening the main window: macOS system dragging is modal and swallows the mouse-up, so dragging now only starts after the pointer really moves
- Fixed the hover panel flickering while dragging the desktop bubble
- Fixed occasional huge latency readings and the "stall, then reconnect" pattern: ping, pong and heartbeat no longer queue behind mouse and keyboard frames, so the latency number no longer includes queueing time
- Fixed modifier mapping changes in Settings only taking effect after restarting the app
- Fixed Caps Lock getting stuck when using a Mac keyboard on Windows (everything typed in caps, and pressing it again did not turn it off): macOS treats Caps Lock as a held key while Windows toggles on a full press-and-release, so each state change is now turned into a complete press-and-release on the Windows side

## v0.4.8 · 2026-10-23

### Improved

- "Dual-keyboard control" is now really on by default: existing configs that still hold the old default (off) and were never changed by you are migrated to on; settings you turned off yourself are left alone
- Minimizing the main window now also hides it to the tray and shows the desktop bubble, same as closing it (bring it back from the tray icon, the tray menu, or a single click on the bubble)
- Desktop bubble is smaller and stands out more: the ball shrinks from 64 to 52, with a deeper shadow and a white outline
- A single click on the bubble opens the main window (double click no longer needed; dragging is unchanged)

### Fixed

- Fix: hovering the bubble flickered — it kept expanding and collapsing while the cursor sat on it
- Fix: opening the main window from the bubble marked the bubble as "hidden by you", so it never came back on later

## v0.4.7 · 2026-10-22

### New

- New tray item "Show Desktop Bubble": the way to bring the bubble back after hiding it (a hidden bubble has no menu of its own)

### Improved

- While hidden, the bubble stops asking for status every 2 seconds and no longer stacks up pending requests

### Fixed

- Fixed: after picking an item in the bubble's right-click menu, the bubble stayed at the menu's size instead of shrinking back to the ball
- Fixed: hiding the bubble from its menu is no longer undone the next time you close the main window — your choice is remembered

## v0.4.6 · 2026-10-22

### New

- Desktop bubble: when you hide the main window, a small ball stays on the desktop with a ring that shows the current latency in colour, so you can see at a glance whether you are connected and who is in control. Hover for details, drag it anywhere, right-click for its menu

### Improved

- Closing the main window now hides it to the tray instead of quitting (use Quit in the tray menu to actually exit)
- Mouse and keyboard come first: file transfers and clipboard sync use their own channel and no longer block the mouse; when the network degrades, transfers slow down to leave room for input
- Performance: smoother mouse movement, and logging no longer slows down input

## v0.4.5 · 2026-10-21

### New

- Anonymous usage statistics: only events like "connected", "switched", "which feature was used" and "where it failed" are counted, to decide what to fix first. Turn it off anytime in Settings

### Improved

- No IP, hostname, file name or path, clipboard content, keystrokes or screen content is collected; "Reset Anonymous ID" unlinks later records from earlier ones
- The privacy policy now spells out what is collected, in both Chinese and English

## v0.4.4 · 2026-10-20

### New

- New "Dual-keyboard control" switch (off by default): when on, both keyboards type on whichever computer the cursor is on; when off, typing on the controlled computer brings the cursor back to it. Both computers share the setting

### Fixed

- System shortcuts such as screenshots no longer run on the Mac while it controls the other computer
- After a screenshot on the Mac, pasting on Windows no longer gets overwritten by Windows' old clipboard or lands on the wrong computer
- Dragging files from a Mac to the other computer no longer quits KVMini
- Clicking your own mouse while being controlled takes control back (Windows now behaves like the Mac)
- An internal error no longer closes the app: it is logged and you are notified

## v0.4.3 · 2026-10-16

### Fixed

- Dragging files from a Mac to the other computer did nothing
- Dragging files from Windows worked only sometimes: the cursor crossed the edge before the files were read
- Releasing the mouse before the dragged files were read left the other computer holding files it never dropped
- A leftover cursor stayed at the edge of the Mac screen while it controlled the other computer
- After a screenshot tool moved the cursor on the controlled computer, the next mouse move jumped it back

## v0.4.2 · 2026-10-15

### New

- Dragging files from the other computer onto a Mac now follows the cursor and drops where you release

### Fixed

- During a cross-screen drag the source computer also dropped the files at its own cursor (on the same disk they could be moved)
- After a drag was interrupted — disconnect, cancel, or moving back to your own screen — the drag stayed stuck to the cursor on the other computer
- Files received during a drag were dropped along with it
- Dropping into a folder with the same name also dragged away the files already in it
- Dragging the same file twice in quick succession could corrupt the received file

## v0.4.1 · 2026-10-14

### New

- Native cross-screen drag and drop on Mac: drag a file from Finder past the screen edge and it lands on the other computer where you release it

### Fixed

- Dragging a folder dropped only one of its files: the whole folder is now dropped once every file has arrived
- After a cancelled or failed drag the other computer kept waiting for files (and could mistake later transfers for the drag)
- Releasing before the transfer finished made your next click act as the drop; the files now stay in the receive folder
- Dragging files onto Windows was cancelled before you released the mouse
- Dragging text or a window across screens could send the files from your previous drag

## v0.4.0 · 2026-10-14

### Fixed

- On Windows the trial period was reset on every restart

## v0.3.4 · 2026-10-14
### New
- **Drag files across screens (Windows)**: drag a file from File Explorer past the screen edge and it is sent to the other computer and dropped where you release the mouse — no more copy-then-paste
### Fixed
- After an update on Windows, the other computer could stay stuck in the controlled state (control was not returned before installing)

## v0.3.3 · 2026-10-11
### Improved
- The Mac installer is notarized by Apple and opens directly after downloading
- Update dialog layout: buttons stay at the bottom and only the release notes scroll when they are long
### Fixed
- “Check for updates” in Settings showed nothing when already up to date or when the check failed

## v0.3.2 · 2026-10-10
### New
- **Automatic updates**: a dialog shows the release notes and download progress when a new version is available; the signature is verified before installing. You can “Skip this version” or “Remind me tomorrow”
- Installer for Intel Macs
### Improved
- Before restarting to finish an update, control is returned and the local keyboard and mouse are restored, so the other computer never gets stuck
### Fixed
- Version comparison bug: 0.3.10 was treated as older than 0.3.9, so the update was never detected

## v0.3.1 · 2026-10-10
### New
- **Encrypted transport**: keyboard, mouse, clipboard and files are all encrypted with TLS 1.2 / 1.3, and encryption cannot be turned off
- **Fingerprint check on first connection**: both computers show each other’s certificate fingerprint; after confirming they match, click “Trust and connect” and the device is trusted from then on
### Improved
- After copying several files, crossing screens or copy-to-send now sends all of them (previously only the first)
- When sending a folder or several files, “Cancel” cancels the rest of the batch
- The receive folder can be picked with the system folder chooser, and is checked to be writable
### Fixed
- Possible “sticky keys” after encryption was added
> Note: from 0.3.1 on, KVMini only connects to 0.3.1 or later (older versions are not encrypted). Please update both computers.

## v0.3.0 · 2026-10-09
### New
- **Folders and multiple files**: drag a whole folder or several files into the window; they are queued and sent one by one, with “file N of M” progress
- **Resumable transfers**: after a network drop, a cancel or a restart on the other side, sending the same file again continues where it stopped
- **Custom receive folder**: Settings → General → Receive folder (empty = the system Downloads folder)
- **Automatic reconnect**: retries after 1, 2, 4 … seconds (up to 30 seconds) and shows the retry count; no automatic reconnect after you disconnect manually
### Improved
- On Windows, older apps such as Paint and Office can paste images sent from the Mac
- Web content pasted into plain-text places such as a terminal becomes plain text instead of nothing; formatting is kept between Notes, WordPad and Word
- After plugging in or removing a display, or waking from sleep, the screen layout refreshes automatically
- Tray menu in Chinese and English
- Accurate message when changing the listening port fails (no more false “restored”)
- Devices running outdated versions can no longer connect, avoiding hard-to-diagnose random disconnects
### Fixed
- Two KVMini icons in the menu bar, or the icon shown as a white square
> Note: transport in this version is not yet encrypted; everything is encrypted from 0.3.1 on.

## v0.2.7 · 2026-09-30
### New
- **Mouse side buttons**: buttons 4 and 5 are passed through as-is by default, so custom mappings in Logitech Options, BetterTouchTool and similar tools keep working; you can switch to “Back / Forward”
- **Images in the clipboard**: take a screenshot and paste it on the other computer (up to 8 MB)
- **Rich text in the clipboard**: content copied from web pages and documents keeps its formatting
- **Copy to send files**: copy a file on one computer and it is sent to the other computer’s download folder; copy a file and then move the mouse across, and the file follows. Can be turned off in Settings → General
- Connection history entries can be deleted one by one
### Improved
- The text sync limit can be adjusted in Settings → General (default 10 MB); larger content is not synced at all rather than cut off
- The network interface chosen in Settings is now actually used (previously all interfaces were listened on)
- A new listening port takes effect immediately without restarting; on failure the previous setting is restored with the reason
- The connection status follows the real handshake result instead of first showing “connected” and then failing
- On a connection timeout, a hint says the other computer’s IP may have changed
- Light scrolling on a Mac trackpad now works when controlling Windows
### Fixed
- The mouse wheel did nothing when controlling a Mac from Windows
- The browser Back / Forward keys on the keyboard did nothing when controlling a Mac from Windows (now converted to ⌘[ / ⌘])
- The [ and ] keys were swapped when typing across devices

## v0.2.3 · 2026-09-29
### New
- **Modifier key mapping**: choose whether the Windows key maps to Option or Command on the Mac (by default Ctrl maps to Command, so ⌘C copies)
### Improved
- The “Connect” button at the top is smarter: it prefers the IP you entered, then the most recent device
- Long texts in Settings no longer overflow and reflow when the window gets narrow
### Fixed
- A leftover cursor at the screen edge on the Mac while controlling the other computer

## v0.2.2 · 2026-09-28
### Improved
- Manual connections follow the real result, and success and failure are shown in the same place
- Errors always show a message with a suggestion
### Fixed
- With Windows in control, touching the screen edge disconnected
- No message when the Windows global hotkey was taken by another program
- Keys occasionally stuck on the controlled side, leaving the target app in a pressed state

## v0.1.63 · 2026-05-21
### Fixed
- Unstable cross-device scrolling on Apple silicon Macs
- Control occasionally bouncing back and forth when switching
- Double-clicks across devices sometimes recognized as two single clicks
- Windows still showing “connected” after the Mac disconnected

## v0.1.61 · 2026-05-19
### Fixed
- The scroll wheel stopped working when controlling Windows from a Mac

## v0.1.60 · 2026-05-14
### New
- **Automatic layout sync**: the two computers exchange display information when connecting and align the layout
### Fixed
- Keyboard and mouse could stay locked after the controlled Windows process was killed
- The wheel could not scroll windows when controlling a Mac from Windows

## v0.1.57 · 2026-05-11
### New
- **Emergency release hotkey**: press Ctrl+Alt+S (Control+Option+S on a Mac) at any time to take back keyboard and mouse control immediately
### Fixed
- The controlled side could not take control back with its own keyboard and mouse
- The local keyboard and mouse were not blocked while being controlled, so both computers reacted
- After dragging a window from the Mac to Windows and releasing, the window was still being dragged
- ⌘⇧4 screenshots did not work while the Mac was being controlled

## v0.1.44 · 2026-05-09
### New
- **Move to take control back**: when someone moves the mouse or presses a key on the controlled computer, control returns to it immediately and the other side sees a notice
### Fixed
- Keyboard and mouse locked after the controlled side disconnected

## v0.1.42 · 2026-05-08
### New
- Mouse side buttons on Windows
- Windows detects administrator rights and shows a hint (needed to control windows running as administrator)
### Fixed
- Three- and four-finger trackpad gestures on a controlled Mac triggered Mission Control or Launchpad
- Keyboard and mouse blocking stopped working after the Mac window lost focus

## v0.1.40 · 2026-05-07
### New
- **Push past the edge to switch**: after sharing starts, push the mouse past the screen edge to enter the other computer; the distance is configurable to prevent accidental switches
- When crossing screens, the cursor lands at the matching height on the other screen
- Push back through the opposite edge or press the hotkey to return to this computer

## v0.1.39 · 2026-05-06
### Improved
- Permission prompts have an “Open Settings” button that goes straight to the right system settings page
- After granting Input Monitoring, a clear hint says to quit completely (⌘Q) and reopen for it to take effect

## v0.1.36 · 2026-05-01
### New
- **Keyboard and mouse sharing is ready**: click “Start sharing” and both computers share one keyboard and mouse
### Improved
- On startup macOS checks both Accessibility and Input Monitoring and tells you which one is missing

## v0.1.27 · 2026-04-29
### Improved
- Opening the app again switches to the existing window instead of adding another menu bar icon

## v0.1.25 · 2026-04-28
### Improved
- When the LAN scan finds nothing, addresses are probed one by one, making the other computer easier to find with a VPN or firewall on
### Fixed
- Automatic disconnect after about 15 seconds

## v0.1.20 · 2026-04-12
### New
- Connection details panel: local IP, peer IP and latency

## v0.1.15 · 2026-04-05
### New
- Connect manually by IP to computers on another subnet
- Listen on a single network interface only

## v0.1.0 · 2026-03-31
### New
- First release: one keyboard and mouse shared between macOS and Windows on the local network
- Automatic device discovery on the LAN
- Multi-display layout configuration
- Dark / light theme
