# osArchive 0.1

Initial public release.

## Highlights

- Local OSINT investigation board with cases, entities, relationships, notes, sources, and lookup results.
- Command Map UI theme with graph canvas, highlighted main node, and idle orbit view for related nodes.
- Built-in Sherlock-style username scanning with bundled fallback site data.
- WhatsMyName candidate URL generation.
- DNS and HTTP metadata transforms.
- Target import, graph auto-arrange, radial layout, collapse/expand, remove node, and delete-all board actions.
- Linux and Windows launcher files.

## Install

Linux:

```bash
python -m pip install -e .
osarchive
```

Windows:

```powershell
py -3 -m pip install -e .
windows\osArchive.bat
```

## Requirements

- Python 3.11 or newer
- Tkinter
