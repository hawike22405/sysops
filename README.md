# SysOps

A cross-platform terminal system-info dashboard for Windows, macOS, and Linux — hostname, OS, CPU, memory, disks, network interfaces, and GPU at a glance, plus a live htop-style process/resource monitor.

## Installation

### Windows — PowerShell

```powershell
irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
```

### Windows — Command Prompt

```cmd
curl -o install.bat https://raw.githubusercontent.com/hawike22405/sysops/main/install.bat && install.bat
```

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/hawike22405/sysops/main/install.sh | bash
```

The installers set up an isolated virtual environment under your user profile and put a `sysops` command on your `PATH` without modifying system Python packages.

## Usage

Run the system summary:

```bash
sysops
```

The summary uses one consistent bordered-panel layout for system, CPU, memory, storage, network, and GPU information. The old `--format` output switch has been removed.

### Live monitor

```bash
sysops monitor
```

`sysops htop` remains an alias.

Controls:

| Key | Action |
|---|---|
| `c` | Sort processes by CPU% |
| `m` | Sort processes by memory% |
| `p` | Sort processes by PID |
| `n` | Sort processes by name |
| `q` | Quit |

The monitor uses `rich` live rendering and `psutil` for cross-platform CPU, memory, and process data.

### Interactive dashboard

```bash
sysops dashboard
```

Alias:

```bash
sysops menu
```

Controls:

| Key | Action |
|---|---|
| `h` | Toggle extended statistics |
| `t` | Cycle dashboard themes |
| `c` | Copy displayed statistics |
| `r` | Refresh |
| `q` | Quit |

### Benchmark

```bash
sysops benchmark
sysops benchmark --duration 0.5
sysops benchmark --no-multi
```

The benchmark reports temporary-file read/write throughput and single/multi-core CPU operations per second.

### Achievements

```bash
sysops achievements
sysops achievements --list
```

Unlocked badges are stored locally in `~/.sysops_achievements.json`; no achievement data is sent to a server.

### Self-update

```bash
sysops update
```

SysOps checks the remote `main` branch and updates the installed source when changes are available. Windows uses a detached helper so the running executable is not overwritten while it is still locked.

### Dino game

```bash
sysops play
```

Controls include jump, duck, pause, restart, and quit.

### ASCII art and logos

Use an image for one run:

```bash
sysops --image ./logo.png --logo-width 24
```

Manage a persistent logo:

```bash
sysops logo set ./logo.png --width 24 --color
sysops logo show
sysops logo clear
```

Render an image as terminal ASCII art:

```bash
sysops ascii ./logo.png --width 80 --color
sysops ascii ./logo.png --width 80 --no-color --invert
```

## Useful options

```bash
sysops --detail full
sysops --output report.json
sysops --modules cpu,memory,disks
sysops --no-root
sysops --no-logo
```

`--output` writes the collected JSON data to a file. Normal terminal rendering is the single panel-based layout.

## Requirements

- Python 3.9+
- Git for `sysops update`
- Rich
- psutil
- Pillow
- `windows-curses` on Windows

## Development

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
make install
make run
```

Run tests with:

```bash
python -m pytest -q
```

## Uninstalling

- Windows: remove `%USERPROFILE%\.local\share\sysops`
- macOS/Linux: remove `~/.local/share/sysops`

Also remove the managed SysOps directory from your user `PATH` if necessary.

## Contributing

Issues and pull requests are welcome at [github.com/hawike22405/sysops](https://github.com/hawike22405/sysops).

## License

See [LICENSE](./LICENSE).
