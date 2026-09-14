"""High-quality ASCII art logos with ANSI brand colors for major operating systems.

Each logo is stored as a multi-line string.  The module provides a mapping from
distro/OS identifiers to their art and colour palette.  All logos use the same
height (padded where necessary) so the side-by-side layout never jitters.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------
CSI = "\x1b["
RESET = f"{CSI}0m"
BOLD = f"{CSI}1m"


def _color(code: str) -> str:
    """Return an ANSI SGR escape for the given code."""
    return f"{CSI}{code}m"


# ---------------------------------------------------------------------------
# Brand colour palettes  (primary, secondary)
# Each entry is a tuple of ANSI SGR codes.
# ---------------------------------------------------------------------------
DISTRO_COLORS: dict[str, tuple[str, str]] = {
    "arch":         ("1;36", "1;36"),    # Cyan / Cyan
    "ubuntu":       ("1;33", "1;31"),    # Orange(yellow) / Red
    "debian":       ("1;31", "1;37"),    # Red / White
    "fedora":       ("1;34", "1;37"),    # Blue / White
    "opensuse":     ("1;32", "1;37"),    # Green / White
    "centos":       ("1;35", "1;32"),    # Magenta / Green
    "manjaro":      ("1;32", "1;32"),    # Green / Green
    "mint":         ("1;32", "1;37"),    # Green / White
    "pop":          ("1;36", "1;33"),    # Cyan / Yellow
    "elementary":   ("1;37", "1;34"),    # White / Blue
    "gentoo":       ("1;35", "1;37"),    # Magenta / White
    "void":         ("1;32", "1;35"),    # Green / Magenta
    "alpine":       ("1;34", "1;37"),    # Blue / White
    "nixos":        ("1;34", "1;36"),    # Blue / Cyan
    "kali":         ("1;34", "1;37"),    # Blue / White
    "raspbian":     ("1;31", "1;32"),    # Red / Green
    "endeavouros":  ("1;35", "1;36"),    # Magenta / Cyan
    "artix":        ("1;36", "1;36"),    # Cyan / Cyan
    "slackware":    ("1;34", "1;37"),    # Blue / White
    "rhel":         ("1;31", "1;37"),    # Red / White
    "rocky":        ("1;32", "1;37"),    # Green / White
    "alma":         ("1;34", "1;33"),    # Blue / Yellow
    "linux":        ("1;33", "1;37"),    # Yellow (Tux) / White
    "windows":      ("1;34", "1;36"),    # Blue / Cyan
    "macos":        ("1;32", "1;33"),    # Green / Yellow
    "unknown":      ("1;37", "1;37"),    # White / White
}


def get_logo_colors(distro_id: str) -> tuple[str, str]:
    """Return (primary_sgr, secondary_sgr) for *distro_id*."""
    key = distro_id.lower().replace(" ", "").replace("os", "")
    for name, colors in DISTRO_COLORS.items():
        if name in key or key in name:
            return colors
    return DISTRO_COLORS["unknown"]


# ---------------------------------------------------------------------------
# ASCII art logos
# ---------------------------------------------------------------------------

# Each logo is 18 lines tall; shorter ones are bottom-padded.
_LOGO_HEIGHT = 18


def _pad_logo(art: str) -> str:
    """Ensure every logo has exactly _LOGO_HEIGHT lines."""
    lines = art.splitlines()
    if len(lines) < _LOGO_HEIGHT:
        max_w = max((len(l) for l in lines), default=0)
        lines.extend([" " * max_w] * (_LOGO_HEIGHT - len(lines)))
    return "\n".join(lines[:_LOGO_HEIGHT])


# ---- Arch Linux ----
_ARCH = "\n".join([
    "        /\\         ",
    "       /  \\        ",
    "      /\\   \\       ",
    "     /  \\   \\      ",
    "    /   _\\   \\     ",
    "   /   /  \\   \\    ",
    "  /   /    \\   \\   ",
    " /   /  /\\  \\   \\  ",
    "/   /  /  \\  \\   \\ ",
    "   /  /    \\  \\    ",
    "  /  /______\\  \\   ",
    " /              \\  ",
    "/________________\\ ",
])

# ---- Ubuntu ----
_UBUNTU = "\n".join([
    "             .-/+oossssoo+/-.        ",
    "         `:+ssssssssssssssssss+:`    ",
    "       -+ssssssssssssssssssyyssss+-  ",
    "     .ossssssssssssssssssdMMMNysssso.",
    "   /ssssssssssshdmmNNmmyNMMMMhssssss/",
    "  +ssssssssshmydMMMMMMMNddddyssssssss+",
    " /sssssssshNMMMyhhyyyyhmNMMMNhssssssss/",
    ".ssssssssdMMMNhsssssssssshNMMMdssssssss.",
    "+sssshhhyNMMNyssssssssssssyNMMMysssssss+",
    "ossyNMMMNyMMhsssssssssssssshmmmhssssssso",
    "ossyNMMMNyMMhsssssssssssssshmmmhssssssso",
    "+sssshhhyNMMNyssssssssssssyNMMMysssssss+",
    ".ssssssssdMMMNhsssssssssshNMMMdssssssss.",
    " /sssssssshNMMMyhhyyyyhmNMMMNhssssssss/ ",
    "  +ssssssssshmydMMMMMMMNddddyssssssss+  ",
    "   /ssssssssssshdmNNNNmyNMMMMhssssss/   ",
    "     .ossssssssssssssssssdMMMNysssso.    ",
    "       -+sssssssssssssssssssssssss+-     ",
])

# ---- Debian ----
_DEBIAN = "\n".join([
    "       _,met$$$$$gg.          ",
    "    ,g$$$$$$$$$$$$$$$P.       ",
    '  ,g$$P"        """Y$$.".    ',
    " ,$$P'              `$$$.    ",
    "',$$P       ,ggs.     `$$b:  ",
    "`d$$'     ,$P\"'   .    $$$   ",
    " $$P      d$'     ,    $$P   ",
    " $$:      $$.   -    ,d$$'   ",
    " $$;      Y$b._   _,d$P'    ",
    " Y$$.    `.`\"Y$$$$P\"'       ",
    " `$$b      \"-.__             ",
    "  `Y$$                       ",
    "   `Y$$.                     ",
    "     `$$b.                   ",
    "       `Y$$b.                ",
    '          `"Y$b._            ',
    '              `"""           ',
])

