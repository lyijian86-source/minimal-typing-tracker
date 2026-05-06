# TypeLedger

[Simplified Chinese](./README.zh-CN.md) | **English**

TypeLedger is a privacy-first Windows desktop typing tracker. It helps you understand daily output, session rhythm, hourly activity, and weekly efficiency without storing what you typed.

It is designed for writers, developers, researchers, students, and knowledge workers who want a calm local record of their typing activity.

> Repository: `Yijian6/type-ledger`
> Data compatibility: internal data paths still use `TypeRecord`

## Why Use It

TypeLedger answers practical questions:

- Did I actually write today?
- Is this week more productive than last week?
- Did output improve because I worked longer or because I worked more efficiently?
- Which hours of the day are usually my most active?
- Am I building a consistent writing or coding rhythm?

## Privacy Model

TypeLedger only stores aggregate numbers.

It records counts such as typed characters, pasted characters, backspaces, session length, hourly totals, and weekly summaries. It does not save raw typed text, clipboard content, window titles, website URLs, file names, screenshots, or keystroke sequences.

The app runs locally on your Windows machine. No cloud account is required.

## Download And Run

The portable Windows build is:

```text
TypeLedger-windows-portable.zip
```

To use it:

1. Download the zip from GitHub Releases.
2. Extract it to a folder you trust.
3. Run `TypeLedger.exe`.
4. Find the tray icon if the main window starts hidden.

The current build is unsigned. Windows SmartScreen or antivirus tools may warn because the app uses a global keyboard hook to count keystrokes. This is expected for local input trackers. TypeLedger does not store typed content.

## Features

| Area | What You Get |
| --- | --- |
| Daily tracking | Net count, keyboard input, pasted characters, backspaces, accuracy estimate |
| Session rhythm | Current session, last session, session length, recent activity |
| Speed estimate | CPM and WPM estimates based on recent keyboard input |
| Weekly efficiency | Weekly output, active time, active efficiency, comparison with last week and target |
| History | Daily records, 30-day trend, hourly distribution, CSV export |
| Tray app | Runs in the background, supports tray menu actions |
| Localization | English and Simplified Chinese UI |

## Data Location

TypeLedger stores local data under:

```text
%APPDATA%\TypeRecord\
```

The folder name remains `TypeRecord` for compatibility with earlier versions.

Main files:

- `data\daily_counts.json`
- `config\settings.json`
- `data\logs\type_record.log`

## Run From Source

Requirements:

- Windows
- Python 3.11+

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Build Windows Portable App

Install development dependencies:

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
```

Build:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Outputs:

```text
dist\TypeLedger\TypeLedger.exe
dist\TypeLedger-windows-portable.zip
```

## Development Checks

Run tests:

```powershell
python -m pytest
```

Run linting if needed:

```powershell
ruff check .
```

## Release Notes For Users

- This is a local Windows desktop app.
- It counts aggregate typing activity only.
- It does not store what you type.
- The portable build is currently unsigned.
- Some security tools may warn because keyboard counting requires a global keyboard hook.

## License

No license has been declared yet. Add a license before distributing broadly or accepting external contributions.
