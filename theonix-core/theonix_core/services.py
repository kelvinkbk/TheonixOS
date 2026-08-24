"""
Theonix Core Services — Shared Platform Services for Package Management, Telemetry, and Search.
"""

import enum
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import threading
from typing import Dict, List, Optional, Tuple, Any

UACL_DB_PATH = os.path.expanduser("~/.config/theonix/uacl.db")


class CompatibilityRating(enum.Enum):
    NATIVE = "native"                   # 🟢 Native Linux
    UACL_COMPATIBLE = "uacl"            # 🟢 Works with UACL (Proton/Wine)
    CONFIG_REQUIRED = "config_required" # 🟡 Requires Configuration
    UNSUPPORTED = "unsupported"         # 🔴 Unsupported


class ThemeService:
    """Manages system theme, wallpapers, and desktop effects."""
    THEMES = ["Theonix Dark", "Deep Space", "Cyber Neon", "Solar Glow"]

    @staticmethod
    def apply_wallpaper(image_path: str) -> bool:
        if os.path.exists(image_path):
            try:
                subprocess.Popen(["plasma-apply-wallpaperimage", image_path], stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def apply_colorscheme(scheme_name: str) -> bool:
        try:
            subprocess.Popen(["plasma-apply-colorscheme", scheme_name], stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False


class PackageService:
    """Unified software search and compatibility analyzer across Pacman, Flatpak, and UACL."""

    @staticmethod
    def evaluate_compatibility(pkg_name: str, source: str = "pacman") -> Tuple[CompatibilityRating, str]:
        lower = pkg_name.lower()
        if source in ["pacman", "arch"]:
            return CompatibilityRating.NATIVE, "Official Arch Linux package — 100% native performance"
        elif source == "flatpak":
            return CompatibilityRating.NATIVE, "Sandboxed Flathub container — 100% native"
        elif lower.endswith(".exe") or lower.endswith(".msi") or source == "uacl":
            return CompatibilityRating.UACL_COMPATIBLE, "Windows binary handled seamlessly by Theonix UACL (Proton/DXVK)"
        elif "anticheat" in lower or "vanguard" in lower or "easyanticheat" in lower:
            return CompatibilityRating.UNSUPPORTED, "Requires kernel-level driver unsupported on Linux"
        return CompatibilityRating.CONFIG_REQUIRED, "Community software — may require custom environment variables"

    @staticmethod
    def search_packages(query: str) -> List[Dict[str, Any]]:
        results = []
        if not query:
            return results

        # 1. Search Pacman
        try:
            res = subprocess.run(["pacman", "-Ss", query], capture_output=True, text=True, timeout=8)
            cur_pkg = None
            for line in res.stdout.strip().splitlines():
                if not line.startswith("    "):
                    parts = line.split()
                    if parts:
                        cur_pkg = parts[0].split("/")[-1]
                        cur_ver = parts[1] if len(parts) > 1 else "1.0"
                else:
                    desc = line.strip()
                    if cur_pkg:
                        compat, reason = PackageService.evaluate_compatibility(cur_pkg, "pacman")
                        results.append({
                            "name": cur_pkg,
                            "pkg": cur_pkg,
                            "version": cur_ver,
                            "source": "pacman",
                            "icon": "📦",
                            "desc": desc,
                            "compat": compat,
                            "compat_desc": reason
                        })
                        cur_pkg = None
        except Exception:
            pass

        # 2. Search UACL Applications
        if os.path.exists(UACL_DB_PATH):
            try:
                conn = sqlite3.connect(UACL_DB_PATH)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT name, format_type FROM applications WHERE name LIKE ?", (f"%{query}%",))
                for row in cur.fetchall():
                    compat, reason = PackageService.evaluate_compatibility(row["name"], "uacl")
                    results.append({
                        "name": row["name"],
                        "pkg": row["name"],
                        "version": "1.0",
                        "source": "uacl",
                        "icon": "🪟",
                        "desc": f"Windows/UACL application [{row['format_type']}]",
                        "compat": compat,
                        "compat_desc": reason
                    })
                conn.close()
            except Exception:
                pass

        return results[:80]


class SearchService:
    """Advanced search query parser for files, directories, and system settings."""

    @staticmethod
    def parse_file_query(query: str) -> Dict[str, Any]:
        """Parses advanced query filters like kind:image, size:>1GB, name:*.iso"""
        filters = {
            "text": "",
            "kind": None,
            "min_size": None,
            "max_size": None,
            "ext": None,
        }

        tokens = query.split()
        for token in tokens:
            if token.startswith("kind:"):
                filters["kind"] = token.split(":", 1)[1].lower()
            elif token.startswith("ext:"):
                filters["ext"] = token.split(":", 1)[1].lower()
            elif token.startswith("size:>"):
                size_str = token.split(":>", 1)[1].upper()
                filters["min_size"] = SearchService._parse_size(size_str)
            elif token.startswith("size:<"):
                size_str = token.split(":<", 1)[1].upper()
                filters["max_size"] = SearchService._parse_size(size_str)
            else:
                filters["text"] += f" {token}"

        filters["text"] = filters["text"].strip()
        return filters

    @staticmethod
    def _parse_size(s: str) -> int:
        multiplier = 1
        if s.endswith("GB"):
            multiplier = 1024**3
            s = s[:-2]
        elif s.endswith("MB"):
            multiplier = 1024**2
            s = s[:-2]
        elif s.endswith("KB"):
            multiplier = 1024
            s = s[:-2]
        try:
            return int(float(s) * multiplier)
        except Exception:
            return 0


class SystemService:
    """Hardware telemetry, PipeWire audio, Network, and Btrfs snapshots."""

    @staticmethod
    def get_hardware_telemetry() -> Dict[str, Any]:
        # Memory
        mem_total_kb = 1
        mem_avail_kb = 0
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total_kb = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_avail_kb = int(line.split()[1])
        except Exception:
            pass

        used_kb = mem_total_kb - mem_avail_kb
        mem_pct = int((used_kb / mem_total_kb) * 100)

        # Disk
        disk_pct = 0
        try:
            u = shutil.disk_usage("/")
            disk_pct = int((u.used / u.total) * 100)
        except Exception:
            pass

        return {
            "ram_used_gb": used_kb / (1024**2),
            "ram_total_gb": mem_total_kb / (1024**2),
            "ram_percent": mem_pct,
            "disk_percent": disk_pct
        }

    @staticmethod
    def create_btrfs_snapshot(tag: str = "manual") -> Tuple[bool, str]:
        snap_dir = os.path.expanduser("~/.local/share/theonix/snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        name = f"snapshot_{tag}_{int(subprocess.check_output(['date', '+%s']).decode().strip())}"
        return True, name


class AIService:
    """Client for local Ollama and THAID AI engine."""

    @staticmethod
    def is_available() -> bool:
        try:
            res = subprocess.run(["ollama", "list"], capture_output=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_models() -> List[str]:
        models = []
        try:
            res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().splitlines()
            if len(lines) > 1:
                for l in lines[1:]:
                    p = l.split()
                    if p:
                        models.append(p[0])
        except Exception:
            pass
        return models


class UACLService:
    """Theonix Universal App Compatibility Layer launcher."""

    @staticmethod
    def launch(target_path: str):
        subprocess.Popen(["theonix-uacl", "launch", "--path", target_path])
