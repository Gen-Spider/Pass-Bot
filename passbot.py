#!/usr/bin/env python3
"""
PassBot Enterprise — Gen‑Spider Brand Edition
Complete 9‑Chapter Logic + Brand Animation + Accurate Progress + Safe Resume

Chapters:
1) Words Input Logic
2) Mobile Numbers Logic
3) Date of Birth Logic
4) Year Range Logic
5) Special Characters Logic
6) Separator Choice Logic
7) Number Patterns Logic
8) Generation Mode Logic (full/strong) with scoring
9) Resume Logic (phase + position + dedupe from existing file)
"""

import os
import sys
import re
import time
import math
import signal
import pickle
import shutil
import psutil
import secrets
import string
from dataclasses import dataclass, asdict
from typing import List, Set, Optional, Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

# Attempt to install dependencies automatically
def _ensure_deps():
    needed = []
    for p in ("rich","colorama","psutil"):
        try:
            __import__(p)
        except Exception:
            needed.append(p)
    if needed:
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", *needed])
        except Exception:
            pass
_ensure_deps()

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

try:
    import colorama
    colorama.init(autoreset=True)
except Exception:
    pass

# Terminal colors (fallback print)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

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
    generated_passwords: Set[str]
    current_phase: int
    phase_position: int
    total_generated: int
    generation_start_time: float
    last_save_time: float
    input_profile_data: dict
    strong_mode_filtered: int = 0

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
    min_output_count: Optional[int] = None
    max_output_count: Optional[int] = None

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
        if n >= 20:
            s += 30
        elif n >= 16:
            s += 25
        elif n >= 12:
            s += 20
        elif n >= 8:
            s += 15
        else:
            s += n * 1.5
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
        # penalties
        if re.search(r"(.)\1{2,}", password):
            s -= 15
        if re.search(r"(abc|123|qwe|password|admin|user|test)", password.lower()):
            s -= 20
        return max(0, min(100, s))

    @staticmethod
    def is_strong(pw: str, threshold: float = 60.0) -> bool:
        return PasswordStrength.score(pw) >= threshold

