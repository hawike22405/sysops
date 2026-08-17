#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/hawike22405/sysops.git"
INSTALL_DIR="${SYSOPS_INSTALL_DIR:-$HOME/.local/share/sysops}"
BIN_DIR="${SYSOPS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="$INSTALL_DIR/.venv"

info()  { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m!!\033[0m %s\n' "$1"; }
error() { printf '\033[1;31mERROR:\033[0m %s\n' "$1" >&2; }

if ! command -v python3 >/dev/null 2>&1; then
    error "python3 is required but was not found on PATH."
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
info "Found python3 $PY_VERSION"

if ! python3 -m venv --help >/dev/null 2>&1; then
    error "The 'venv' module is not available for this python3 install."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/src/sysops" ]; then
    SRC_DIR="$SCRIPT_DIR"
    info "Using local source at $SRC_DIR"
else
    if ! command -v git >/dev/null 2>&1; then
        error "git is required to fetch sysops but was not found on PATH."
        exit 1
    fi
    SRC_DIR="$INSTALL_DIR/src-checkout"
    info "Fetching sysops source into $SRC_DIR"
    mkdir -p "$INSTALL_DIR"
    if [ -d "$SRC_DIR/.git" ]; then
        git -C "$SRC_DIR" pull --ff-only
    else
        rm -rf "$SRC_DIR"
        git clone --depth 1 "$REPO_URL" "$SRC_DIR"
    fi
fi

info "Setting up virtual environment at $VENV_DIR"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet

info "Installing sysops"
"$VENV_DIR/bin/pip" install --quiet "$SRC_DIR"

mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/sysops" "$BIN_DIR/sysops"
info "Linked $BIN_DIR/sysops -> $VENV_DIR/bin/sysops"

case ":$PATH:" in
    *":$BIN_DIR:"*)
        info "Install complete! Run it with: sysops"
        ;;
    *)
        warn "$BIN_DIR is not on your PATH yet."
        echo
        echo "  Add it by running:"
        echo "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
        echo
        echo "  (use ~/.zshrc instead of ~/.bashrc if you're on zsh)"
        echo
        echo "Then run: sysops"
        ;;
esac
