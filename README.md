# sysops

A modern, terminal-first system information reporter (prototype).

## Features

- Pretty terminal output (Rich)
- JSON output for automation
- Modular probes: OS, CPU, memory, disks, network, GPU, sensors
- No privileged operations by default

## Installation

Clone the repository and install the project using the included Makefile:

```bash
git clone https://github.com/hawike22405/sysops.git
cd sysops
make install
```

## Usage

After installation, run sysops from the project directory with:

```bash
make run
```

See `docs/DESIGN.md` for design notes and roadmap.
