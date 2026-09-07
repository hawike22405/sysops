# SysOps

> **A polished, cross-platform terminal system intelligence toolkit for Windows, Linux, and macOS.**

SysOps is a terminal-first system information and diagnostics utility built around fast, readable output and interactive terminal experiences. It reports hardware and operating-system information, provides live monitoring and benchmarking tools, renders ASCII/3D visuals, and includes an animated OS-logo flipbook.

## ✨ Highlights

- 🖥️ Cross-platform system information for **Windows, Linux, and macOS**
- 🎨 Rich, structured terminal UI with clear visual hierarchy
- 🔄 **Animated OS logo flipbook** using pre-rendered ASCII sprite frames
- 🪟 Windows, 🐧 Linux/Tux, and 🍎 macOS logo animations
- 🌈 ANSI color support with `NO_COLOR` compatibility
- 📐 Resize-aware terminal rendering with stable ASCII alignment
- 👻 Flicker-free in-place animation using ANSI cursor control
- 🛡️ Safe cursor restoration on normal exit, exceptions, and `Ctrl+C`
- ⚡ Low-overhead animation without rebuilding a 3D scene every frame
- 📊 CPU, memory, storage, network, GPU, uptime, desktop, and host information
- 📈 Live htop-style process monitor
- 🧪 CPU and disk benchmark tools
- 🏆 Local achievement/badge system
- 🖼️ Image-to-ASCII and interactive 3D ASCII image viewer
- 🎮 Terminal Dino game
- 🔄 Self-update support
- 🧩 JSON output for scripting and automation

---

## 🚀 Installation

### Windows — PowerShell

```powershell
irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
```

### Windows — Command Prompt

```cmd
curl -o install.bat https://raw.githubusercontent.com/hawike22405/sysops/main/install.bat && install.bat
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/hawike22405/sysops/main/install.sh | bash
```

The installers create an isolated virtual environment and expose the `sysops` command on the user's `PATH` without modifying the system Python installation.

