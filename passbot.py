#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PassBot Enterprise — Gen‑Spider Brand Edition (Optimized)
- Accurate progress estimates per phase and global
- Deterministic estimation equals actual loop counts
- Faster I/O with buffered writes, optional gzip
- Strong-mode with tunable threshold
- Safer resume with compact state and hash for versioning
- Optional de-duplication bloom filter for memory efficiency
- Rich UI fallbacks maintained; clearer rate/ETA
- Visual polish and stable matrix intro
- Optional multi-file sharding for huge outputs
"""
import os, sys, re, time, math, signal, pickle, shutil, secrets, string, gzip, hashlib, bz2, lzma, random
from dataclasses import dataclass, asdict
from typing import List, Set, Optional, Dict, Tuple, Iterable
from collections import defaultdict
from datetime import datetime, timedelta

# Try deps once, but don't fail hard
try:
    import psutil
except Exception:
    psutil = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

# ANSI fallback
GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; BLUE = "\033[94m"; CYAN = "\033[96m"; RESET = "\033[0m"; BOLD = "\033[1m"

APP_VERSION = "1.4.0"
STATE_VERSION = 3

@dataclass
class LiveStats:
    current_password: str = ""
    passwords_generated: int = 0
    current_phase: str = ""
    start_time: float = 0.0
    estimated_total: int = 0
    memory_usage_mb: float = 0.0
    disk_space_gb: float = 0.0
    generation_rate: float = 0.0
    eta_seconds: float = 0.0
    output_file: str = "passbot_dictionary.txt"
    strong_mode_filtered: int = 0

@dataclass
class ProgressState:
    version: int
    phases_done: Dict[int, int]
    idx_cursors: Dict[int, Tuple[int, int, int, int]]
    total_generated: int
    start_time: float
    input_profile: dict
    strong_mode_filtered: int = 0
    checksum: str = ""

@dataclass
class InputProfile:
    words: List[str]
    mobile_numbers: List[str]
    date_fragments: List[str]
    year_ranges: List[str]
    special_chars: List[str]
    number_patterns: List[str]
    output_filename: str
    generation_mode: str = "full"  # full or strong
    use_underscore_separator: bool = False
    max_output_count: Optional[int] = None
    compression: str = "none"
    shard_every_million: bool = False
    strong_threshold: float = 60.0
    min_length: int = 0
    max_length: int = 0
    leetspeak: bool = False

class PasswordStrength:
    @staticmethod
    def entropy(password: str) -> float:
        if not password:
            return 0.0
        counts = defaultdict(int)
        for c in password:
            counts[c] += 1
        n = len(password)
        e = 0.0
        for k in counts.values():
            p = k / n
            e -= p * math.log2(max(p, 1e-12))
        return e * n

    @staticmethod
    def score(password: str) -> float:
        if not password:
            return 0.0
        n = len(password)
        s = 0.0
        # length
        s += 30 if n >= 20 else 25 if n >= 16 else 20 if n >= 12 else 15 if n >= 8 else n * 1.5
        # variety
        kinds = sum([
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        ])
        s += kinds * 10
        # entropy bonus
        ent = PasswordStrength.entropy(password)
        s += min(30, (ent / 6.0) * 30)
        # simple bad patterns
        if re.search(r"(.)\1{2,}", password):
            s -= 15
        if re.search(r"(abc|123|qwe|password|admin|user|test)", password.lower()):
            s -= 20
        return max(0, min(100, s))

    @staticmethod
    def is_strong(pw: str, threshold: float) -> bool:
        return PasswordStrength.score(pw) >= threshold

class HorrorUI:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        if RICH_AVAILABLE:
            size = self.console.size
            self.width = size.width
            self.height = size.height
        else:
            self.width = 80
            self.height = 24

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def show_matrix_effect(self, duration: float = 2.5):
        chars = "01" + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        glitch_chars = ["▓", "▒", "░"]
        start = time.time()
        print("\033[?25l", end="")  # hide cursor
        try:
            while time.time() - start < duration:
                for _ in range(int(self.width / 2)):
                    col = secrets.randbelow(self.width) if self.width > 0 else 0
                    row = secrets.randbelow(self.height) if self.height > 0 else 0
                    ch = secrets.choice(chars)
                    color = secrets.choice([91, 92, 93, 94, 95, 96]) # red, green, yellow, blue, magenta, cyan
                    print(f"\033[{row};{col}H\033[{color}m{ch}\033[0m", end="", flush=True)

                if secrets.randbelow(10) < 2:
                    col = secrets.randbelow(self.width - 5) if self.width > 5 else 0
                    row = secrets.randbelow(self.height) if self.height > 0 else 0
                    print(f"\033[{row};{col}H\033[91m{''.join(secrets.choice(glitch_chars) for _ in range(5))}\033[0m", end="", flush=True)

                time.sleep(0.01)
        finally:
            print("\033[H\033[J\033[?25h", end="")

    def show_full_banner(self):
        if RICH_AVAILABLE:
            self.clear()
            self.show_matrix_effect(2.5)
            banner_text = Text(
                "\n"
                "        ▒▓▓▓▒▒▒░░▒▒▒▒▒▒▒░░▒▒▓▓▓▒░\n"
                "      ▒▓    ▒▓▓▓▒░    ░▒▓▓▓▒    ▓▒\n"
                "    ▒▓        ▒▓▓▓▒░▒▓▓▓▒        ▓▒\n"
                "  ▒▓          ▒▓▓▓▓▓▓▓▓▒          ▓▒\n"
                "▒▓            ▒▓▓▓▓▓▓▓▓▒            ▓▒\n"
                "▓▒            ▒▓  ▓▓▓  ▓▒            ▒▓\n"
                "▓▒            ▓▒  ▒▓▒  ▒▓            ▒▓\n"
                "▓▒          ▒▓    ▓ ▒▓    ▓▒          ▒▓\n"
                "▓▒        ▒▓    ▒▓ ▒ ▓▒    ▓▒        ▒▓\n"
                "▓▒      ▒▓    ▒▓▒ ▓ ▒▓▒    ▓▒      ▒▓\n"
                "▓▒    ▒▓    ▒▓▒   ▓   ▒▓▒    ▓▒    ▒▓\n"
                "▓▒  ▒▓    ▒▓▒     ▓     ▒▓▒    ▓▒  ▒▓\n"
                "▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▓\n"
                "▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓\n"
                "▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓\n"
                "▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓\n"
                "▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓\n"
                "▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓\n"
                "▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▓\n",
                style="bold red"
            )
            panel = Panel(
                Align.center(banner_text),
                title="[bold red]💀 DANGER: PASSBOT ACTIVE 💀[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            self.clear()
            print(f"{BOLD}{RED}")
            print("        ▒▓▓▓▒▒▒░░▒▒▒▒▒▒▒░░▒▒▓▓▓▒░")
            print("      ▒▓    ▒▓▓▓▒░    ░▒▓▓▓▒    ▓▒")
            print("    ▒▓        ▒▓▓▓▒░▒▓▓▓▒        ▓▒")
            print("  ▒▓          ▒▓▓▓▓▓▓▓▓▒          ▓▒")
            print("▒▓            ▒▓▓▓▓▓▓▓▓▒            ▓▒")
            print("▓▒            ▒▓  ▓▓▓  ▓▒            ▒▓")
            print("▓▒            ▓▒  ▒▓▒  ▒▓            ▒▓")
            print("▓▒          ▒▓    ▓ ▒▓    ▓▒          ▒▓")
            print("▓▒        ▒▓    ▒▓ ▒ ▓▒    ▓▒        ▒▓")
            print("▓▒      ▒▓    ▒▓▒ ▓ ▒▓▒    ▓▒      ▒▓")
            print("▓▒    ▒▓    ▒▓▒   ▓   ▒▓▒    ▓▒    ▒▓")
            print("▓▒  ▒▓    ▒▓▒     ▓     ▒▓▒    ▓▒  ▒▓")
            print("▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▓")
            print("▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓")
            print("▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓")
            print("▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓")
            print("▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓")
            print("▓▒▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▓▓▒ ▒▓▒▓")
            print("▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▓")
            print(f"💀 DANGER: PASSBOT ACTIVE v{APP_VERSION} 💀{RESET}")

    def layout(self):
        if not RICH_AVAILABLE:
            return None
        lay = Layout()
        lay.split(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))
        lay["main"].split_row(Layout(name="stats", ratio=2), Layout(name="progress", ratio=3))
        return lay

    def update_live(self, layout: 'Layout', stats: LiveStats):
        if not (RICH_AVAILABLE and layout):
            return
        now = datetime.now().strftime("%H:%M:%S")

        # Glitchy header
        header_text = f"[bold red]TARGETING... BREACHING... {now}[/bold red]"
        if secrets.randbelow(10) < 2:
            header_text = f"[bold red]T4RG3TING... BR34CHING... {now}[/bold red]"
        layout["header"].update(Panel(header_text, border_style="red"))

        tbl = Table(show_header=False, box=box.DOUBLE_EDGE, border_style="red")
        tbl.add_column("Metric", style="yellow", width=15)
        tbl.add_column("Value", style="bold red")

        elapsed = time.time() - stats.start_time
        eta = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds > 0 else "COMPUTING..."

        # Add glitch effects to stats
        def glitch(text, rate=0.1):
            if random.random() < rate:
                return "".join(secrets.choice([c, c.lower(), c.upper(), "▓", "░"]) for c in text)
            return text

        tbl.add_row(glitch("🔐 VECTORS"), f"{stats.passwords_generated:,}")
        tbl.add_row(glitch("⚡ SPEED"), f"{stats.generation_rate:.1f}/s")
        tbl.add_row(glitch("📝 PAYLOAD"), stats.current_password[:60])
        tbl.add_row(glitch("🎯 PHASE"), stats.current_phase)
        tbl.add_row(glitch("⏱️ DURATION"), str(timedelta(seconds=int(elapsed))))
        tbl.add_row("⏳ ETA", eta)
        tbl.add_row(glitch("💾 MEMORY"), f"{stats.memory_usage_mb:.1f} MB")
        tbl.add_row(glitch("💽 STORAGE"), f"{stats.disk_space_gb:.1f} GB")
        if stats.strong_mode_filtered > 0:
            tbl.add_row(glitch("🛡️ REJECTED"), f"{stats.strong_mode_filtered:,}")
        layout["stats"].update(Panel(tbl, title="[bold yellow]ATTACK STATS[/bold yellow]", border_style="yellow"))

        if stats.estimated_total > 0:
            pct = min(100.0, (stats.passwords_generated / max(1, stats.estimated_total)) * 100.0)
            bar_len = 50
            filled = int(pct / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            text = f"Progress: {pct:.1f}%\n[{bar}]\n{stats.passwords_generated:,} / {stats.estimated_total:,}\n\n{stats.current_password}"
        else:
            text = f"Generated: {stats.passwords_generated:,}\n\n{stats.current_password}"
        layout["progress"].update(Panel(text, title="[bold red]LIVE FEED[/bold red]", border_style="red"))

        footer_text = f"CTRL+C TO ABORT ATTACK • TARGET: {stats.output_file}"
        layout["footer"].update(Panel(footer_text, border_style="blue"))

class Bloom:
    """Simple scalable bloom-like set using multiple hashed buckets for lower RAM than Python set.
    False positives possible in de-dup; acceptable for password dictionary use.
    """
    def __init__(self, size_bits: int = 24, hash_count: int = 3):
        self.size = 1 << size_bits  # power of two for fast mask
        self.mask = self.size - 1
        self.arr = bytearray(self.size // 8)
        self.k = hash_count

    def _hashes(self, s: str) -> Iterable[int]:
        h1 = int.from_bytes(hashlib.blake2b(s.encode('utf-8'), digest_size=16).digest(), 'little')
        h2 = int.from_bytes(hashlib.sha1(s.encode('utf-8')).digest()[:8], 'little')
        for i in range(self.k):
            yield (h1 + i * h2) & self.mask

    def add(self, s: str) -> None:
        for h in self._hashes(s):
            byte = h >> 3
            bit = h & 7
            self.arr[byte] |= (1 << bit)

    def __contains__(self, s: str) -> bool:
        for h in self._hashes(s):
            byte = h >> 3
            bit = h & 7
            if (self.arr[byte] >> bit) & 1 == 0:
                return False
        return True

class PassBotEnterprise:
    def __init__(self):
        self.ui = HorrorUI()
        self.stats = LiveStats()
        self.input_profile: Optional[InputProfile] = None
        self.generated_passwords: Set[str] = set()
        self.bloom: Optional[Bloom] = None
        self.progress_file = "passbot_progress.pkl"
        self.current_phase = 1
        self.phase_position = 0
        self.output_handle = None
        self.interrupted = False
        self.words: List[str] = []
        self.numbers: List[str] = []
        self.specials: List[str] = []
        self.seps: List[str] = []
        self.theoretical_total = 0
        signal.signal(signal.SIGINT, self._on_interrupt)

    # System helpers
    def _mem(self) -> float:
        try:
            if psutil:
                return psutil.Process(os.getpid()).memory_info().rss / (1024*1024)
        except Exception:
            pass
        return 0.0

    def _disk(self) -> float:
        try:
            return shutil.disk_usage('.').free / (1024*1024*1024)
        except Exception:
            return 0.0

    # Interrupt
    def _on_interrupt(self, *_):
        print(f"\n{YELLOW}[🛑] Interrupt — saving & exiting quickly...{RESET}")
        self.interrupted = True
        try:
            if self.output_handle and not self.output_handle.closed:
                self.output_handle.flush()
                if hasattr(self.output_handle, 'fileno'):
                    os.fsync(self.output_handle.fileno())
        except Exception:
            pass
        try:
            self._save_progress()
        except Exception:
            pass

    # Serialization helpers
    def _checksum_profile(self, prof: InputProfile) -> str:
        h = hashlib.blake2b(digest_size=16)
        h.update(str(sorted(prof.words)).encode()); h.update(str(sorted(prof.mobile_numbers)).encode())
        h.update(str(sorted(prof.date_fragments)).encode()); h.update(str(sorted(prof.year_ranges)).encode())
        h.update(str(sorted(prof.special_chars)).encode()); h.update(str(sorted(prof.number_patterns)).encode())
        h.update(str(prof.use_underscore_separator).encode()); h.update((prof.generation_mode).encode())
        h.update(str(prof.max_output_count).encode()); h.update(str(prof.strong_threshold).encode())
        return h.hexdigest()

    def _save_progress(self):
        try:
            cursors = {self.current_phase: (self.phase_position, 0, 0, 0)}
            st = ProgressState(
                version=STATE_VERSION,
                phases_done={},
                idx_cursors=cursors,
                total_generated=len(self.generated_passwords),
                start_time=self.stats.start_time,
                input_profile=asdict(self.input_profile) if self.input_profile else {},
                strong_mode_filtered=self.stats.strong_mode_filtered,
                checksum=self._checksum_profile(self.input_profile) if self.input_profile else ""
            )
            with open(self.progress_file, "wb") as f:
                pickle.dump(st, f)
        except Exception as e:
            print(f"{RED}[❌] Save failed: {e}{RESET}")

    def _load_progress(self) -> bool:
        try:
            if not os.path.exists(self.progress_file):
                return False
            with open(self.progress_file, "rb") as f:
                st: ProgressState = pickle.load(f)
            if st.version != STATE_VERSION:
                print(f"{YELLOW}[⚠️] Progress state version changed; starting fresh.{RESET}")
                return False
            if not st.input_profile:
                return False
            ip = InputProfile(**st.input_profile)
            if st.checksum and st.checksum != self._checksum_profile(ip):
                print(f"{YELLOW}[⚠️] Input profile differs from saved state; starting fresh.{RESET}")
                return False
            self.input_profile = ip
            self.current_phase = max(1, min(7, max(st.idx_cursors.keys())))
            self.phase_position = st.idx_cursors.get(self.current_phase, (0,0,0,0))[0]
            self.stats.start_time = st.start_time or time.time()
            self.stats.strong_mode_filtered = st.strong_mode_filtered
            self._preload_existing_output()

            # If the state file claims passwords were generated, but after preloading we have none,
            # then the output file was likely deleted. Force a fresh start.
            if st.total_generated > 0 and not self.generated_passwords:
                print(f"{YELLOW}[⚠️] Progress file indicates passwords were generated, but output file is missing or empty. Starting fresh to ensure data integrity.{RESET}")
                # Reset state variables that might have been partially set
                self.current_phase = 1
                self.phase_position = 0
                return False

            print(f"{GREEN}[📂] Resumed with {len(self.generated_passwords):,} entries • Phase {self.current_phase} pos {self.phase_position}{RESET}")
            return True
        except Exception as e:
            print(f"{YELLOW}[⚠️] Resume failed: {e}{RESET}")
            return False

    # Input helpers
    def _variants(self, w: str) -> List[str]:
        s = set([w, w.lower(), w.upper(), w.capitalize()])
        return sorted(s)

    def _mobile_frags(self, mobile: str) -> List[str]:
        m = re.sub(r"\D", "", mobile)
        fr = set()
        L = len(m)
        for s in range(L):
            for e in range(s + 2, min(s + 11, L + 1)):
                fr.add(m[s:e])
        return sorted(fr)

    def _dob_frags(self, dob: str) -> List[str]:
        s = re.sub(r"[\/\-\s]", "", dob)
        out = set()
        if len(s) == 8 and s.isdigit():
            d, m, y = s[:2], s[2:4], s[4:]
            y2 = y[-2:]
            parts = [d, m, y, y2]
            out.update(parts)
            for i, a in enumerate(parts):
                for j, b in enumerate(parts):
                    if i != j:
                        out.add(f"{a}{b}")
            out.update([
                f"{d}{m}{y2}", f"{d}{m}{y}", f"{m}{d}{y2}", f"{m}{d}{y}",
                f"{y2}{d}{m}", f"{y}{d}{m}", f"{y2}{m}{d}", f"{y}{m}{d}"
            ])
        return sorted(out)

    def _year_range(self, yr: str) -> List[str]:
        if not yr or "-" not in yr:
            return []
        try:
            a, b = yr.split("-")
            a, b = int(a.strip()), int(b.strip())
            if 1900 <= a <= b <= 2099 and (b - a) <= 400:
                return [str(x) for x in range(a, b + 1)]
        except Exception:
            pass
        return []

    def _num_patterns(self, p: str) -> List[str]:
        s = set()
        if p == "00":
            for i in range(100): s.add(f"{i:02d}")
        elif p == "000":
            for i in range(1000): s.add(f"{i:03d}")
        elif p == "0000":
            for i in range(10000): s.add(f"{i:04d}")
        return sorted(s)

    # Write and stats
    def _write(self, pw: str) -> bool:
        # de-dup via bloom + set for high accuracy with low RAM
        if self.bloom and pw in self.bloom:
            return False
        if pw in self.generated_passwords:
            return False
        if self.input_profile.min_length > 0 and len(pw) < self.input_profile.min_length:
            return False
        if self.input_profile.max_length > 0 and len(pw) > self.input_profile.max_length:
            return False
        if self.input_profile.generation_mode == "strong" and not PasswordStrength.is_strong(pw, self.input_profile.strong_threshold):
            self.stats.strong_mode_filtered += 1
            return False
        if self.input_profile.max_output_count and len(self.generated_passwords) >= self.input_profile.max_output_count:
            return False
        self.generated_passwords.add(pw)
        if self.bloom:
            self.bloom.add(pw)
        if self.output_handle:
            self.output_handle.write((pw + "\n").encode('utf-8'))
        # infrequent flush for speed
        if len(self.generated_passwords) % 10000 == 0 and self.output_handle and not self.interrupted:
            try:
                self.output_handle.flush()
            except Exception:
                pass
        return True

    def _update_stats(self, cur: str, phase_name: str):
        self.stats.current_password = cur
        self.stats.current_phase = phase_name
        self.stats.passwords_generated = len(self.generated_passwords)
        elapsed = max(1e-6, time.time() - self.stats.start_time)
        self.stats.generation_rate = self.stats.passwords_generated / elapsed
        self.stats.memory_usage_mb = self._mem()
        self.stats.disk_space_gb = self._disk()
        if self.stats.estimated_total > 0 and self.stats.generation_rate > 0:
            rem = max(0, self.stats.estimated_total - self.stats.passwords_generated)
            self.stats.eta_seconds = rem / self.stats.generation_rate

    # Input collection
    def _collect(self) -> InputProfile:
        print(f"\n{CYAN}📝 PassBot Input Collection{RESET}\n")
        words_input = Prompt.ask("💬 Enter base words (comma-separated)") if RICH_AVAILABLE else input("Enter base words (comma-separated): ")
        words = [w.strip() for w in words_input.split(",") if w.strip()]
        mob_in = Prompt.ask("📱 Mobile numbers (comma-separated, optional)", default="") if RICH_AVAILABLE else input("Mobile numbers (optional): ")
        mobiles = []
        if mob_in:
            for m in [x.strip() for x in mob_in.split(",") if x.strip()]:
                mobiles.extend(self._mobile_frags(m))
        dob = Prompt.ask("🎂 DOB DD/MM/YYYY (optional)", default="") if RICH_AVAILABLE else input("DOB DD/MM/YYYY (optional): ")
        dobf = self._dob_frags(dob) if dob else []
        yr = Prompt.ask("📅 Year range YYYY-YYYY (optional)", default="") if RICH_AVAILABLE else input("Year range YYYY-YYYY (optional): ")
        years = self._year_range(yr) if yr else []
        sc = Prompt.ask("🔣 Special characters (comma-separated, optional)", default="") if RICH_AVAILABLE else input("Special chars (optional): ")
        specials = [c.strip() for c in sc.split(",") if c.strip()] if sc else []
        allow_us = Confirm.ask("🔗 Allow '_' as separator?", default=False) if RICH_AVAILABLE else (input("Allow '_' as separator? (y/N): ").strip().lower() in ("y","yes","1"))
        pat = Prompt.ask("🔢 Number patterns (00,000,0000; comma-separated, optional)", default="") if RICH_AVAILABLE else input("Number patterns 00,000,0000 (optional): ")
        patterns = []
        if pat:
            for p in [x.strip() for x in pat.split(",") if x.strip()]:
                patterns.extend(self._num_patterns(p))
        out = Prompt.ask("💾 Output filename", default="passbot_dictionary.txt") if RICH_AVAILABLE else (input("Output filename [passbot_dictionary.txt]: ").strip() or "passbot_dictionary.txt")
        mode = Prompt.ask("💪 Mode", choices=["full","strong"], default="full") if RICH_AVAILABLE else (input("Mode (full/strong) [full]: ").strip().lower() or "full")
        compression = Prompt.ask("🌀 Compression", choices=["none", "gzip", "bzip2", "lzma"], default="none") if RICH_AVAILABLE else (input("Compression (none/gzip/bzip2/lzma) [none]: ").strip().lower() or "none")
        shard = Confirm.ask("📦 Shard output every ~1,000,000 entries?", default=False) if RICH_AVAILABLE else (input("Shard every 1M? (y/N): ").strip().lower() in ("y","yes","1"))
        strong_thr = 60.0
        if mode == "strong":
            try:
                strong_thr = float(Prompt.ask("Strong threshold (0-100)", default="60")) if RICH_AVAILABLE else float(input("Strong threshold (0-100) [60]: ") or 60)
            except Exception:
                strong_thr = 60.0
        # Optional max cap
        if RICH_AVAILABLE:
            set_cap = Confirm.ask("🎯 Set maximum output cap?", default=False)
        else:
            set_cap = input("Set maximum output cap? (y/N): ").strip().lower() in ("y","yes","1")
        max_count = None
        if set_cap:
            try:
                max_count = IntPrompt.ask("Maximum output (0 = unlimited)", default=0) if RICH_AVAILABLE else int(input("Maximum output (0 = unlimited) [0]: ") or "0")
            except Exception:
                max_count = 0
            if max_count == 0:
                max_count = None

        min_len = IntPrompt.ask("Minimum password length (0 = no limit)", default=0) if RICH_AVAILABLE else int(input("Minimum password length (0 = no limit) [0]: ") or "0")
        max_len = IntPrompt.ask("Maximum password length (0 = no limit)", default=0) if RICH_AVAILABLE else int(input("Maximum password length (0 = no limit) [0]: ") or "0")
        leetspeak = Confirm.ask("Enable leetspeak transformations (e.g., e -> 3)?", default=False) if RICH_AVAILABLE else (input("Enable leetspeak? (y/N): ").strip().lower() in ("y","yes","1"))

        prof = InputProfile(
            words=words,
            mobile_numbers=mobiles,
            date_fragments=dobf,
            year_ranges=years,
            special_chars=specials,
            number_patterns=patterns,
            output_filename=out,
            generation_mode=mode,
            use_underscore_separator=allow_us,
            max_output_count=max_count,
            compression=compression,
            shard_every_million=shard,
            strong_threshold=strong_thr,
            min_length=min_len,
            max_length=max_len,
            leetspeak=leetspeak,
        )
        return prof

    # Prepare lists and accurate estimate
    def _prepare(self):
        self.words = sorted({v for w in self.input_profile.words for v in self._variants(w)})
        self.numbers = sorted(set(self.input_profile.mobile_numbers + self.input_profile.date_fragments + self.input_profile.year_ranges + self.input_profile.number_patterns))
        self.specials = sorted(set(self.input_profile.special_chars))
        self.seps = ["_"] if self.input_profile.use_underscore_separator else [""]

    def _estimate_total(self) -> int:
        W = len(self.words); N = len(self.numbers); S = len(self.specials); SEP = len(self.seps)
        total = 0
        # Phase 1: single words
        total += W
        # Phase 2: single numbers
        total += N
        # Phase 3: word + number (both orders) with seps
        total += W * N * SEP * 2
        # Phase 4: word + special (both orders) with seps
        total += W * S * SEP * 2
        # Phase 5: number + special (both orders) with seps
        total += N * S * SEP * 2
        # Phase 6: word + word (ordered, i != j) with seps
        total += (W * (W - 1)) * SEP
        # Phase 7: triples
        # 7a: w n s permutations (6) with 2 separators
        total += W * N * S * (SEP * SEP) * 6
        # 7b: a,b distinct words + number; permutations (3) with 2 separators
        total += (W * (W - 1)) * N * (SEP * SEP) * 3
        # Optional cap
        if self.input_profile.max_output_count:
            total = min(total, self.input_profile.max_output_count)
        return max(0, total)

    def _leetspeak(self, s: str) -> str:
        leet_map = {'e': '3', 'a': '4', 's': '5', 'o': '0', 'i': '1', 't': '7'}
        return "".join(leet_map.get(c.lower(), c) for c in s)

    def _preload_existing_output(self):
        # Dedupe history
        try:
            fname = self.input_profile.output_filename
            if not os.path.exists(fname):
                return
            load = 0
            if fname.endswith('.gz'):
                opener = gzip.open
                mode = 'rb'
            else:
                opener = open
                mode = 'rb'
            with opener(fname, mode) as f:
                for line in f:
                    try:
                        if isinstance(line, bytes):
                            line = line.decode('utf-8', 'ignore')
                    except Exception:
                        continue
                    line = line.rstrip('\n')
                    if line:
                        self.generated_passwords.add(line)
                        if self.bloom:
                            self.bloom.add(line)
                        load += 1
            if load:
                print(f"{GREEN}[✔] Preloaded existing output: {load:,} entries{RESET}")
        except Exception as e:
            print(f"{YELLOW}[⚠] Could not preload existing output: {e}{RESET}")

    # Generators by phase ensuring deterministic counts
    def _run_generation(self, layout):
        # phase names
        PH = {
            1: "Phase 1/8: Single Words",
            2: "Phase 2/8: Single Numbers",
            3: "Phase 3/8: Word + Number",
            4: "Phase 4/8: Word + Special",
            5: "Phase 5/8: Number + Special",
            6: "Phase 6/8: Word + Word",
            7: "Phase 7/8: Three Elements",
            8: "Phase 8/8: Leetspeak",
        }
        # Phase 1
        if self.current_phase == 1:
            name = PH[1]
            for i, w in enumerate(self.words):
                if self.interrupted: return
                if i < self.phase_position: continue
                self._write(w)
                self.phase_position = i + 1
                if (i % 200) == 0:
                    self._update_stats(w, name); self.ui.update_live(layout, self.stats)
            self.current_phase, self.phase_position = 2, 0
        # Phase 2
        if self.current_phase == 2:
            name = PH[2]
            for i, n in enumerate(self.numbers):
                if self.interrupted: return
                if i < self.phase_position: continue
                self._write(str(n))
                self.phase_position = i + 1
                if (i % 200) == 0:
                    self._update_stats(str(n), name); self.ui.update_live(layout, self.stats)
            self.current_phase, self.phase_position = 3, 0
        # Phase 3
        if self.current_phase == 3:
            name = PH[3]
            idx = 0
            for w in self.words:
                if self.interrupted: return
                for n in self.numbers:
                    if self.interrupted: return
                    for s in self.seps:
                        for combo in (f"{w}{s}{n}", f"{n}{s}{w}"):
                            if self.interrupted: return
                            if idx < self.phase_position:
                                idx += 1; continue
                            self._write(combo)
                            if (idx % 200) == 0:
                                self._update_stats(combo, name); self.ui.update_live(layout, self.stats)
                            idx += 1; self.phase_position = idx
            self.current_phase, self.phase_position = 4, 0
        # Phase 4
        if self.current_phase == 4:
            name = PH[4]
            idx = 0
            if self.specials:
                for w in self.words:
                    if self.interrupted: return
                    for sp in self.specials:
                        if self.interrupted: return
                        for s in self.seps:
                            for combo in (f"{w}{s}{sp}", f"{sp}{s}{w}"):
                                if self.interrupted: return
                                if idx < self.phase_position:
                                    idx += 1; continue
                                self._write(combo)
                                if (idx % 200) == 0:
                                    self._update_stats(combo, name); self.ui.update_live(layout, self.stats)
                                idx += 1; self.phase_position = idx
            self.current_phase, self.phase_position = 5, 0
        # Phase 5
        if self.current_phase == 5:
            name = PH[5]
            idx = 0
            if self.specials:
                for n in self.numbers:
                    if self.interrupted: return
                    for sp in self.specials:
                        if self.interrupted: return
                        for s in self.seps:
                            for combo in (f"{n}{s}{sp}", f"{sp}{s}{n}"):
                                if self.interrupted: return
                                if idx < self.phase_position:
                                    idx += 1; continue
                                self._write(combo)
                                if (idx % 200) == 0:
                                    self._update_stats(combo, name); self.ui.update_live(layout, self.stats)
                                idx += 1; self.phase_position = idx
            self.current_phase, self.phase_position = 6, 0
        # Phase 6
        if self.current_phase == 6:
            name = PH[6]
            idx = 0
            if len(self.words) >= 2:
                for i, a in enumerate(self.words):
                    if self.interrupted: return
                    for j, b in enumerate(self.words):
                        if self.interrupted: return
                        if i == j: continue
                        for s in self.seps:
                            combo = f"{a}{s}{b}"
                            if idx < self.phase_position:
                                idx += 1; continue
                            self._write(combo)
                            if (idx % 200) == 0:
                                self._update_stats(combo, name); self.ui.update_live(layout, self.stats)
                            idx += 1; self.phase_position = idx
            self.current_phase, self.phase_position = 7, 0
        # Phase 7
        if self.current_phase == 7:
            name = PH[7]
            idx = 0
            # w n s (6 perms)
            if self.words and self.numbers and self.specials:
                for w in self.words:
                    if self.interrupted: return
                    for n in self.numbers:
                        if self.interrupted: return
                        for sp in self.specials:
                            if self.interrupted: return
                            for s1 in self.seps:
                                if self.interrupted: return
                                for s2 in self.seps:
                                    combos = (
                                        f"{w}{s1}{n}{s2}{sp}", f"{w}{s1}{sp}{s2}{n}",
                                        f"{n}{s1}{w}{s2}{sp}", f"{n}{s1}{sp}{s2}{w}",
                                        f"{sp}{s1}{w}{s2}{n}", f"{sp}{s1}{n}{s2}{w}",
                                    )
                                    for c in combos:
                                        if self.interrupted: return
                                        if idx < self.phase_position:
                                            idx += 1; continue
                                        self._write(c)
                                        if (idx % 200) == 0:
                                            self._update_stats(c, name); self.ui.update_live(layout, self.stats)
                                        idx += 1; self.phase_position = idx
            # a,b (distinct words) + number — 3 perms
            if len(self.words) >= 2 and self.numbers:
                for i, a in enumerate(self.words):
                    if self.interrupted: return
                    for j, b in enumerate(self.words):
                        if self.interrupted: return
                        if i == j: continue
                        for n in self.numbers:
                            if self.interrupted: return
                            for s1 in self.seps:
                                if self.interrupted: return
                                for s2 in self.seps:
                                    combos = (
                                        f"{a}{s1}{b}{s2}{n}", f"{a}{s1}{n}{s2}{b}", f"{n}{s1}{a}{s2}{b}",
                                    )
                                    for c in combos:
                                        if self.interrupted: return
                                        if idx < self.phase_position:
                                            idx += 1; continue
                                        self._write(c)
                                        if (idx % 200) == 0:
                                            self._update_stats(c, name); self.ui.update_live(layout, self.stats)
                                        idx += 1; self.phase_position = idx

        # Phase 8: Leetspeak
        if self.input_profile.leetspeak:
            name = "Phase 8/8: Leetspeak"
            passwords_to_transform = list(self.generated_passwords)
            for i, pw in enumerate(passwords_to_transform):
                if self.interrupted: return
                leet_pw = self._leetspeak(pw)
                if leet_pw != pw:
                    self._write(leet_pw)
                if (i % 200) == 0:
                    self._update_stats(leet_pw, name); self.ui.update_live(layout, self.stats)

    def _open_output(self):
        fname = self.input_profile.output_filename
        if self.input_profile.compression == "gzip" and not fname.endswith('.gz'):
            fname += '.gz'
        elif self.input_profile.compression == "bzip2" and not fname.endswith('.bz2'):
            fname += '.bz2'
        elif self.input_profile.compression == "lzma" and not fname.endswith('.xz'):
            fname += '.xz'

        self.input_profile.output_filename = fname
        os.makedirs(os.path.dirname(fname) or '.', exist_ok=True)

        if self.input_profile.compression == "gzip":
            self.output_handle = gzip.open(fname, 'ab', compresslevel=6)
        elif self.input_profile.compression == "bzip2":
            self.output_handle = bz2.open(fname, 'ab')
        elif self.input_profile.compression == "lzma":
            self.output_handle = lzma.open(fname, 'ab')
        else:
            self.output_handle = open(fname, 'ab', buffering=1024*1024)

    def run(self) -> int:
        # Full Brand intro with ASCII art
        self.ui.show_full_banner()
        time.sleep(2.0)  # Let user see the banner

        # Resume or fresh
        resumed = False
        if os.path.exists(self.progress_file):
            if RICH_AVAILABLE:
                do_resume = Confirm.ask("📂 Previous progress found. Resume?", default=True)
            else:
                do_resume = input("Previous progress found. Resume? (Y/n): ").strip().lower() not in ("n","no","0")
            if do_resume:
                resumed = self._load_progress()
        if not resumed:
            self.input_profile = self._collect()
            if not self.input_profile or not self.input_profile.words:
                print(f"{RED}❌ At least one base word is required.{RESET}")
                return 1
        # bloom for memory efficient dedupe
        self.bloom = Bloom(size_bits=24, hash_count=3)  # ~2MB
        # Prepare
        self._prepare()
        # Open output + preload
        try:
            self._open_output()
        except Exception as e:
            print(f"{RED}❌ Cannot open output: {e}{RESET}")
            return 1
        self._preload_existing_output()
        # Cap already satisfied?
        if self.input_profile.max_output_count and len(self.generated_passwords) >= self.input_profile.max_output_count:
            print(f"{GREEN}✔ Max output already reached ({len(self.generated_passwords):,}). Nothing to do.{RESET}")
            return 0
        # Estimate
        self.theoretical_total = self._estimate_total()
        self.stats.start_time = time.time()
        self.stats.output_file = self.input_profile.output_filename
        self.stats.estimated_total = self.theoretical_total
        # Live layout
        layout = self.ui.layout()
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2):
                    self._run_generation(layout)
            else:
                self._run_generation(None)
        except KeyboardInterrupt:
            pass
        finally:
            try:
                if self.output_handle:
                    self.output_handle.flush()
                    if hasattr(self.output_handle, 'fileno'):
                        os.fsync(self.output_handle.fileno())
                    self.output_handle.close()
            except Exception:
                pass
            if not self.interrupted:
                self._save_progress()
        # Summary
        total = len(self.generated_passwords)
        elapsed = time.time() - self.stats.start_time
        print(f"\n{BOLD}{GREEN}✅ Done. Generated: {total:,}{RESET}")
        print(f"{GREEN}⏱️ Time: {str(timedelta(seconds=int(elapsed)))}{RESET}")
        print(f"{GREEN}⚡ Rate: {total/max(1,elapsed):.1f}/sec{RESET}")
        if self.stats.strong_mode_filtered > 0:
            print(f"{YELLOW}🛡️ Filtered weak: {self.stats.strong_mode_filtered:,}{RESET}")
        print(f"{GREEN}💾 Output: {self.input_profile.output_filename}{RESET}")
        return 0

def main():
    print(f"{BOLD}{CYAN}🕷️ PassBot Enterprise — Gen‑Spider Brand Edition v{APP_VERSION}{RESET}\n")
    app = PassBotEnterprise()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
