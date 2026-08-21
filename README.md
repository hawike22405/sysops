# sysops

A modern, terminal-first system information reporter with a Fastfetch/Neofetch-style display and image-to-ASCII rendering.

## Features

- Fast, terminal-first system summary
- Rich terminal output
- JSON output for automation
- Modular probes for OS, CPU, memory, disks, network, GPU, and sensors
- Neofetch/Fastfetch-style logo beside system information
- Render any supported image as ASCII art
- 24-bit truecolor image rendering with ANSI half-block characters
- Automatic terminal color detection
- Persistent custom logo configuration
- One-off logo overrides with `--image`
- Interactive live dashboard
- Quick CPU and disk benchmark
- Persistent system achievement badges
- One-command self-update
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

The installers create an isolated virtual environment, fetch the latest source from `main`, install the required dependencies, and create the `sysops` launcher. The source checkout is retained so `sysops update` can update it in place.

After installation, open a new terminal and run:

```bash
sysops
```

### From a cloned repository

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
./install.sh
```

Then:

```bash
sysops
```

### Development installation

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
make install
make run
```

## Updating SysOps

After the initial installation, update the local installation with:

```bash
sysops update
```

SysOps checks the remote `main` branch before changing anything. If the installed source is already at the latest commit, it reports:

```text
SysOps is already up to date. No further actions needed.
```

If a developer has pushed changes, it automatically:

1. Fetches the latest source.
2. Downloads the changes with a fast-forward-only Git update.
3. Installs the updated package into the existing isolated virtual environment.
4. Applies any changed Python package dependencies through pip.
5. Reports whether the update completed successfully.

The updater does not use `sudo`, does not modify system Python packages, and does not replace the virtual environment on every update. If the managed source checkout cannot be found, it asks you to rerun the official installer rather than making potentially unsafe changes.

## Basic Usage

Run the system reporter:

```bash
sysops
```

Useful options:

```bash
sysops --detail full
sysops --format json
sysops --format compact
sysops --no-root
sysops --no-logo
```

## Interactive Dashboard

Open a live terminal dashboard with automatic refresh and single-key controls:

```bash
sysops dashboard
# alias:
sysops menu
```

Controls:

- `h` — toggle extended statistics such as load, memory, swap, disk usage, process count, and kernel
- `t` — cycle `default`, `dark`, and `mono` themes
- `c` — copy the displayed statistics to the clipboard when `wl-copy`, `xclip`, `xsel`, `pbcopy`, or `clip.exe` is available
- `r` — force a refresh
- `q` — quit

The dashboard is implemented with the Python standard library and supports POSIX terminals plus Windows consoles.

## Benchmark

Run a short CPU and disk benchmark without installing another benchmarking package:

```bash
sysops benchmark
```

The benchmark reports:

- Sequential temporary-file write throughput in MB/s
- Sequential temporary-file read throughput in MB/s
- Single-core CPU operations per second
- Multi-core CPU operations per second

Adjust the duration or skip the multi-core stage:

```bash
sysops benchmark --duration 0.5
sysops benchmark --no-multi
```

The benchmark uses a temporary file and removes it when the test finishes. Results are intended for quick relative comparisons, not hardware certification or storage endurance testing.

## Achievements

SysOps can unlock persistent badges based on the current machine's hardware and uptime:

```bash
sysops achievements
sysops achievements --list
```

Examples include `Day One`, `Week Streak`, `Century Club`, `Quad Squad`, `Core Hoarder`, `Memory Lane`, `Modest Machine`, and `Disk Collector`.

Unlocked badges are stored locally in:

```text
~/.sysops_achievements.json
```

No achievement data is sent to a server.

## Game

Open a live terminal dashboard with automatic refresh and single-key controls:

```bash
sysops dashboard
# alias:
sysops menu
```

Controls:

- `h` — toggle extended statistics such as load, memory, swap, disk usage, process count, and kernel
- `t` — cycle `default`, `dark`, and `mono` themes
- `c` — copy the displayed statistics to the clipboard when `wl-copy`, `xclip`, `xsel`, `pbcopy`, or `clip.exe` is available
- `r` — force a refresh
- `q` — quit

The dashboard is implemented with the Python standard library and supports POSIX terminals plus Windows consoles.

## Benchmark

Run a short CPU and disk benchmark without installing another benchmarking package:

```bash
sysops benchmark
```

The benchmark reports sequential temporary-file write/read throughput and single/multi-core CPU operations per second.

```bash
sysops benchmark --duration 0.5
sysops benchmark --no-multi
```

## Achievements

SysOps can unlock persistent badges based on the current machine's hardware and uptime:

```bash
sysops achievements
sysops achievements --list
```

Unlocked badges are stored locally in `~/.sysops_achievements.json`. No achievement data is sent to a server.

## Game

You can also play the Chrome-offline-style Dino runner directly in your terminal:

```bash
sysops play
# or
sysops --play
```

Controls:
- `SPACE` / `UP` / `W`: Jump
- `DOWN` / `S` / `,`: Duck
- `P`: Pause / Resume
- `SPACE` / `R`: Start / Restart
- `Q`: Quit

## ASCII Art

By default, `sysops` displays a built-in operating-system logo beside the system information panels.

Use an image once:

```bash
sysops --image ./logo.png --logo-width 24
```

Save a persistent custom logo:

```bash
sysops logo set ./logo.png --width 24 --color
sysops logo show
sysops logo clear
```

`sysops ascii` converts images into terminal-rendered ASCII art:

```bash
sysops ascii ./logo.png --width 80 --color
sysops ascii ./logo.png --width 80 --no-color --invert
```

## Command Reference

### System summary

```text
sysops [OPTIONS]
```

| Option | Description |
|---|---|
| `--format {pretty,json,compact}` | Select output format |
| `--detail {brief,full}` | Select detail level |
| `--output, -o PATH` | Write output to a file |
| `--modules MODULES` | Run selected comma-separated modules |
| `--watch SECONDS` | Repeat at an interval |
| `--no-root` | Disable privileged probes |
| `--image PATH` | Use a custom image as the logo |
| `--logo-width N` | Set logo width |
| `--no-logo` | Hide the logo |
| `--logo-color` | Force 24-bit color |
| `--no-logo-color` | Force grayscale |

### Feature commands

```text
sysops dashboard [alias: menu]
sysops benchmark [--duration N] [--no-multi]
sysops achievements [--list]
```

### ASCII image command

```text
sysops update
sysops dashboard [alias: menu]
sysops benchmark [--duration N] [--no-multi]
sysops achievements [--list]
```

### Persistent logo commands

```text
sysops logo set IMAGE [OPTIONS]
sysops logo show
sysops logo clear
```

`logo set` accepts:

```text
--width N
--color
--no-color
```

## Examples

Show system information with the built-in logo:

```bash
sysops
```

Open the live dashboard:

```bash
sysops dashboard
```

Run a quick hardware benchmark:

```bash
sysops benchmark
```

Check for newly unlocked badges:

```bash
sysops achievements
```

List every badge:

```bash
sysops achievements --list
```

Use a custom image for one run:

```bash
sysops --image ./logo.png --logo-width 24
```

Save an image as the default logo:

```bash
sysops logo set ./logo.png --width 24 --color
```

Render an image as truecolor ASCII art:

```bash
sysops ascii ./logo.png --width 80 --color
```

Render a grayscale inverted version:

```bash
sysops ascii ./logo.png --width 80 --no-color --invert
```

Return to the built-in OS logo:

```bash
sysops logo clear
```

## Requirements

- Python 3
- Git for the `sysops update` command
- Pillow for image rendering
- Rich for the terminal interface

The new dashboard, benchmark, and achievement modules use only the Python standard library.
The dashboard, benchmark, achievement, and updater modules use only the Python standard library.

See `docs/DESIGN.md` for design notes and roadmap.
