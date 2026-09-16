# 🚀 SysOps

> **A professional, cross-platform terminal system intelligence toolkit for Windows, Linux, and macOS.**

SysOps is a high-performance, terminal-first system information and diagnostics utility. It combines deep system probing with polished, interactive terminal experiences—ranging from structured hardware reports and live monitoring to experimental 3D ASCII rendering.

---

## ✨ Key Features

### 🛠️ System Intelligence
- **Comprehensive Reporting:** detailed insights into CPU, Memory, Storage, Network, GPU, and OS internals.
- **Live Monitoring:** A high-performance, `htop`-style process monitor with real-time sorting.
- **Hardware Benchmarking:** Integrated tools for measuring CPU and disk throughput.
- **Automation Ready:** Supports JSON output for seamless integration into scripts and DevOps pipelines.

### 🎨 Visual Experience
- **High-Fidelity ASCII Art:** Advanced image-to-ASCII converter with automatic contrast normalization for crystal-clear visuals.
- **Adaptive Layout:** Intelligent, window-aware rendering that automatically switches between side-by-side and vertical layouts to prevent "breaking" on narrow terminals.
- **Interactive 3D Viewer:** A software-rasterized 3D ASCII renderer for viewing images with depth and lighting.
- **Animated OS Logos:** Lightweight "flipbook" animations for Windows, Linux, and macOS.

### 🎮 Extras
- **Integrated Game:** A fully functional Terminal Dino run game.
- **Achievement System:** Local badge tracking for system exploration and benchmarking.
- **Self-Updating:** Built-in update mechanism to keep your toolkit current.

---

## 🚀 Installation

### 📦 Quick Install (Recommended)

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
```

**Windows (CMD):**
```cmd
curl -o install.bat https://raw.githubusercontent.com/hawike22405/sysops/main/install.bat && install.bat
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/hawike22405/sysops/main/install.sh | bash
```

### 🛠️ Development Installation
If you wish to contribute or modify the source:
```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
python -m pip install -e .
```

---

## 📋 Usage Guide

### 1. Basic System Report
The primary command generates a structured report of your hardware and software environment.
```bash
sysops
```
**Useful Flags:**
- `--detail full`: Expanded information.
- `--output report.json`: Export data to JSON.
- `--no-logo`: Hide the ASCII logo.
- `--logo-style [chars|blocks|image]`: Change the logo rendering style.

### 2. Interactive Dashboard
A live, theme-able interface for quick statistics.
```bash
sysops dashboard
```
**Dashboard Controls:**
- `[h]`: Toggle hidden/extended statistics.
- `[t]`: Cycle through visual themes.
- `[i]`: **(New!)** Render a custom image as ASCII art directly in the dashboard.
- `[c]`: Copy current system info to clipboard.
- `[r]`: Refresh data.
- `[q]`: Quit.

### 3. ASCII & 3D Visuals
**Standard ASCII Render:**
```bash
sysops ascii <image_path> --width 80 --style chars
```

**Interactive 3D Viewer:**
```bash
sysops 3d <image_path>
```
*Controls: `W/A/S/D` to rotate/tilt, `+/-` to zoom, `R` to reset, `Q` to quit.*

### 4. Specialized Tools
| Command | Description |
| :--- | :--- |
| `sysops monitor` | Launch the live `htop`-style process monitor. |
| `sysops benchmark` | Run CPU and Disk performance tests. |
| `sysops fetch` | Display a `neofetch`-style system summary. |
| `sysops play` | Launch the Terminal Dino game. |
| `sysops achievements` | Check your unlocked system badges. |
| `sysops update` | Update SysOps to the latest version. |

---

## ⚙️ Configuration

Manage your persistent settings (like your custom logo) via the CLI:
```bash
# Set a custom image as your default logo
sysops logo set ./my_logo.png --width 30 --style chars

# View current configuration
sysops logo show

# Reset to default OS logo
sysops logo clear
```

---

## 🏗️ Technical Architecture

### 📐 Design Principles
- **Adaptive Rendering:** Uses `rich` and terminal-size detection to ensure the UI remains stable regardless of window dimensions.
- **Defensive Probing:** Every system probe is wrapped in safe fallbacks, ensuring the app never crashes due to missing hardware or permissions.
- **Performance-First:** Animations use static sprite arrays to avoid the CPU overhead of real-time 3D calculation.
- **UTF-8 Hardened:** Specifically patched for Windows terminals to prevent `UnicodeEncodeError` when rendering complex ASCII glyphs.

### 📁 Project Structure
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

---

## 📦 Requirements

- **Python 3.9+**
- Rich
- psutil
- Pillow
- `windows-curses` on Windows
- NumPy for the experimental 3D ASCII subsystem
- Git for `sysops update`

---

## 🧪 Development & Testing
Clone the repository, install in editable mode, and run tests using `pytest`.

---

## 📜 License
Distributed under the **MIT License**. See `LICENSE` for more information.
