# SysOps

A cross-platform terminal system-information dashboard for Windows, macOS, and Linux. SysOps reports hostname, OS, CPU, memory, disks, network interfaces, GPU information, and uptime, and includes an interactive dashboard, htop-style process monitor, benchmark tools, achievements, ASCII art/logo support, a Dino game, and a self-update mechanism.

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

The installers create an isolated virtual environment and place the `sysops` command on your user `PATH` without modifying the system Python installation.

For a development checkout:

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
python -m pip install -e .
```

On Windows, use a Python version supported by your environment and let the package install its Windows-specific console dependency automatically.

## Usage

### System summary

```bash
sysops
sysops --detail full
sysops --output report.json
sysops --modules cpu,memory,disks
sysops --no-root
sysops --no-logo
```

The terminal summary uses the current panel-based renderer. JSON remains available through `--output` for automation.

### Live process monitor

```bash
sysops monitor
```

`sysops htop` is an alias.

Controls:

| Key | Action |
|---|---|
| `c` | Sort by CPU% |
| `m` | Sort by memory% |
| `p` | Sort by PID |
| `n` | Sort by process name |
| `q` | Quit |

### Interactive dashboard

```bash
sysops dashboard
```

`sysops menu` is an alias.

Controls:

| Key | Action |
|---|---|
| `h` | Toggle extended statistics |
| `t` | Cycle themes |
| `c` | Copy displayed statistics |
| `r` | Refresh |
| `q` | Quit |

### Benchmark

```bash
sysops benchmark
sysops benchmark --duration 0.5
sysops benchmark --no-multi
```

The benchmark measures temporary-file read/write throughput and single-/multi-core CPU operations.

### Achievements

```bash
sysops achievements
sysops achievements --list
```

Achievement data is stored locally; it is not uploaded to a SysOps service.

### Self-update

```bash
sysops update
```

The updater checks the remote `main` branch. On Windows it uses a detached helper so the running executable can exit before the installation is replaced.

### Dino game

```bash
sysops play
```

The game supports jumping, ducking, pause/restart, obstacles, scoring, and a persistent high score.

### ASCII art and logos

Render an image for one command:

```bash
sysops --image ./logo.png --logo-width 24
```

Manage a persistent logo:

```bash
sysops logo set ./logo.png --width 24 --color
sysops logo show
sysops logo clear
```

Render an image as ASCII art:

```bash
sysops ascii ./logo.png --width 80 --color
sysops ascii ./logo.png --width 80 --no-color --invert
sysops ascii ./logo.png --width 80 --color --style blocks
```

When no image is supplied to the ASCII command, SysOps falls back to a built-in OS logo.

## 3D ASCII renderer foundation

SysOps now contains an **experimental `ascii3d` subsystem** under `src/sysops/features/ascii3d/`.

It is intentionally additive: the original SysOps features remain the primary supported interface, while the 3D subsystem provides the foundation for a future CPU-based 3D terminal renderer.

Current pipeline:

```text
image.py → depth.py → mesh.py → geometry.py → camera.py
         → rasterizer.py → terminal.py → viewer.py
```

The foundation currently includes image preprocessing, depth generation, mesh construction, geometry primitives, camera scaffolding, lighting, rasterization scaffolding, terminal rendering helpers, a viewer scaffold, and a cube example.

The 3D feature is **not yet exposed as a stable `sysops 3d` command**. Camera projection, full triangle rasterization, interactive input, lighting/shading integration, and the final viewer loop are still implementation milestones.

See [`src/sysops/features/ascii3d/README.md`](src/sysops/features/ascii3d/README.md) for the subsystem details and suggested development order.

## Python API / project layout

The package uses a `src/` layout and a standard `pyproject.toml` build configuration. The 3D code is isolated under `sysops.features.ascii3d` so it can evolve without replacing the existing system-information, dashboard, monitor, game, benchmark, and updater modules.

## Requirements

- Python 3.9+
- Git for `sysops update`
- Rich
- psutil
- Pillow
- `windows-curses` on Windows
- NumPy for the experimental `ascii3d` subsystem

The normal SysOps runtime does not require the 3D subsystem to be used.

## Development

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
python -m pip install -e .
python -m pytest -q
```

To experiment with the 3D subsystem, install its additional dependencies from:

```bash
pip install -r src/sysops/features/ascii3d/requirements.txt
```

The existing test suite covers the core CLI/features and should remain green as the 3D renderer is developed incrementally.

## Uninstalling

The official installers keep SysOps in a user-managed directory. Remove the managed SysOps directory and its `PATH` entry when you want to uninstall.

## Contributing

Issues and pull requests are welcome at [github.com/hawike22405/sysops](https://github.com/hawike22405/sysops).

When adding new features, keep optional or experimental subsystems isolated so the stable CLI and cross-platform runtime remain intact.

## License

See [LICENSE](./LICENSE).