# ---- Fedora ----
_FEDORA = "\n".join([
    "          /:-------------:\\        ",
    "        :-------------------::     ",
    "      :-----------/sssssssss/-:    ",
    "    :-----------ssssssssssssss----:",
    "  .----------.ssssssssssssssss-----:",
    " :----------ssssssssssssssssss------:",
    ":----------ssssssssssssssssssss------:",
    ":---------sssssssssssssssssssss------:",
    ":--------ssssssssss/------+sssss-----:",
    " :------ssssssss/--:------:+ssss-----:",
    "  :-----sssss/----::------::+sss-----:",
    "   :----sss/------::------:::+ss-----:",
    "    :---ss/-------::------:::+s------:",
    "     :--s/--------::------::::------: ",
    "      :-/---------::------::::-----:  ",
    "       :----------::------::-----:    ",
    "        :-------------------:---:     ",
    "          :-----------------::        ",
])

# ---- openSUSE ----
_OPENSUSE = "\n".join([
    "            .;ldkO0000Okdl;.       ",
    "        .;d00xl:^''''''^:ok00d;.   ",
    "      .d00l'                'o00d. ",
    "    .d0Kd'    Geeko          :O0d. ",
    "   .OK0Kk.                  lKKK0.",
    "  :OKKKKKOxol:,.      ,;:ldOKKKKK:",
    "  ;OOOOKKKKKKKKKdolOKKKKKKKKOOO;  ",
    "   lOOOOOOOKKKKKKKKKKKKOOOOOOl    ",
    "    ;lOOOOOOKKKKKKKKOOOOOOl;      ",
    "       :dOOOOOOOOOOOOOd:          ",
    "          ',;clllc;,'             ",
])

# ---- Manjaro ----
_MANJARO = "\n".join([
    "  ██████████████████  ████████",
    "  ██████████████████  ████████",
    "  ██████████████████  ████████",
    "  ██████████████████  ████████",
    "  ████████            ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
    "  ████████  ████████  ████████",
])

