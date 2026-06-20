# osArchive for Linux

## Install

Install Python 3.11 or newer and Tkinter. On Arch/CachyOS:

```bash
sudo pacman -S python tk
```

From the osArchive project folder:

```bash
python -m pip install -e .
```

## Run

```bash
osarchive
```

or:

```bash
./linux/osArchive.sh
```

The local database is stored at:

```text
~/.local/share/osint-tool/osint.sqlite3
```
