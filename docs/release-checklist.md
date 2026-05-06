# Windows Release Checklist

## Build

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The unsigned portable build is generated at:

```text
dist\TypeLedger\TypeLedger.exe
```

The portable zip is generated at:

```text
dist\TypeLedger-windows-portable.zip
```

## Smoke Test

Before publishing a release, verify:

1. `TypeLedger.exe` starts without a console window.
2. The tray icon appears.
3. The main window can be opened from the tray menu.
4. Chinese and English language modes both save correctly.
5. The weekly efficiency section is visible.
6. CSV export writes a file and opens the data folder.
7. Reset today asks for confirmation.
8. Exit from the tray menu closes the process.

## Release Notes

Mention these points in GitHub Releases:

1. This is a local Windows typing tracker.
2. It stores aggregate counts only.
3. It does not store raw typed content.
4. Some antivirus tools may warn because global keyboard hooks are required for counting keystrokes.
5. The current build is unsigned.