# ---- Linux Mint ----
_MINT = "\n".join([
    " MMMMMMMMMMMMMMMMMMMMMMMMMmds+.    ",
    " MMm----::-://////////////oymNMd+` ",
    " MMd      /++                -sNMd:",
    " MMNso/`  dMM    `.::-. .-::.` .hMN:",
    " ddddMMh  dMM   :hNMNMNhNMNMNh: `NMm",
    "     NMm  dMM  .NMN/-+MMM+-/NMN` dMM",
    "     NMm  dMM  -MMm  `MMM   dMM. dMM",
    "     NMm  dMM  -MMm  `MMM   dMM. dMM",
    "     NMm  dMM  .mmd  `mmm   yMM. dMM",
    "     NMm  dMM`  ..`   ...   ydm. dMM",
    "     hMM- +MMd/-------...-:sdds  dMM",
    "     -NMm- :hNMNNNmdddddddddy/` dMM",
    "      -dMNs-``-::::-------.``    dMM",
    "       `/dMNmy+/:-------------:/yMMM",
    "          ./ydNMMMMMMMMMMMMMMMMMMMMM ",
    "             .MMMMMMMMMMMMMMMMMMM   ",
])

# ---- Pop!_OS ----
_POP = "\n".join([
    "              /////////////         ",
    "         /////////////////////      ",
    "      ///////*767////////*767////   ",
    "    //////7676767676*7676*//767///  ",
    "   /////7676767676//7676767////767///",
    "  /////767676///*7676767///767///    ",
    " ///////767676///7676767///767/767/  ",
    "////////767676//76767676///767//     ",
    "/////////76767676767676767///767//   ",
    "//////////76767676767676////767//    ",
    "///////////7676767676/////767//      ",
    "////////////*76767677/////767//      ",
    "//////////////767////////767//       ",
    "  //////////////////////767//        ",
    "   ///////////////////767//          ",
    "     /////////////////767/           ",
    "       /////////////767              ",
    "          ////////                   ",
])

# ---- Gentoo ----
_GENTOO = "\n".join([
    "         -/oyddmdhs+:.             ",
    "     -odNMMMMMMMMNNmhy+-`          ",
    "   -yNMMMMMMMMMMMNNNmmdhy+-        ",
    " `omMMMMMMMMMMMMNmdmmmmddhhy/`     ",
    " omMMMMMMMMMMMNhhyyyohmdddhhhdo`   ",
    ".ydMMMMMMMMMMdoyhsrosmsmdddhhhhdm+`",
    " ydMMMMMMMMMdoyhssssshmdddhhhhddd+`",
    " :mMMMMMMMMMyoyhssssshmdddhhhhddd+ ",
    " `oNMMMMMMMMdyyhssssshmdddhhhdddd+ ",
    "  `sNMMMMMMMMyoyhsssshmdddhhhdddd+ ",
    "    `yMMMMMMMMMyoyhysshmdddhhhdddo. ",
    "      /NMMMMMMMMyoyhysshmdddhhhdo`  ",
    "       .+dNMMMMMMMyoyhyhmdddhho.    ",
    "          `omMMMMMMMyoyhyhddiyo`    ",
    "           `+dNMMMMMMyohdsss`       ",
    "             `/yNMMMMMMysos`        ",
    "                 .:+syhhdhys/.      ",
])

# ---- Void Linux ----
_VOID = "\n".join([
    "                __.;=====;.__      ",
    "            _.=+==++=++=+=+===;.   ",
    "             -=+++=+===+=+=+++++=_ ",
    "        .     -=:``     `--==+=++==.",
    "       _vi,    `            --+=++++:",
    "      .vtez.                 -=+++;.",
    "        .+-.    _:,!=-  :=. ;=+;.  ",
    "         -=::= =_ = =_=; =+++.    ",
    "          ,= = = = = = =.  ,=+.   ",
    "           .-= = = =,= = = +=.    ",
    "             ==,= =,= = =,=+-.    ",
    "              += = = = = =.-       ",
    "               .= = = =;-.        ",
    "                  ,= = =,.        ",
    "                    `-= -.`       ",
])

# ---- Alpine Linux ----
_ALPINE = "\n".join([
    "       .hddddddddddddddddddddddh.   ",
    "      :dddddddddddddddddddddddddd:   ",
    "     /dddddddddddddddddddddddddddd/  ",
    "    +dddddddddddddddddddddddddddddd+ ",
    "  `sdddddddddddddddddddddddddddddddds`",
    " `ydddddddddddd++hdddddddddddddddddddy`",
    ".hddddddddddd+`  `+ddddh:-sdddddddddddh.",
    "hdddddddddd+`      `+y:    `sdddddddddddh",
    "ddddddddh+`   `//`    `      `+ddddddddddd",
    "ddddddh+`   `/hddh/`           `+dddddddddd",
    "ddddh+`   `/hdddddddh/`          `+ddddddddd",
    "ddd+`   `/hddddddddddddh/`         `+dddddddd",
])