class MatrixUI:
    """
    Gen‑Spider brand UI:
    - Animated banner (matrix effect)
    - Panel with red border, green title text, cyan accents
    """
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

    def show_matrix_effect(self, duration: float = 1.8):
        # simple falling characters
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        start = time.time()
        while time.time() - start < duration:
            col = secrets.randbelow(max(2, self.width - 2))
            row = secrets.randbelow(max(4, self.height - 4))
            ch = secrets.choice(chars)
            print(f"\033[{row};{col}H\033[92m{ch}\033[0m", end="", flush=True)
            time.sleep(0.006)
        # clear the artifacts
        print("\033[H\033[J", end="")

    def show_banner(self):
        # Animated intro + brand panel
        if RICH_AVAILABLE:
            self.clear()
            self.show_matrix_effect(1.8)
            banner_text = Text(
                "\n██████╗ ███████╗███╗  ██╗ ██████╗  █████╗ ███████╗███████╗\n"
                "██╔════╝ ██╔════╝████╗ ██║ ██╔══██╗██╔══██╗██╔════╝██╔════╝\n"
                "██║  ███╗█████╗  ██╔██╗██║ █████╔╝ ███████║███████╗███████╗\n"
                "██║   ██║██╔══╝  ██║╚████║ ██╔═══╝  ██╔══██║╚════██║╚════██║\n"
                "╚██████╔╝███████╗██║ ╚███║ ██║      ██║  ██║███████║███████║\n"
                " ╚═════╝ ╚══════╝╚═╝  ╚══╝ ╚═╝      ╚═╝  ╚═╝╚══════╝╚══════╝\n\n"
                "🕷️ PASSBOT ENTERPRISE SUITE 🕷️\n"
                "Professional Password Dictionary Generation & Analysis\n",
                style="bold green"
            )
            panel = Panel(
                Align.center(banner_text),
                title="[bold red]🔐 GEN-SPIDER SECURITY SYSTEMS 🔐[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"{BOLD}{GREEN}PASSBOT ENTERPRISE — GEN‑SPIDER SECURITY SYSTEMS{RESET}")

    def show_loading(self, text: str = "Initializing Enterprise Systems", duration: float = 1.5):
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn("dots", style="green"),
                TextColumn("[green]{task.description}")
            , console=self.console) as prog:
                t = prog.add_task(text, total=100)
                for _ in range(100):
                    time.sleep(duration/100.0)
                    prog.update(t, advance=1)
        else:
            print(f"{GREEN}{text}...{RESET}")
            time.sleep(duration)

    def layout(self):
        if not RICH_AVAILABLE:
            return None
        lay = Layout()
        lay.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        lay["main"].split_row(
            Layout(name="stats", ratio=2),
            Layout(name="progress", ratio=3)
        )
        return lay

    def update_live(self, layout: Layout, stats: LiveStats):
        if not (RICH_AVAILABLE and layout):
            return
        now = datetime.now().strftime("%H:%M:%S")
        layout["header"].update(
            Panel(f"[bold green]🎯 LIVE GENERATION — {now}[/bold green]", border_style="green")
        )
        tbl = Table(show_header=False, box=box.SIMPLE)
        tbl.add_column("Metric", style="cyan", width=15)
        tbl.add_column("Value", style="bright_green")
        elapsed = time.time() - stats.start_time
        eta = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds > 0 else "Calculating..."
        tbl.add_row("🔐 Generated", f"{stats.passwords_generated:,}")
        tbl.add_row("⚡ Rate", f"{stats.generation_rate:.1f}/sec")
        tbl.add_row("📝 Current", stats.current_password[:40])
        tbl.add_row("🎯 Phase", stats.current_phase)
        tbl.add_row("⏱️ Elapsed", str(timedelta(seconds=int(elapsed))))
        tbl.add_row("⏳ ETA", eta)
        tbl.add_row("💾 Memory", f"{stats.memory_usage_mb:.1f} MB")
        tbl.add_row("💽 Disk", f"{stats.disk_space_gb:.1f} GB")
        if stats.strong_mode_filtered > 0:
            tbl.add_row("🛡️ Filtered", f"{stats.strong_mode_filtered:,}")
        layout["stats"].update(
            Panel(tbl, title="📊 Live Statistics", border_style="cyan")
        )
        # progress panel
        if stats.estimated_total > 0:
            pct = min(100.0, (stats.passwords_generated / max(1, stats.estimated_total)) * 100.0)
            bar = "█" * int(pct/2) + "░" * (50 - int(pct/2))
            text = f"Progress: {pct:.1f}%\n[{bar}]\n{stats.passwords_generated:,} / {stats.estimated_total:,}\n\n{stats.current_password}"
        else:
            text = f"Generated: {stats.passwords_generated:,}\n\n{stats.current_password}"
        layout["progress"].update(
            Panel(text, title="⚡ Live Progress", border_style="yellow")
        )
        layout["footer"].update(
            Panel(
                f"Press Ctrl+C to stop safely • Output: {stats.output_file}",
                border_style="blue"
            )
        )