### Development installation

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
python -m pip install -e .
```

Run the test suite with:

```bash
python -m pytest -q
```

---

# 📋 System Information

The default command produces a structured terminal report containing the most important information available from the host.

```bash
sysops
```

Useful options:

```bash
sysops --detail full
sysops --output report.json
sysops --modules cpu,memory,disks
sysops --no-root
sysops --no-logo
```

### Reported information

| Category | Examples |
|---|---|
| OS | Distribution, release, platform, version |
| Host | Hostname, architecture, processor |
| Kernel | Kernel release and version |
| CPU | Model, physical/logical cores, frequency, flags |
| Memory | RAM usage, available memory, swap |
| Storage | Partitions, filesystem, capacity, usage |
| Network | Interfaces, addresses, state, speed, MTU |
| GPU | Detected graphics hardware |
| Desktop | Desktop environment, window/session information, terminal, shell |
| Uptime | Host uptime |
| Sensors | Available non-privileged sensor information |

Optional probes are designed to fail safely when platform-specific information or utilities are unavailable.

---

# 🎞️ Animated OS Logo Flipbook

SysOps includes a lightweight **sprite-array / flipbook animation engine** in:

```text
src/sysops/features/os_logo.py
```

At startup, SysOps detects the host operating-system family using Python's platform information:

```text
Windows → Windows logo
Linux   → Tux penguin
macOS   → Apple logo
Other   → SysOps fallback logo
```

Each supported OS has **8 pre-rendered ASCII frames** representing different rotation poses. The animation moves through the sprite array sequentially and wraps back to the first frame:

```python
frame_index = (frame_index + 1) % len(frames)
```

This creates a continuous rotation illusion without the CPU cost of generating a 3D model for every frame.

### Animation characteristics

- Default playback: **12 FPS**
- Fixed-height sprite frames prevent vertical jitter
- Terminal width is recalculated during rendering to handle resizing
- Narrow terminals crop rather than wrap the logo
- ANSI color is injected without changing visible character width
- Cursor is hidden while animation runs
- Cursor is restored automatically when animation exits
- `Ctrl+C` is handled cleanly
- Rendering updates the existing terminal area rather than flooding the screen with new lines
- `NO_COLOR` disables ANSI coloring
- Non-TTY output automatically falls back to plain text

### Example

```bash
sysops --animate-logo
```

To change animation speed:

```bash
sysops --animate-logo --fps 16
```

To play a fixed number of rotations:

```bash
sysops --animate-logo --loops 3
```

The exact CLI flags depend on the installed command parser; the flipbook engine itself exposes `animate_os_logo()` for Python integration.

---

# 🖼️ ASCII Art & Logos

Render an image as ASCII art:

```bash
sysops ascii ./logo.png --width 80
```

Color mode:

```bash
sysops ascii ./logo.png --width 80 --color
```

Plain grayscale mode:

```bash
sysops ascii ./logo.png --width 80 --no-color --invert
```

Block rendering:

```bash
sysops ascii ./logo.png --width 80 --color --style blocks
```

If no image is supplied, the ASCII subsystem can use the built-in OS logo.

## Persistent custom logo

```bash
sysops logo set ./logo.png --width 24 --color
sysops logo show
sysops logo clear
```

Configuration is stored per-user rather than in the repository or system-wide configuration.

---

# 🧊 3D ASCII Image Viewer

SysOps contains an interactive software-rasterized 3D ASCII viewer under:

```text
src/sysops/features/ascii3d/
```

Launch it with:

```bash
sysops 3d /path/to/image.png
```

Options:

```bash
sysops 3d image.png --width 100 --height 35
sysops 3d image.png --scale 1.2
sysops 3d image.png --no-color
```

### Controls

| Key | Action |
|---|---|
| `w` / `s` | Tilt up / down |
| `a` / `d` | Rotate left / right |
| `+` / `-` | Zoom |
| `r` | Reset camera |
| `q` | Quit |

The subsystem performs image preprocessing, depth-map generation, mesh construction, barycentric rendering, color interpolation, lighting, and non-blocking terminal input.

The 3D viewer remains isolated from the normal system-information path so the basic `sysops` command does not require the experimental renderer.

---

# 📊 Live Process Monitor

Launch the htop-style monitor:

```bash
sysops monitor
```

Alias:

```bash
sysops htop
```

Optional refresh interval and initial sort:

```bash
sysops monitor --refresh 1.5 --sort cpu
```

### Controls

| Key | Action |
|---|---|
| `c` | Sort by CPU% |
| `m` | Sort by memory% |
| `p` | Sort by PID |
| `n` | Sort by process name |
| `q` | Quit |

The monitor uses Rich's live rendering rather than repeatedly printing full screens, reducing visible flicker.

---

# 🖥️ Interactive Dashboard

Launch the general interactive dashboard:

```bash
sysops dashboard
```

Alias:

```bash
sysops menu
```

### Controls

| Key | Action |
|---|---|
| `h` | Toggle extended statistics |
| `t` | Cycle themes |
| `c` | Copy displayed statistics |
| `r` | Refresh |
| `q` | Quit |

The dashboard supports multiple visual themes and platform-aware clipboard backends.

---

# 🧪 Benchmark

Run the CPU and disk benchmark:

```bash
sysops benchmark
```

Specify the duration of each stage:

```bash
sysops benchmark --duration 0.5
```

Skip the multi-core test:

```bash
sysops benchmark --no-multi
```

The benchmark reports:

- Temporary-file sequential write throughput
- Temporary-file sequential read throughput
- Single-core CPU operations/sec
- Multi-core CPU operations/sec
- Number of cores used

Benchmark results are hardware- and system-dependent and should be treated as relative measurements rather than formal hardware specifications.

---

# 🏆 Achievements

Check for newly unlocked badges:

```bash
sysops achievements
```

List all badges:

```bash
sysops achievements --list
```

Achievement state is stored locally and is not uploaded to a SysOps service.

---

# 🎮 Dino Game

Launch the terminal game:

```bash
sysops play
```

The game includes jumping, ducking, obstacles, scoring, pause/restart behavior, and persistent high score support.

---

# 🔄 Self Update

Check for and install the latest version:

```bash
sysops update
```

The updater tracks the `main` branch. Windows uses a detached helper process so the running installation can exit before files are replaced; POSIX systems use a detached shell helper.

If the update cannot be performed, SysOps reports the failure instead of silently modifying the installation.

---

# 🧱 Architecture

SysOps follows a `src/` package layout:

```text
sysops/
├── src/sysops/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── probes.py
│   ├── output.py
│   ├── ascii_art.py
│   ├── gpu.py
│   ├── sensors.py
│   ├── dino.py
│   └── features/
│       ├── __init__.py
│       ├── achievements.py
│       ├── benchmark.py
│       ├── htop_view.py
│       ├── interactive_menu.py
│       ├── updater.py
│       ├── os_logo.py
│       └── ascii3d/
├── tests/
├── pyproject.toml
├── install.ps1
├── install.bat
├── install.sh
└── README.md
```

### Core design principles

**Cross-platform first** — platform-specific probes and terminal input are isolated behind safe fallbacks.

**Optional subsystems** — experimental or heavyweight functionality, such as the 3D renderer, is kept separate from the normal reporting path.

**Terminal-safe rendering** — ANSI sequences are treated separately from visible text width so colored output remains aligned.

**Defensive probing** — unavailable commands, permissions, missing sensors, and unsupported hardware should not crash the entire report.

**Low-overhead animation** — the OS logo uses static sprite data and timed frame replacement rather than per-frame 3D computation.

**Automation-friendly output** — JSON output remains available independently of the human-oriented Rich renderer.

---

# 📦 Requirements

- **Python 3.9+**
- Rich
- psutil
- Pillow
- `windows-curses` on Windows
- NumPy for the experimental 3D ASCII subsystem
- Git for `sysops update`

The normal system-information workflow does not require the 3D subsystem to be actively used.

Dependencies are declared in `pyproject.toml`.

---

# 🧪 Development & Testing

Clone the repository:

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
```

