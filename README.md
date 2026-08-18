# sysops

A modern, terminal-first system information reporter (prototype).

## Features

- Pretty terminal output (Rich)
- JSON output for automation
- Modular probes: OS, CPU, memory, disks, network, GPU, sensors
- ASCII-art image rendering
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

## ASCII Art

You can turn any supported image into ASCII art directly from the terminal.

### 1. Upload or copy an image

Place your image anywhere you can access from the terminal, for example:

```text
Downloads/my-image.png
```

The ASCII-art command supports common image formats handled by Pillow, including PNG, JPG, BMP, GIF, and WEBP.

### 2. Run the ASCII command

Pass the image path to `sysops ascii`:

```bash
sysops ascii Downloads/my-image.png
```

The command converts the image to grayscale and prints the ASCII version in your terminal.

### 3. Change the output width

Use `--width` to control how wide the ASCII art is:

```bash
sysops ascii Downloads/my-image.png --width 120
```

A larger width gives more detail but uses more terminal space.

### 4. Invert the brightness

Use `--invert` to reverse the character brightness ramp:

```bash
sysops ascii Downloads/my-image.png --invert
```

You can combine both options:

```bash
sysops ascii Downloads/my-image.png --width 120 --invert
```

### 5. Show the built-in OS logo

You do not need to provide an image. Running the command without a path displays the built-in logo for the detected operating system:

```bash
sysops ascii
```

See `docs/DESIGN.md` for design notes and roadmap.
