"""
Theonix Core Services — Shared Platform Services for Package Management, Telemetry, and Search.
"""

import enum
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.request
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
    """
    High-Performance Local AI Service for Theonix OS.
    Integrates directly with local Qwen GGUF models via llamafile / llama-server
    with OpenAI-compatible streaming API on http://127.0.0.1:8080.
    """

    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8080
    API_URL = f"http://127.0.0.1:{LOCAL_PORT}/v1/chat/completions"

    MODEL_PATHS = [
        os.path.expanduser("/home/k/Desktop/local ai"),
        os.path.expanduser("~/.local/share/theonix/models"),
        "/usr/share/theonix/models",
    ]

    @classmethod
    def _find_binary_and_model(cls, model_id: str = "1.5b") -> Tuple[Optional[str], Optional[str]]:
        bin_path = None
        model_filename = "Qwen2.5-Coder-1.5B-Q4_K_M.gguf" if model_id == "1.5b" else "Qwen3.5-4B-Q4_0.gguf"
        model_path = None

        for base in cls.MODEL_PATHS:
            if not os.path.exists(base):
                continue
            # Look for llamafile executable
            for cand_bin in ["llamafile.exe", "llamafile", "llama-server"]:
                p = os.path.join(base, cand_bin)
                if os.path.exists(p) and not bin_path:
                    bin_path = p
            # Look for model
            cand_m1 = os.path.join(base, "models", model_filename)
            cand_m2 = os.path.join(base, model_filename)
            if os.path.exists(cand_m1):
                model_path = cand_m1
            elif os.path.exists(cand_m2):
                model_path = cand_m2

        return bin_path, model_path

    @classmethod
    def is_server_running(cls) -> bool:
        try:
            req = urllib.request.Request(f"http://{cls.LOCAL_HOST}:{cls.LOCAL_PORT}/v1/models", headers={"User-Agent": "TheonixOS"})
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def is_available(cls) -> bool:
        if cls.is_server_running():
            return True
        bin_p, mod_p = cls._find_binary_and_model()
        if bin_p and mod_p:
            return True
        try:
            res = subprocess.run(["ollama", "list"], capture_output=True, timeout=1)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def ensure_server_running(cls, model_id: str = "1.5b") -> bool:
        """Starts the local llamafile/Qwen server in background if not already active."""
        if cls.is_server_running():
            return True

        bin_path, model_path = cls._find_binary_and_model(model_id)
        if not bin_path or not model_path:
            return False

        ctx_size = 8192 if model_id == "1.5b" else 16384
        cmd = [
            "sh", bin_path,
            "--server",
            "--host", cls.LOCAL_HOST,
            "--port", str(cls.LOCAL_PORT),
            "-m", model_path,
            "-c", str(ctx_size),
            "-ngl", "999"
        ]

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            # Poll for up to 8 seconds for server to be ready
            for _ in range(16):
                time.sleep(0.5)
                if cls.is_server_running():
                    return True
        except Exception:
            pass

        return False

    @classmethod
    def stream_chat(cls, messages: List[Dict[str, str]], model_id: str = "1.5b", system_prompt: Optional[str] = None):
        """
        Yields tokens in real-time from the local high-speed AI engine.
        Falls back to Ollama or simple response if server is unlaunchable.
        """
        if not cls.is_server_running():
            cls.ensure_server_running(model_id)

        all_msgs = []
        if system_prompt:
            all_msgs.append({"role": "system", "content": system_prompt})
        all_msgs.extend(messages)

        if cls.is_server_running():
            payload = json.dumps({
                "messages": all_msgs,
                "stream": True,
                "temperature": 0.6,
                "max_tokens": 4096
            }).encode("utf-8")

            req = urllib.request.Request(
                cls.API_URL,
                data=payload,
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    for raw_line in resp:
                        line = raw_line.decode("utf-8").strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_str)
                            choices = chunk_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except Exception:
                            continue
                return
            except Exception as e:
                yield f"\n[AI Stream Error: {e}]\n"
                return

        # Fallback to Ollama if local llamafile is unavailable
        try:
            last_prompt = messages[-1]["content"] if messages else ""
            p = subprocess.Popen(
                ["ollama", "run", "llama3.2:1b", last_prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            for line in p.stdout:
                yield line
            p.wait()
        except Exception:
            yield "\n[THAID Local AI engine is starting or not configured. Place Qwen GGUF models in /home/k/Desktop/local ai/]\n"

    @classmethod
    def get_models(cls) -> List[Dict[str, str]]:
        return [
            {"id": "1.5b", "name": "⚡ Qwen 2.5-Coder 1.5B (Ultra-Fast Coder)"},
            {"id": "4b", "name": "🧠 Qwen 3.5 4B (High Quality Reasoning)"}
        ]


class UACLService:
    """Theonix Universal App Compatibility Layer launcher."""

    @staticmethod
    def launch(target_path: str):
        subprocess.Popen(["theonix-uacl", "launch", "--path", target_path])

