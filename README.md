# TypeLedger

**English** | [简体中文](./README.zh-CN.md)

TypeLedger is a privacy-first Windows desktop typing tracker for people who want a calm, local, reliable view of daily output, session rhythm, hourly activity, and weekly efficiency.

It runs in the background, lives in the system tray, stores aggregate metrics only, and never stores raw typed content.

> Current product name in code/UI: `Type Record`  
> Recommended public GitHub repository name: `type-ledger`

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

After launch, the app can stay in the system tray and keep tracking in the background.

## Why This Name

`TypeLedger` is the naming direction I recommend for the repository because it is:

- easier to remember than a generic `tracker` name
- more searchable than abstract product names
- aligned with the product's tone: measured, private, trustworthy
- broad enough for future analytics features without sounding gimmicky

Other strong alternatives:

- `type-pulse`
- `key-ledger`
- `typing-ledger`

## What It Does

TypeLedger helps you answer practical questions like:

- Did I actually write today?
- Was this week productive or just busy?
- Did output improve because I worked longer or because I worked better?
- What time of day do I usually type the most?

It is designed for long-running personal use on Windows, not for text capture.

## Who It Is For

- writers who want a lightweight local writing ledger
- knowledge workers who care about daily output rhythm
- bilingual users who type in Chinese and English
- privacy-sensitive users who do not want cloud logging

## Core Capabilities

| Area | What you get |
| --- | --- |
| Daily tracking | Net count, keyboard typed, pasted volume, backspace count, estimated accuracy |
| Session analytics | Session duration, session typed volume, live speed, recent activity |
| Trend views | 30-day trend, hourly activity view, full history dialog |
| Weekly insight | Weekly output, active time, active efficiency, comparison views |
| UX | Tray-first workflow, bilingual UI, scroll-safe dashboard, settings dialog |
| Reliability | Backup recovery, malformed data sanitization, health report output |
| Privacy | Aggregate metrics only, no raw typed text storage |

## Privacy Model

TypeLedger stores:

- counts
- timestamps
- session durations
- hourly totals
- weekly aggregates

TypeLedger does **not** store:

- raw typed text
- clipboard text content
- document content
- application content

Paste actions affect metrics, but pasted text itself is never written to disk.

## Metric Definitions

| Metric | Meaning |
| --- | --- |
| Net count | Main daily count. Includes typed input and paste, and may subtract backspace depending on settings. |
| Keyboard typed | Direct keyboard input only, excluding paste. |
| Pasted | Volume inferred from paste actions. |
| Accuracy | Estimate based on kept keyboard input relative to correction behavior. |
| Current speed | Keyboard characters typed during the last 60 seconds. |
| Peak WPM | Estimated peak speed using `5 chars = 1 word`. |
| Weekly efficiency | Weekly output divided by active session minutes. |

## Accuracy Notes

This project uses a global keyboard hook, so its strongest signal is **input behavior**, not perfectly reconstructed final text.

Important limitations:

- IME workflows such as Chinese pinyin composition are tracked consistently at the key-action level, but may not exactly match committed text.
- Backspace is not always a perfect inverse of prior input across editors and selection flows.
- Elevated applications may partially block input visibility for a normal-permission process.

The product is intentionally optimized for stable aggregate measurement rather than exact text reconstruction.

## Screens You Can Show in the README

Recommended future screenshots:

1. Main dashboard
2. Weekly efficiency detail dialog
3. Hourly activity dialog
4. Tray menu
5. Settings dialog

Recommended asset folder:

```text
assets/readme/
```

Suggested filenames:

- `dashboard-en.png`
- `dashboard-zh.png`
- `weekly-efficiency.png`
- `hourly-view.png`
- `tray-menu.png`
- `settings-dialog.png`

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python app.py
```

## Release Status

Current state:

- source app is usable
- tray workflow is implemented
- dashboard, weekly efficiency, history, and settings flows are working
- tests cover storage, metrics, tray labels, and key UI smoke paths
- packaged Windows release flow is not finalized yet

## Development

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run tests:

```powershell
python -m pytest
```

Optional syntax smoke check:

```powershell
python -m compileall type_record tests
```

## Data Storage

Primary paths:

```text
%APPDATA%\TypeRecord\data\daily_counts.json
%APPDATA%\TypeRecord\config\settings.json
```

Fallback path when `%APPDATA%` is not writable:

```text
<project>\data\
```

Related durability files:

- `daily_counts.json.bak`
- `health_report.json`

## Reliability Features

- backup JSON fallback
- malformed record filtering
- invalid timestamp / day / hour sanitization
- health report generation
- session flush on timeout and shutdown
- UI smoke tests for key window flows

## Project Structure

```text
app.py
requirements.txt
requirements-dev.txt
type_record/
  app.py
  config.py
  counter.py
  charting.py
  metrics.py
  storage.py
  tray.py
  ui/
    dialogs.py
    formatting.py
    theme.py
    widgets.py
    window.py
tests/
```

## Roadmap

Near-term priorities:

1. Finish interaction consistency and polish
2. Add polished screenshots and release-facing assets
3. Prepare packaging and distribution workflow
4. Improve onboarding and metric explanation quality

Potential next-stage improvements:

- packaged Windows release
- richer weekly comparisons
- stronger session review tools
- clearer IME-related explanation layer

## FAQ

### Does it store what I type?

No. It stores counts, timestamps, durations, and aggregate metrics only.

### Is this accurate for Chinese IME input?

It is consistent at the key-action level, but it is not guaranteed to exactly match final committed characters in every IME workflow.

### Does paste count?

Yes. Paste contributes to total volume metrics, but pasted text itself is never stored.

### Can I use it as a precise text-production meter?

Not perfectly. It is better understood as a stable input-behavior tracker than a final-text reconstruction tool.

## Status

The product already has meaningful behavior and a real desktop workflow, but it is still being actively refined across UX, packaging, and public presentation.
