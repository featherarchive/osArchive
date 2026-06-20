# osArchive for Windows

## Install

1. Install Python 3.11 or newer from python.org.
2. Open PowerShell in the osArchive project folder.
3. Run:

```powershell
py -3 -m pip install -e .
```

## Run

Double-click `windows\osArchive.bat`, or run:

```powershell
py -3 -m osint_tool
```

The local database is stored at:

```text
%APPDATA%\osArchive\osint.sqlite3
```

The built-in Sherlock scan works without the `archive` command. It uses bundled fallback site data by default. To use a larger Sherlock data file on Windows, place Sherlock's `data.json` here:

```text
%APPDATA%\osArchive\sherlock-data.json
```
