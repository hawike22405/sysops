# sysops

A modern, terminal-first system information reporter (prototype).

## Features

- Pretty terminal output (Rich)
- JSON output for automation
- Modular probes: OS, CPU, memory, disks, network, GPU, sensors
- No privileged operations by default

## Installation

### Linux / macOS / WSL / Git Bash
```bash
curl -fsSL https://raw.githubusercontent.com/hawike22405/sysops/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
```
> Requires Python 3 and Git for Windows to be installed and on `PATH`.
> If PowerShell blocks the script due to execution policy, run once:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then retry the command above.

Both installers do the same thing: check for Python 3, clone the repo (or use a local
checkout), create an isolated virtual environment, install `sysops` into it, and expose
a `sysops` command on your `PATH`.

```

After installation:

```bash
sysops
```

The installer creates an isolated environment under `~/.local/share/sysops` and places the `sysops` command in `~/.local/bin`.

### From a cloned repository

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
./install.sh
```

Then run:

```bash
sysops
```

### Development installation

For development, you can use the included Makefile:

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
make install
make run
```

## Usage

Run the command from any directory:

```bash
sysops
```

Available options:

```bash
sysops --detail full
sysops --format json
sysops --format compact
sysops --no-root
```

See `docs/DESIGN.md` for design notes and roadmap.