class PassBotEnterprise:
    def __init__(self):
        self.ui = MatrixUI()
        self.stats = LiveStats()
        self.input_profile: Optional[InputProfile] = None
        self.generated_passwords: Set[str] = set()
        self.progress_file = "passbot_progress.pkl"
        self.current_phase = 1
        self.phase_position = 0
        self.backup_interval = 5000
        self.output_file = None
        self.interrupted = False

        signal.signal(signal.SIGINT, self._on_interrupt)

    # System helpers
    def _mem(self) -> float:
        try:
            return psutil.Process(os.getpid()).memory_info().rss / (1024*1024)
        except Exception:
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
            if self.output_file and not self.output_file.closed:
                self.output_file.flush()
                os.fsync(self.output_file.fileno())
        except Exception:
            pass
        # Save state fast
        try:
            self._save_progress()
        except Exception:
            pass

    # Progress save/load
    def _save_progress(self):
        try:
            st = ProgressState(
                generated_passwords=self.generated_passwords.copy(),
                current_phase=self.current_phase,
                phase_position=self.phase_position,
                total_generated=len(self.generated_passwords),
                generation_start_time=self.stats.start_time,
                last_save_time=time.time(),
                input_profile_data=asdict(self.input_profile) if self.input_profile else {},
                strong_mode_filtered=self.stats.strong_mode_filtered
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
            self.generated_passwords = st.generated_passwords
            self.current_phase = st.current_phase
            self.phase_position = st.phase_position
            self.stats.start_time = st.generation_start_time or time.time()
            self.stats.strong_mode_filtered = st.strong_mode_filtered
            if st.input_profile_data:
                self.input_profile = InputProfile(**st.input_profile_data)
            print(f"{GREEN}[📂] Resumed: {len(self.generated_passwords):,} passwords{RESET}")
            print(f"{CYAN}[📍] Phase {self.current_phase}, position {self.phase_position}{RESET}")
            return True
        except Exception as e:
            print(f"{YELLOW}[⚠️] Resume failed: {e}{RESET}")
            return False

    # Input helpers
    def _variants(self, w: str) -> List[str]:
        return list({w.lower(), w.upper(), w.capitalize()})

    def _mobile_frags(self, mobile: str) -> List[str]:
        m = re.sub(r"\D", "", mobile)
        fr = set()
        for s in range(len(m)):
            for e in range(s + 2, min(s + 11, len(m) + 1)):
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
            if 1900 <= a <= b <= 2035:
                return [str(x) for x in range(a, b + 1)]
        except Exception:
            pass
        return []

    def _num_patterns(self, p: str) -> List[str]:
        s = set()
        if p == "00":
            for i in range(100):
                s.add(f"{i:02d}")
        elif p == "000":
            for i in range(1000):
                s.add(f"{i:03d}")
        elif p == "0000":
            for i in range(10000):
                s.add(f"{i:04d}")
        return sorted(s)

    # Write and stats
    def _write(self, pw: str) -> bool:
        if pw in self.generated_passwords:
            return False
        # strong mode
        if self.input_profile.generation_mode == "strong" and not PasswordStrength.is_strong(pw):
            self.stats.strong_mode_filtered += 1
            return False
        # cap by max output count
        if self.input_profile.max_output_count and len(self.generated_passwords) >= self.input_profile.max_output_count:
            return False
        self.generated_passwords.add(pw)
        if self.output_file:
            self.output_file.write(pw + "\n")
        # lighter flush cadence; no fsync unless interrupt/finally
        if len(self.generated_passwords) % 2000 == 0 and self.output_file and not self.interrupted:
            try:
                self.output_file.flush()
            except Exception:
                pass
        if len(self.generated_passwords) % self.backup_interval == 0:
            self._save_progress()
        return True

    def _update_stats(self, cur: str, phase: str):
        self.stats.current_password = cur
        self.stats.current_phase = phase
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
        words = [w.strip().lower() for w in words_input.split(",") if w.strip()]

        mob_in = Prompt.ask("📱 Mobile numbers (comma-separated, optional)", default="") if RICH_AVAILABLE else input("Mobile numbers (optional): ")
        mobiles = []
        if mob_in:
            for m in [x.strip() for x in mob_in.split(",") if x.strip()]:
                mobiles.extend(self._mobile_frags(m))

        dob = Prompt.ask("🎂 DOB DD/MM/YYYY (optional)", default="") if RICH_AVAILABLE else input("DOB DD/MM/YYYY (optional): ")
        dobf = self._dob_frags(dob) if dob else []

        yr = Prompt.ask("📅 Year range YYYY-YYYY (optional)", default="") if RICH_AVAILABLE else input("Year range YYYY-YYYY (optional): ")
        years = self._year_range(yr) if yr else []

        sc = Prompt.ask("🔣 Your special characters (comma-separated, optional)", default="") if RICH_AVAILABLE else input("Your special chars (optional): ")
        specials = [c.strip() for c in sc.split(",") if c.strip()] if sc else []

        allow_us = Confirm.ask("🔗 Allow '_' as separator?", default=False) if RICH_AVAILABLE else (input("Allow '_' as separator? (y/N): ").strip().lower() in ("y","yes","1"))

        pat = Prompt.ask("🔢 Number patterns (00,000,0000; comma-separated, optional)", default="") if RICH_AVAILABLE else input("Number patterns 00,000,0000 (optional): ")
        patterns = []
        if pat:
            for p in [x.strip() for x in pat.split(",") if x.strip()]:
                patterns.extend(self._num_patterns(p))

        out = Prompt.ask("💾 Output filename", default="passbot_dictionary.txt") if RICH_AVAILABLE else (input("Output filename [passbot_dictionary.txt]: ").strip() or "passbot_dictionary.txt")
        mode = Prompt.ask("💪 Mode", choices=["full","strong"], default="full") if RICH_AVAILABLE else (input("Mode (full/strong) [full]: ").strip().lower() or "full")

        # Optional max cap
        if RICH_AVAILABLE:
            set_limits = Confirm.ask("🎯 Set maximum output cap?", default=False)
        else:
            set_limits = input("Set maximum output cap? (y/N): ").strip().lower() in ("y","yes","1")
        min_count = None
        max_count = None
        if set_limits:
            if RICH_AVAILABLE:
                min_count = 0
                max_count = IntPrompt.ask("Maximum output (0 = unlimited)", default=0)
            else:
                try:
                    min_count = 0
                    max_count = int(input("Maximum output (0 = unlimited) [0]: ").strip() or "0")
                except Exception:
                    max_count = 0
            if max_count == 0:
                max_count = None

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
            min_output_count=min_count,
            max_output_count=max_count
        )
        return prof

    # Prepare lists and estimate
    def _prepare(self):
        words = sorted({v for w in self.input_profile.words for v in self._variants(w)})
        numbers = sorted(set(self.input_profile.mobile_numbers + self.input_profile.date_fragments + self.input_profile.year_ranges + self.input_profile.number_patterns))
        specials = sorted(set(self.input_profile.special_chars))
        seps = ["_"] if self.input_profile.use_underscore_separator else [""]
        return words, numbers, specials, seps

    def _estimate_total(self, words: List[str], numbers: List[str], specials: List[str], seps: List[str]) -> int:
        total = 0
        total += len(words)          # singles (words)
        total += len(numbers)        # singles (numbers)
        # pairs
        total += len(words)*len(numbers)*len(seps)*2 if words and numbers else 0
        total += len(words)*len(specials)*len(seps)*2 if words and specials else 0
        total += len(numbers)*len(specials)*len(seps)*2 if numbers and specials else 0
        total += len(words)*max(0, len(words)-1)*len(seps) if len(words) >= 2 else 0
        # triples
        if words and numbers and specials:
            total += len(words)*len(numbers)*len(specials)*len(seps)*len(seps)*6
        return total

    def _preload_existing_output(self):
        # Load already written lines to dedupe on resume or rerun
        try:
            if self.input_profile and os.path.exists(self.input_profile.output_filename):
                with open(self.input_profile.output_filename, "r", encoding="utf-8", errors="ignore") as f:
                    cnt = 0
                    for line in f:
                        line = line.rstrip("\n")
                        if line:
                            self.generated_passwords.add(line)
                            cnt += 1
                if cnt:
                    print(f"{GREEN}[✔] Preloaded existing output: {cnt:,} entries{RESET}")
        except Exception as e:
            print(f"{YELLOW}[⚠] Could not preload existing output: {e}{RESET}")

    # Generation phases
    def _generate(self, words: List[str], numbers: List[str], specials: List[str], seps: List[str], layout):
        # Phase 1: single words
        if self.current_phase == 1:
            phase = "Phase 1/7: Single Words"
            for i, w in enumerate(words):
                if self.interrupted: return
                if i < self.phase_position: continue
                self._write(w)
                self.phase_position = i + 1
                if len(self.generated_passwords) % 200 == 0:
                    self._update_stats(w, phase); self.ui.update_live(layout, self.stats)
            self.current_phase = 2; self.phase_position = 0

        # Phase 2: single numbers
        if self.current_phase == 2:
            phase = "Phase 2/7: Single Numbers"
            for i, n in enumerate(numbers):
                if self.interrupted: return
                if i < self.phase_position: continue
                self._write(str(n))
                self.phase_position = i + 1
                if len(self.generated_passwords) % 200 == 0:
                    self._update_stats(str(n), phase); self.ui.update_live(layout, self.stats)
            self.current_phase = 3; self.phase_position = 0

        # Phase 3: word + number (both orders)
        if self.current_phase == 3:
            phase = "Phase 3/7: Word + Number"
            idx = 0
            for w in words:
                if self.interrupted: return
                for n in numbers:
                    if self.interrupted: return
                    for s in seps:
                        for combo in (f"{w}{s}{n}", f"{n}{s}{w}"):
                            if self.interrupted: return
                            if idx < self.phase_position:
                                idx += 1; continue
                            self._write(combo)
                            if len(self.generated_passwords) % 200 == 0:
                                self._update_stats(combo, phase); self.ui.update_live(layout, self.stats)
                            idx += 1; self.phase_position = idx
            self.current_phase = 4; self.phase_position = 0

        # Phase 4: word + special (both orders)
        if self.current_phase == 4:
            phase = "Phase 4/7: Word + Special"
            idx = 0
            if specials:
                for w in words:
                    if self.interrupted: return
                    for sp in specials:
                        if self.interrupted: return
                        for s in seps:
                            for combo in (f"{w}{s}{sp}", f"{sp}{s}{w}"):
                                if self.interrupted: return
                                if idx < self.phase_position:
                                    idx += 1; continue
                                self._write(combo)
                                if len(self.generated_passwords) % 200 == 0:
                                    self._update_stats(combo, phase); self.ui.update_live(layout, self.stats)
                                idx += 1; self.phase_position = idx
            self.current_phase = 5; self.phase_position = 0

        # Phase 5: number + special (both orders)
        if self.current_phase == 5:
            phase = "Phase 5/7: Number + Special"
            idx = 0
            if specials:
                for n in numbers:
                    if self.interrupted: return
                    for sp in specials:
                        if self.interrupted: return
                        for s in seps:
                            for combo in (f"{n}{s}{sp}", f"{sp}{s}{n}"):
                                if self.interrupted: return
                                if idx < self.phase_position:
                                    idx += 1; continue
                                self._write(combo)
                                if len(self.generated_passwords) % 200 == 0:
                                    self._update_stats(combo, phase); self.ui.update_live(layout, self.stats)
                                idx += 1; self.phase_position = idx
            self.current_phase = 6; self.phase_position = 0

        # Phase 6: word + word
        if self.current_phase == 6:
            phase = "Phase 6/7: Word + Word"
            idx = 0
            if len(words) >= 2:
                for i, a in enumerate(words):
                    if self.interrupted: return
                    for j, b in enumerate(words):
                        if self.interrupted: return
                        if i == j: continue
                        for s in seps:
                            if self.interrupted: return
                            combo = f"{a}{s}{b}"
                            if idx < self.phase_position:
                                idx += 1; continue
                            self._write(combo)
                            if len(self.generated_passwords) % 200 == 0:
                                self._update_stats(combo, phase); self.ui.update_live(layout, self.stats)
                            idx += 1; self.phase_position = idx
            self.current_phase = 7; self.phase_position = 0

        # Phase 7: triple combos
        if self.current_phase == 7:
            phase = "Phase 7/7: Three Elements"
            idx = 0
            # word + number + special (6 permutations)
            if words and numbers and specials:
                for w in words:
                    if self.interrupted: return
                    for n in numbers:
                        if self.interrupted: return
                        for sp in specials:
                            if self.interrupted: return
                            for s1 in seps:
                                if self.interrupted: return
                                for s2 in seps:
                                    combos = (
                                        f"{w}{s1}{n}{s2}{sp}",
                                        f"{w}{s1}{sp}{s2}{n}",
                                        f"{n}{s1}{w}{s2}{sp}",
                                        f"{n}{s1}{sp}{s2}{w}",
                                        f"{sp}{s1}{w}{s2}{n}",
                                        f"{sp}{s1}{n}{s2}{w}",
                                    )
                                    for c in combos:
                                        if self.interrupted: return
                                        if idx < self.phase_position:
                                            idx += 1; continue
                                        self._write(c)
                                        if len(self.generated_passwords) % 200 == 0:
                                            self._update_stats(c, phase); self.ui.update_live(layout, self.stats)
                                        idx += 1; self.phase_position = idx
            # word + word + number
            if len(words) >= 2 and numbers:
                for i, a in enumerate(words):
                    if self.interrupted: return
                    for j, b in enumerate(words):
                        if self.interrupted: return
                        if i == j: continue
                        for n in numbers:
                            if self.interrupted: return
                            for s1 in seps:
                                if self.interrupted: return
                                for s2 in seps:
                                    combos = (
                                        f"{a}{s1}{b}{s2}{n}",
                                        f"{a}{s1}{n}{s2}{b}",
                                        f"{n}{s1}{a}{s2}{b}",
                                    )
                                    for c in combos:
                                        if self.interrupted: return
                                        if idx < self.phase_position:
                                            idx += 1; continue
                                        self._write(c)
                                        if len(self.generated_passwords) % 200 == 0:
                                            self._update_stats(c, phase); self.ui.update_live(layout, self.stats)
                                        idx += 1; self.phase_position = idx

    def run(self) -> int:
        # Brand intro
        self.ui.show_banner()
        self.ui.show_loading("Bringing systems online", 1.2)

        # Resume?
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

        # Prepare lists
        words, numbers, specials, seps = self._prepare()

        # Open output
        try:
            # append if exists; dedupe with preload regardless of resume
            self.output_file = open(self.input_profile.output_filename, "a", encoding="utf-8")
        except Exception as e:
            print(f"{RED}❌ Cannot open output: {e}{RESET}")
            return 1

        # Preload existing file to dedupe and to instantly finish if already at cap
        self._preload_existing_output()

        # If capped and already have enough, exit immediately
        if self.input_profile.max_output_count and len(self.generated_passwords) >= self.input_profile.max_output_count:
            print(f"{GREEN}✔ Max output already reached ({len(self.generated_passwords):,}). Nothing to do.{RESET}")
            return 0

        # Estimated total calculation
        theoretical_total = self._estimate_total(words, numbers, specials, seps)
        if self.input_profile.max_output_count:
            estimated_total = min(theoretical_total, self.input_profile.max_output_count)
        else:
            estimated_total = theoretical_total

        # Stats init
        self.stats.start_time = time.time()
        self.stats.output_file = self.input_profile.output_filename
        self.stats.estimated_total = estimated_total

        # Live loop
        layout = self.ui.layout()
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2):
                    self._generate(words, numbers, specials, seps, layout)
            else:
                self._generate(words, numbers, specials, seps, None)
        except KeyboardInterrupt:
            pass
        finally:
            try:
                if self.output_file:
                    self.output_file.flush()
                    os.fsync(self.output_file.fileno())
                    self.output_file.close()
            except Exception:
                pass
            # final save
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

        # Min output warning (if ever used)
        if self.input_profile.min_output_count and total < self.input_profile.min_output_count:
            print(f"{YELLOW}⚠️ Only {total:,} generated; minimum requested was {self.input_profile.min_output_count:,}{RESET}")

        return 0

def main():
    print(f"{BOLD}{CYAN}🕷️ PassBot Enterprise — Gen‑Spider Brand Edition{RESET}\n")
    app = PassBotEnterprise()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
