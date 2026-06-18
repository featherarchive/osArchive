# OSINT Investigation Board

Local desktop OSINT investigation board built with Python, Tkinter, and SQLite.

## Run

```bash
python -m osint_tool
```

or:

```bash
python launch.py
```

The app stores its default database at `~/.local/share/osint-tool/osint.sqlite3`.

On Arch/CachyOS, Tkinter requires the OS package that provides `libtk8.6.so`:

```bash
sudo pacman -S tk
```

## Test

```bash
pytest
```

## V1 Scope

- Local cases
- Canvas-first entity board
- Entity cards for people, usernames, emails, phones, domains, IPs, URLs, organizations, locations, notes, and sources
- Relationship storage
- Notes, sources, attachments metadata, and lookup result storage
- Curated public lookup links
- URL parsing, DNS lookup, and HTTP header/status helpers
