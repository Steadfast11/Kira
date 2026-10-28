# Kira

Kira is a voice and AI assistant for macOS. It can see what is on your screen, answer questions, manage your calendar, and run background agents.

## Download and run

1. Download `Kira.zip` from the [latest release](https://github.com/Steadfast11/Kira/releases/latest).
2. Unzip it and drag `Kira.app` into your **Applications** folder.
3. Open `Kira` by double-clicking it. The first time, macOS may say the app is from an unidentified developer. Kira is not signed with an Apple developer account yet, so do one of these:
   - Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway**.
   - Or run this command in Terminal once:
     ```bash
     xattr -dr com.apple.quarantine /Applications/Kira.app
     ```
4. When Kira opens, its setup window helps you connect an AI service.
5. To talk to Kira, hold **Control + Option + Space** and speak.

To update, download the newest `Kira.zip` from the releases page and replace the old app.

## Requirements

- macOS 26 or later on an Apple Silicon Mac (M1 or newer).
- An AI service: Claude (Claude Code), Codex, or your own API key. The setup window asks which one you want to use.
- Python 3 (included with macOS; if it is missing, Xcode Command Line Tools install it).

## Permissions

Kira needs these macOS permissions: microphone, speech recognition, screen recording, Accessibility, calendar, and Automation. Each permission is requested only for the task that needs it. Calendar access lets Kira read your calendar and add the events you ask for.

## Features

- **Voice and chat:** type or say a question, and Kira reads the answer aloud.
- **Point at your screen:** circle, click, or scribble on anything on screen, then type or say your question. Kira sees the marked spot.
- **Calendar:** manage events with requests such as "Move my dentist appointment to 4." Adding is immediate; moving or deleting asks first.
- **Background agents:** run long tasks in the background and check the results later.
- **Meetings and dictation:** get meeting summaries and dictate text by voice.

## Build from source (for developers)

Requirements: Xcode Command Line Tools (`xcode-select --install`).

```bash
git clone https://github.com/Steadfast11/Kira.git
cd Kira
./build.sh
```

`build.sh` builds Kira, installs it to `~/Applications/Kira.app`, and starts it. A copy built from a source checkout updates itself from GitHub through **Settings → Updates**.

To install with Nix, use `flake.nix`. In that case Settings shows "Updates are managed by Nix", and you update with `nix profile upgrade`.

To build the downloadable `Kira.zip` yourself:

```bash
KIRA_RELEASE_ZIP=$PWD/dist/Kira.zip ./build.sh
```

## Author

Author: **Xasan Abdukhafizov**

Copyright © 2026 Xasan Abdukhafizov. Licensed under the [Apache License 2.0](LICENSE).

Authorship notice: see AUTHORS.md and COPYRIGHT. Third-party rights are not changed by this notice.