Install in editable mode:

```bash
python -m pip install -e .
```

Run tests:

```bash
python -m pytest -q
```

Install additional 3D dependencies:

```bash
pip install -r src/sysops/features/ascii3d/requirements.txt
```

When extending SysOps, keep platform-specific behavior isolated and preserve the stable CLI path.

---

# 🛠️ Stability Notes

The CLI has been refactored to keep command registration and dispatch in one coherent flow. The report renderer has also been hardened around malformed or unavailable probe data.

The OS-logo renderer intentionally avoids terminal-wide clearing on every frame. It uses cursor positioning and erase sequences so animation stays visually stable without generating hundreds of scrolling lines.

If a terminal does not support ANSI control sequences, the renderer degrades toward plain text rather than treating terminal cosmetics as a hard dependency.

---

# 📜 License

This project is licensed under the MIT License. See [`LICENSE`](./LICENSE).

---

# 🤝 Contributing

Issues and pull requests are welcome.

When contributing:

1. Keep the normal CLI path stable.
2. Avoid making optional features mandatory.
3. Preserve Windows/Linux/macOS compatibility.
4. Add tests for new cross-platform behavior.
5. Prefer deterministic, low-overhead terminal rendering.
6. Run `python -m pytest -q` before submitting changes.

---

## Project Status

SysOps is an actively evolving terminal utility. Core system reporting, interactive monitoring, benchmarking, ASCII rendering, and the OS-logo flipbook are designed to work independently so new features can be introduced without destabilizing the base CLI.
