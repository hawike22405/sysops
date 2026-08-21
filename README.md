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

The Windows installer creates an isolated virtual environment, installs the latest source from `main`, verifies that the `ascii` command is available, and creates the `sysops` launcher.

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

You can also play the Chrome-offline-style Dino runner directly in your
terminal. Jump over cacti and duck under flying pterodactyls to score points:

```bash
sysops play
# or
sysops --play
```

Controls:
- `SPACE` / `UP` / `W`: Jump (hold for variable jump height)
- `DOWN` / `S` / `,`: Duck
- `P`: Pause / Resume
- `SPACE` / `R`: Start / Restart game
- `Q`: Quit

Features:
- Start screen with countdown
- Animated Dino (2-frame run cycle, eye blinking, ducking poses)
- Pterodactyls, clouds, stars, and day/night cycle
- High score persistence saved to `~/.config/sysops/dino_highscore.json`
- Smooth ground scrolling, stats scoreboard, and time-based physics
- Safe terminal size guards & resize handling

On Windows, install `windows-curses` first (`pip install windows-curses`).

## ASCII Art

By default, `sysops` displays a built-in operating-system logo beside the system information panels.

### Use an image once

Pass an image with `--image`:

```powershell
sysops --image "D:\Opera Downloads\marshmello-material-3840x2160-26106.png"
```

Control the logo width:

```powershell
sysops --image "D:\Opera Downloads\marshmello-material-3840x2160-26106.png" --logo-width 24
```

Disable the logo completely:

```bash
sysops --no-logo
```

### Logo color controls

Automatic color detection is used by default. You can override it:

```bash
sysops --logo-color
sysops --no-logo-color
```

These options control the logo displayed beside the system summary.

## Persistent Custom Logo

You can save an image as your default logo so you do not need to pass `--image` every time.

### Set the default logo

```powershell
sysops logo set "D:\Opera Downloads\marshmello-material-3840x2160-26106.png" --width 24 --color
```

Now simply run:

```bash
sysops
```

The saved image, width, and color preference will be used automatically.

### View the saved logo configuration

```bash
sysops logo show
```

### Remove the custom logo

```bash
sysops logo clear
```

After clearing it, `sysops` returns to the built-in OS logo.

### Configuration location

On Windows, the configuration is stored at:

```text
%APPDATA%\sysops\config.json
```

On Linux/macOS it is stored under the XDG configuration directory, normally:

```text
~/.config/sysops/config.json
```

The configuration is plain JSON and can be inspected or edited manually.

## ASCII Art

`sysops ascii` converts an image into terminal-rendered ASCII art.

### Render an uploaded or local image

Copy or download an image somewhere accessible from the terminal, then run:

```powershell
sysops ascii "D:\Opera Downloads\marshmello-material-3840x2160-26106.png"
```

Common formats such as PNG, JPG, BMP, GIF, and WEBP are handled by Pillow.

### Control the size

```bash
sysops ascii image.png --width 120
```

### Force truecolor rendering

```bash
sysops ascii image.png --color
```

This uses 24-bit ANSI colors and half-block characters for a higher-resolution, Fastfetch-style terminal image.

### Force plain grayscale rendering

```bash
sysops ascii image.png --no-color
```

### Invert grayscale output

`--invert` applies to the plain character-ramp renderer:

```bash
sysops ascii image.png --no-color --invert
```

### Show the built-in OS logo

```bash
sysops ascii
```

## Command Reference

### System summary

```text
sysops [OPTIONS]
```

Important options:

| Option | Description |
|---|---|
| `--format {pretty,json,compact}` | Select output format |
| `--detail {brief,full}` | Select detail level |
| `--output, -o PATH` | Write output to a file |
| `--modules MODULES` | Run selected comma-separated modules |
| `--watch SECONDS` | Repeat the report at an interval |
| `--no-root` | Disable privileged probes |
| `--image PATH` | Use a custom image as the logo |
| `--logo-width N` | Set logo width in terminal characters |
| `--no-logo` | Hide the logo |
| `--logo-color` | Force 24-bit color for the logo |
| `--no-logo-color` | Force grayscale for the logo |

### Feature commands

```text
sysops dashboard [alias: menu]
sysops benchmark [--duration N] [--no-multi]
sysops achievements [--list]
```

### ASCII image command

```text
sysops ascii [IMAGE] [OPTIONS]
```

| Option | Description |
|---|---|
| `--width N` | ASCII output width |
| `--invert` | Invert the grayscale character ramp |
| `--color` | Force 24-bit ANSI color rendering |
| `--no-color` | Force plain grayscale rendering |

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
- Pillow for image rendering
- Rich for the terminal interface

The new dashboard, benchmark, and achievement modules use only the Python standard library.

See `docs/DESIGN.md` for design notes and roadmap.
