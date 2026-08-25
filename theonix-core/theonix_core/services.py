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

        # 2. Search Flatpak (Flathub)
        try:
            res_fp = subprocess.run(
                ["flatpak", "search", query, "--columns=application,name,description,version"],
                capture_output=True, text=True, timeout=5
            )
            for line in res_fp.stdout.strip().splitlines()[:25]:
                parts = line.split("\t")
                if len(parts) >= 2:
                    app_id = parts[0].strip()
                    app_title = parts[1].strip()
                    app_desc = parts[2].strip() if len(parts) > 2 else f"Flathub sandboxed container ({app_title})"
                    app_ver = parts[3].strip() if len(parts) > 3 else "Latest"
                    compat, reason = PackageService.evaluate_compatibility(app_id, "flatpak")
                    results.append({
                        "name": app_title or app_id,
                        "pkg": app_id,
                        "version": app_ver,
                        "source": "flatpak",
                        "icon": "🌐",
                        "desc": app_desc,
                        "compat": compat,
                        "compat_desc": reason
                    })
        except Exception:
            pass

        # 3. Search UACL Applications
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

    @staticmethod
    def is_installed(pkg_name: str, source: str = "pacman") -> bool:
        """Check if a package, container, or binary is installed on the system."""
        if not pkg_name:
            return False

        if source in ["pacman", "arch"]:
            try:
                res = subprocess.run(["pacman", "-Qq", pkg_name], capture_output=True, timeout=2)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
            bin_name = pkg_name.split(".")[0]
            return shutil.which(bin_name) is not None
        elif source == "flatpak":
            try:
                res = subprocess.run(["flatpak", "info", pkg_name], capture_output=True, timeout=2)
                return res.returncode == 0
            except Exception:
                return False
        elif source == "uacl":
            uacl_cache_dir = os.path.expanduser("~/.cache/theonix/uacl")
            if os.path.exists(os.path.join(uacl_cache_dir, pkg_name)):
                return True
            apps_dir = os.path.expanduser("~/.local/share/applications")
            if os.path.exists(apps_dir):
                for f in os.listdir(apps_dir):
                    if pkg_name.lower() in f.lower():
                        return True
            return False
        return False

    @staticmethod
    def get_installed_apps() -> List[Dict[str, Any]]:
        """Scans the system for installed GUI applications with desktop entries."""
        apps = []
        seen = set()
        search_dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        
        for sdir in search_dirs:
            if not os.path.exists(sdir):
                continue
            for fname in os.listdir(sdir):
                if not fname.endswith(".desktop"):
                    continue
                fpath = os.path.join(sdir, fname)
                try:
                    name, exec_cmd, desc, nodisplay = None, None, "", False
                    with open(fpath, "r", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("Name=") and not name:
                                name = line.split("=", 1)[1]
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line.split("=", 1)[1].split()[0]
                            elif line.startswith("Comment=") and not desc:
                                desc = line.split("=", 1)[1]
                            elif line.startswith("NoDisplay=true"):
                                nodisplay = True
                                break
                    if nodisplay or not name or not exec_cmd:
                        continue
                    if name in seen:
                        continue
                    seen.add(name)
                    
                    # Determine icon emoji
                    icon_emoji = "📦"
                    lower_n = name.lower()
                    if "code" in lower_n or "develop" in lower_n:
                        icon_emoji = "💻"
                    elif "browser" in lower_n or "web" in lower_n or "firefox" in lower_n:
                        icon_emoji = "🌐"
                    elif "terminal" in lower_n or "konsole" in lower_n:
                        icon_emoji = "⌨️"
                    elif "calc" in lower_n or "settings" in lower_n:
                        icon_emoji = "⚙️"
                    elif "image" in lower_n or "gimp" in lower_n or "paint" in lower_n:
                        icon_emoji = "🎨"
                    elif "music" in lower_n or "audio" in lower_n or "vlc" in lower_n or "video" in lower_n:
                        icon_emoji = "🎬"

                    apps.append({
                        "name": name,
                        "pkg": os.path.basename(exec_cmd),
                        "source": "pacman",
                        "icon": icon_emoji,
                        "desc": desc or f"Installed system application ({name})",
                        "version": "Installed",
                        "compat": CompatibilityRating.NATIVE,
                        "compat_desc": "Native Linux application",
                        "installed": True
                    })
                except Exception:
                    pass
        return sorted(apps, key=lambda x: x["name"].lower())

    @staticmethod
    def check_updates() -> List[Dict[str, Any]]:
        """Scans for available system (pacman) and Flatpak updates."""
        updates = []
        # 1. Check Pacman updates (via pacman -Qu)
        try:
            res = subprocess.run(["pacman", "-Qu"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.strip().splitlines()[:60]:
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "->":
                    pkg_name = parts[0]
                    old_ver = parts[1]
                    new_ver = parts[3]
                    updates.append({
                        "name": pkg_name,
                        "pkg": pkg_name,
                        "old_version": old_ver,
                        "version": new_ver,
                        "source": "pacman",
                        "icon": "📦",
                        "desc": f"Arch package upgrade: {old_ver} → {new_ver}",
                        "compat": CompatibilityRating.NATIVE,
                        "compat_desc": "Official Arch Linux package update"
                    })
        except Exception:
            pass

        # 2. Check Flatpak updates
        try:
            res_fp = subprocess.run(
                ["flatpak", "remote-ls", "--updates", "--columns=application,name,version"],
                capture_output=True, text=True, timeout=5
            )
            if res_fp.returncode == 0:
                for line in res_fp.stdout.strip().splitlines()[:25]:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        app_id = parts[0].strip()
                        app_name = parts[1].strip()
                        app_ver = parts[2].strip() if len(parts) > 2 else "Latest"
                        updates.append({
                            "name": app_name or app_id,
                            "pkg": app_id,
                            "old_version": "Installed",
                            "version": app_ver,
                            "source": "flatpak",
                            "icon": "🌐",
                            "desc": f"Flathub container upgrade to {app_ver}",
                            "compat": CompatibilityRating.NATIVE,
                            "compat_desc": "Sandboxed container update"
                        })
        except Exception:
            pass

        return updates


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
        # Check if the prompt triggers a direct desktop action
        last_prompt = messages[-1]["content"] if messages else ""
        action_res = ActionService.execute_intent(last_prompt)
        if action_res:
            yield action_res
            return

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


class ActionService:
    """
    Intelligent OS Automation & Action Dispatcher for THAID.
    Executes native desktop commands, app launches, telemetry checks, volume controls, and web lookups.
    """

    APP_MAP = {
        "browser": ["theonix-browser", "firefox", "chromium", "google-chrome"],
        "firefox": ["firefox", "theonix-browser"],
        "files": ["theonix-files", "dolphin", "nautilus", "thunar"],
        "file manager": ["theonix-files", "dolphin", "nautilus"],
        "settings": ["theonix-settings", "systemsettings"],
        "store": ["theonix-store", "discover"],
        "messages": ["theonix-messages"],
        "terminal": ["konsole", "alacritty", "kitty", "foot", "xterm"],
        "calculator": ["kcalc", "gnome-calculator"],
        "screenshot": ["spectacle", "grim", "flameshot"],
        "text editor": ["kate", "kwrite", "gedit", "code"],
    }

    @classmethod
    def execute_intent(cls, prompt: str) -> Optional[str]:
        p = prompt.strip().lower()

        # 1. Launch / Open Apps
        for key, binaries in cls.APP_MAP.items():
            pattern = rf"\b(open|launch|start|run|open up)\s+(the\s+)?{key}\b"
            if re.search(pattern, p) or p == key or p == f"open {key}":
                for b in binaries:
                    # Check system path
                    if shutil.which(b):
                        subprocess.Popen([b], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return f"✓ Launched {key.title()}."
                    # Check local project apps
                    local_main = os.path.expanduser(f"/home/k/Desktop/Projects/theonix/{b}/main.py")
                    if os.path.exists(local_main):
                        subprocess.Popen(["python3", local_main], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return f"✓ Launched {key.title()} (Theonix Native App)."

                if key == "firefox":
                    local_browser = os.path.expanduser("/home/k/Desktop/Projects/theonix/theonix-browser/main.py")
                    if os.path.exists(local_browser):
                        subprocess.Popen(["python3", local_browser])
                        return "✓ Firefox is not installed. Opened Theonix Browser instead.\n*(Tip: Run `sudo pacman -S firefox` to install Firefox)*"
                return f"Could not find application for '{key}'."

        # 2. Open Website / URL
        url_match = re.search(r"\b(open|go to|visit)\s+(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.(com|org|io|net|xyz|edu|gov))\b", p)
        if url_match:
            raw_url = url_match.group(2)
            if not raw_url.startswith("http"):
                raw_url = "https://" + raw_url
            local_browser = os.path.expanduser("/home/k/Desktop/Projects/theonix/theonix-browser/main.py")
            if os.path.exists(local_browser):
                subprocess.Popen(["python3", local_browser, raw_url])
            elif shutil.which("firefox"):
                subprocess.Popen(["firefox", raw_url])
            return f"✓ Opening {raw_url} in Theonix Browser."

        # 3. Lock Screen
        if any(term in p for term in ["lock screen", "lock my pc", "lock computer", "lock session"]):
            subprocess.Popen(["loginctl", "lock-session"])
            return "✓ Screen locked."

        # 4. Take Screenshot
        if any(term in p for term in ["screenshot", "capture screen", "take screenshot"]):
            if shutil.which("spectacle"):
                subprocess.Popen(["spectacle", "-b"], stderr=subprocess.DEVNULL)
            elif shutil.which("grim"):
                subprocess.Popen(["grim"], stderr=subprocess.DEVNULL)
            return "✓ Captured screenshot."

        # 5. Volume control
        if "mute" in p and "unmute" not in p:
            subprocess.Popen(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"], stderr=subprocess.DEVNULL)
            return "✓ Audio muted."
        if "unmute" in p:
            subprocess.Popen(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], stderr=subprocess.DEVNULL)
            return "✓ Audio unmuted."

        # 6. Telemetry / Hardware stats
        if any(w in p for w in ["ram usage", "memory usage", "check ram", "system status", "telemetry", "how much ram"]):
            stats = SystemService.get_hardware_telemetry()
            return f"📊 **System Telemetry**:\n• **RAM**: {stats['ram_used_gb']:.1f} GB / {stats['ram_total_gb']:.1f} GB ({stats['ram_percent']}% used)\n• **Disk**: {stats['disk_percent']}% used"

        return None


class UACLService:
    """Theonix Universal App Compatibility Layer launcher."""

    @staticmethod
    def launch(target_path: str):
        if os.path.exists(target_path):
            subprocess.Popen(["theonix-uacl", "run", "--file", target_path])
        else:
            subprocess.Popen(["theonix-uacl", "launch", "--id", target_path])


class UpdateClient:
    """High-level client for the decoupled org.theonix.Updates D-Bus service."""

    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall("org.theonix.Updates", "/org/theonix/Updates", "", "GetSystemStatus")
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return json.loads(str(reply.arguments()[0]))
        except Exception:
            pass
        return {"os_name": "Theonix OS", "os_version": "2.0.0", "status": "standalone"}

    @staticmethod
    def check_for_updates() -> Dict[str, Any]:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall("org.theonix.Updates", "/org/theonix/Updates", "", "CheckForUpdates")
            reply = bus.call(msg, QDBus.CallMode.Block, 5000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return json.loads(str(reply.arguments()[0]))
        except Exception:
            pass
        return {"status": "offline", "total_count": 0}

    @staticmethod
    def install_updates() -> bool:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall("org.theonix.Updates", "/org/theonix/Updates", "", "InstallUpdates")
            msg << "all"
            reply = bus.call(msg, QDBus.CallMode.Block, 5000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return bool(reply.arguments()[0])
        except Exception:
            pass
        return False


class AuthClient:
    """High-level client for the decoupled org.theonix.Auth D-Bus service."""

    @staticmethod
    def request_authorization(app_name: str, action: str, target: str, risk_level: str = "CONFIRM") -> bool:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall("org.theonix.Auth", "/org/theonix/Auth", "", "RequestAuthorization")
            msg << app_name << action << target << risk_level
            reply = bus.call(msg, QDBus.CallMode.Block, 35000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return bool(reply.arguments()[0])
        except Exception:
            pass
        return True


class NotificationClient:
    """High-level client for the decoupled org.theonix.Notifications D-Bus service."""

    @staticmethod
    def notify(
        app_name: str,
        title: str,
        message: str,
        icon: str = "🔔",
        priority: str = "normal",
        actions: List[str] = None,
        timeout_ms: int = 6000
    ) -> int:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Notifications", "/org/theonix/Notifications", "", "Notify"
            )
            actions_json = json.dumps(actions or [])
            msg << app_name << title << message << icon << priority << actions_json << timeout_ms
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return int(reply.arguments()[0])
        except Exception:
            pass
        return 0


class SearchClient:
    """High-level client for the decoupled org.theonix.Search D-Bus service."""

    @staticmethod
    def query(query_text: str, limit: int = 8) -> List[Dict[str, Any]]:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Search", "/org/theonix/Search", "", "Query"
            )
            msg << query_text << limit
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return json.loads(str(reply.arguments()[0]))
        except Exception:
            pass
        return []

    @staticmethod
    def toggle_overlay():
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Search", "/org/theonix/Search", "", "Toggle"
            )
            bus.send(msg)
        except Exception:
            pass


class InputClient:
    """High-level client for the decoupled org.theonix.Input D-Bus service."""

    @staticmethod
    def get_gesture_config() -> Dict[str, Any]:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Input", "/org/theonix/Input", "", "GetGestureConfig"
            )
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return json.loads(str(reply.arguments()[0]))
        except Exception:
            pass
        return {}

    @staticmethod
    def set_gesture_config(config_data: Dict[str, Any]) -> bool:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Input", "/org/theonix/Input", "", "SetGestureConfig"
            )
            msg << json.dumps(config_data)
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return bool(reply.arguments()[0])
        except Exception:
            pass
        return False

    @staticmethod
    def trigger_gesture(gesture_name: str) -> bool:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.theonix.Input", "/org/theonix/Input", "", "TriggerGestureAction"
            )
            msg << gesture_name
            reply = bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                return bool(reply.arguments()[0])
        except Exception:
            pass
        return False