# ---- NixOS ----
_NIXOS = "\n".join([
    "          ::::.    ':::::     ::::'  ",
    "          ':::::    ':::::.  ::::'   ",
    "            :::::     '::::.:::::    ",
    "      .......:::::..... ::::::::     ",
    "     ::::::::::::::::::. ::::::    ::::",
    "    ::::::::::::::::::::: :::::.  .::::'",
    "           .....           ::::' :::::'",
    "          :::::            '::' :::::'",
    " ........:::::               ' ::::::::::.",
    " :::::::::::::                 ::::::::::::::",
    "  ::::::::::: ..              :::::          ",
    "      .::::: .:::            :::::          ",
    "     .:::::  :::::          '''''    .:.    ",
    "     :::::   ':::::.                :::::   ",
    "    .::::     ::::::::::            ::::::   ",
    "    :::::       '::::::.         .:::::::'   ",
    "     :::::.        ':::::::::::::::::::'     ",
    "      ':::::.        '::::::::::'           ",
])

# ---- Kali Linux ----
_KALI = "\n".join([
    "      ,.....                        ",
    "  ----`     `..,;:ccc,.             ",
    "           ......''';lxO.           ",
    " .....''''...........:oo,.          ",
    "            ___        .oo;.        ",
    "           / __ \\     .oP\"         ",
    "          / / _` \\   .oP'           ",
    "         / / / ) |  oP'             ",
    "      .-/ / / / /  o'               ",
    "     `---/  `-'  .l                 ",
    "                 ;l                 ",
    "                ;l                  ",
    "              _/l;                  ",
    "             oP'`                   ",
    "            oP'                     ",
    "           oP'                      ",
    "          oP'                       ",
])

# ---- Raspbian / Raspberry Pi OS ----
_RASPBIAN = "\n".join([
    "   `.::///+:/-.        --///+//-:`` ",
    "  `+oooooooooooo:   `+oooooooooooo:",
    "   /oooo++//ooooo:  ooooo+//+ooooo.",
    "   `+ooooooo:-:oo-  +o+:ooooooo:/  ",
    "    `:oooooooo+``    `.oooooooo+-   ",
    "      `:++ooo/.        :+ooo+/.`   ",
    "         ...`  `.        `. `.``    ",
    "  .:::::::...  .:.      .:. .::::. ",
    " -::::::::::...      .:..      .-::::::::::",
    " -::::::::::::.      .::.       :::::::::::",
    "  .::::::::::.       .::.        ::::::::::",
    "    `...::::..`      `::..       ::::::..`  ",
    "        ...       `:.       `             ",
])

# ---- EndeavourOS ----
_ENDEAVOUROS = "\n".join([
    "                     ./o.           ",
    "                   ./sssso-         ",
    "                 `:osssssss+-       ",
    "               `:+sssssssssso/.    ",
    "             `-/ossssssssssssso/.   ",
    "           `-/+sssssssssssssssso+:`",
    "         `-:/+sssssssssssssssssso+/.",
    "       `.://osssssssssssssssssssso++-",
    "      .://+ssssssssssssssssssssssso++:",
    "    .:///ossssssssssssssssssssssssso++:",
    "   :////ssssssssssssssssssssssssssso+++.",
    " `/////ssssssssssssssssssssssssssssso+++",
    "`/////sssssssssssssssssssssssssssssso+++.",
    "://///ssssssssssssssssssssssssssssssso+++",
])

# ---- Windows ----
_WINDOWS = "\n".join([
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "                                    ",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
    "  ################  ################",
])

# ---- macOS ----
_MACOS = "\n".join([
    "                 'c.                ",
    "                ,xNMM.             ",
    "              .OMMMMo              ",
    "              OMMM0,               ",
    "    .;loddo:' loolloddol;.         ",
    "  cKMMMMMMMMMMNWMMMMMMMMMM0:       ",
    " .KMMMMMMMMMMMMMMMMMMMMMMMWd.      ",
    " XMMMMMMMMMMMMMMMMMMMMMMMX.        ",
    ";MMMMMMMMMMMMMMMMMMMMMMMM:         ",
    ":MMMMMMMMMMMMMMMMMMMMMMMM:         ",
    ".MMMMMMMMMMMMMMMMMMMMMMMMX.        ",
    " kMMMMMMMMMMMMMMMMMMMMMMMMWd.      ",
    " .XMMMMMMMMMMMMMMMMMMMMMMMMk       ",
    "  .XMMMMMMMMMMMMMMMMMMMMK.         ",
    "    kMMMMMMMMMMMMMMMMMMd.           ",
    "     ;KMMMMMMMWXXWMMMk.            ",
    "       .cooc,.    .,coo.           ",
])

