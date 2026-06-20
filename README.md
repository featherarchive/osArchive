# osArchive

Local desktop OSINT investigation board built with Python, Tkinter, and SQLite.

## Run

Install locally:

```bash
python -m pip install -e .
```

Then run:

```bash
osarchive
```

or from the source folder:

```bash
python -m osint_tool
```

or:

```bash
python launch.py
```

On Linux, the app stores its default database at `~/.local/share/osint-tool/osint.sqlite3`.
On Windows, it stores the database at `%APPDATA%\osArchive\osint.sqlite3`.

On Arch/CachyOS, Tkinter requires the OS package that provides `libtk8.6.so`:

```bash
sudo pacman -S tk
```

## Test

```bash
pytest
```

## Version 0.1

- Local cases
- Canvas-first investigation board
- Entity cards for people, usernames, emails, phones, domains, IPs, URLs, organizations, locations, notes, and sources
- Relationship storage
- Main-node pinning and idle orbit view for related nodes
- Notes, sources, attachments metadata, and lookup result storage
- Curated public lookup links
- Target import, graph layout helpers, collapse/expand, and delete-all board management
- Built-in Sherlock-style username scans with bundled fallback sites
- WhatsMyName candidate URL generation
- URL parsing, DNS lookup, and HTTP header/status helpers
- Linux and Windows launcher files
