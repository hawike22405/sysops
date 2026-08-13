# Design notes and short roadmap

This document outlines key design choices and a short roadmap for the sysops prototype.

Goals:
- Terminal-first, modern display
- Modular probes and JSON output
- No privileged operations by default

Roadmap:
- Prototype: Python + Rich (this branch)
- Add more probes: smartctl, dmidecode (opt-in)
- Add TUI & theming with Textual or port to Rust for single-binary release