# ---- Generic Linux (Tux) ----
_LINUX = "\n".join([
    "        .-/+oossssoo+/-.           ",
    "    `:+sssssssssssssssssss+:`      ",
    "  -+sssssssssssssssssssssssss+-    ",
    " .ossssssssssssssssssssssssssso.   ",
    "+sssssssssssss/-`` .-/sssssssssss+ ",
    "ossssssssssss:      :sssssssssssso ",
    "osssss:+ssss:        :ssss+:sssss+ ",
    "osssss. .+s:    .-    :+s. .sssss+ ",
    "osssss.   .   .:ss:.   .   .sssss+ ",
    "+sssss+:....:+sssss+:....:+ssssss+ ",
    "`ossssssssssssssssssssssssssssssso` ",
    "  /sssssssssssssssssssssssssssss/   ",
    "   `+ssssssssssssssssssssssssss/`   ",
    "     -+sssssssssssssssssssssss+-    ",
    "       `:+ssssssssssssssssss+:`     ",
    "          .-/+oossssoo+/-.          ",
])

# ---- Unknown / fallback ----
_UNKNOWN = "\n".join([
    "      +------------------+         ",
    "      |                  |         ",
    "      |     SYSOPS       |         ",
    "      |                  |         ",
    "      |     System       |         ",
    "      |     Info         |         ",
    "      |                  |         ",
    "      +------------------+         ",
])


# ---------------------------------------------------------------------------
# Distro -> logo mapping
# ---------------------------------------------------------------------------
_LOGO_MAP: dict[str, str] = {
    "arch":         _ARCH,
    "ubuntu":       _UBUNTU,
    "debian":       _DEBIAN,
    "fedora":       _FEDORA,
    "opensuse":     _OPENSUSE,
    "centos":       _OPENSUSE,  # similar family
    "manjaro":      _MANJARO,
    "mint":         _MINT,
    "linuxmint":    _MINT,
    "pop":          _POP,
    "elementary":   _MINT,      # similar family
    "gentoo":       _GENTOO,
    "void":         _VOID,
    "alpine":       _ALPINE,
    "nixos":        _NIXOS,
    "kali":         _KALI,
    "raspbian":     _RASPBIAN,
    "endeavouros":  _ENDEAVOUROS,
    "artix":        _ARCH,      # Arch-based
    "slackware":    _LINUX,
    "rhel":         _FEDORA,    # Red Hat family
    "rocky":        _FEDORA,
    "alma":         _FEDORA,
    "linux":        _LINUX,
    "windows":      _WINDOWS,
    "macos":        _MACOS,
    "darwin":       _MACOS,
    "unknown":      _UNKNOWN,
}


def list_supported_distros() -> list[str]:
    """Return a sorted list of supported distro identifiers."""
    return sorted(_LOGO_MAP.keys())


def get_logo(distro_id: str) -> str:
    """Return the padded ASCII logo for *distro_id* (case-insensitive, fuzzy).

    Falls back to the generic Linux or unknown logo when the distro is
    not explicitly supported.
    """
    key = distro_id.lower().replace(" ", "").replace("_", "").replace("-", "")
    # Exact match
    if key in _LOGO_MAP:
        return _pad_logo(_LOGO_MAP[key])
    # Substring match
    for name, art in _LOGO_MAP.items():
        if name in key or key in name:
            return _pad_logo(art)
    # Default fallback
    return _pad_logo(_LOGO_MAP.get("linux", _UNKNOWN))


def colorize_logo(logo: str, distro_id: str) -> str:
    """Apply the distro brand colours to every line of *logo*.

    Alternates between primary and secondary colour per line to give
    visual depth (matching the neofetch convention).
    """
    primary_sgr, secondary_sgr = get_logo_colors(distro_id)
    lines = logo.splitlines()
    coloured: list[str] = []
    for i, line in enumerate(lines):
        sgr = primary_sgr if i % 2 == 0 else secondary_sgr
        coloured.append(f"{_color(sgr)}{line}{RESET}")
    return "\n".join(coloured)
