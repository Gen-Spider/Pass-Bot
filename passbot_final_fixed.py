#!/usr/bin/env python3
"""
Pass-Bot Enterprise Personal Dictionary Generator (Fixed Version - No Separators + Incremental Output)
=====================================================================================================

🕷️ Professional brute force dictionary generator for security testing
Built with Gen-Spider level enterprise architecture and quality standards

🎯 FIXES IN THIS UPDATE:
- Removed '.' and '-' separators entirely; only empty separator is used by default
- Added optional '_' separator toggle (prompt) — default OFF
- Implemented incremental save directly to output file during generation
- On interrupt, current progress is flushed to the same output file (no loss)
- Resume continues and keeps writing to the same output file without duplications

Repository: Pass-Bot
Author: Gen-Spider Security Systems
Version: 1.2.2 Fixed
License: MIT
"""

import os
import sys
import re
import time
import psutil
import shutil
import signal
import pickle
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    os.system("pip install rich psutil")
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.prompt import Prompt, Confirm
        from rich.live import Live
        from rich.layout import Layout
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

class Colors:
    BRIGHT_GREEN = '\033[1;92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

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
    output_file: str = "passbot_final_dictionary.txt"

@dataclass
class ProgressState:
    generated_passwords: Set[str]
    current_phase: int
    phase_position: int
    total_generated: int
    generation_start_time: float
    last_save_time: float
    input_profile_data: dict

@dataclass
class InputProfile:
    words: List[str]
    mobile_numbers: List[str]
    date_fragments: List[str]
    year_ranges: List[str]
    special_chars: List[str]
    number_patterns: List[str]
    output_filename: str
    allow_underscore: bool = False
    complete_generation: bool = True

class SystemMonitor:
    @staticmethod
    def mem_mb() -> float:
        try:
            return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except:
            return 0.0

    @staticmethod
    def disk_gb(path: str = ".") -> float:
        try:
            return shutil.disk_usage(path).free / 1024 / 1024 / 1024
        except:
            return 0.0

class MatrixUI:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def layout(self):
        if not RICH_AVAILABLE:
            return None
        layout = Layout()
        layout.split(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))
        layout["main"].split_row(Layout(name="stats", ratio=2), Layout(name="progress", ratio=3))
        return layout

    def update(self, layout: Layout, stats: LiveStats):
        if not RICH_AVAILABLE or not layout:
            return
        layout["header"].update(Panel(f"[bold green]🎯 PASS-BOT LIVE - {datetime.now().strftime('%H:%M:%S')}[/bold green]"))

        t = Table(show_header=False)
        t.add_column("Metric", style="cyan")
        t.add_column("Value", style="bright_green")
        elapsed = time.time() - stats.start_time
        eta = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds > 0 else "Calculating..."
        t.add_row("🔐 Generated", f"{stats.passwords_generated:,}")
        t.add_row("⚡ Rate", f"{stats.generation_rate:.1f}/sec")
        t.add_row("📝 Current", stats.current_password[:40])
        t.add_row("🎯 Phase", stats.current_phase)
        t.add_row("⏱️ Elapsed", str(timedelta(seconds=int(elapsed))))
        t.add_row("⏳ ETA", eta)
        t.add_row("💾 Memory", f"{stats.memory_usage_mb:.1f} MB")
        t.add_row("💽 Disk", f"{stats.disk_space_gb:.1f} GB")
        layout["stats"].update(Panel(t, title="📊 Statistics"))

        if stats.estimated_total > 0:
            pct = min(100.0, (stats.passwords_generated / stats.estimated_total) * 100)
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            info = f"Progress: {pct:.1f}% [{bar}]\nGenerated: {stats.passwords_generated:,}/{stats.estimated_total:,}\n\nCurrent: {stats.current_password}\n"
        else:
            info = f"Generated: {stats.passwords_generated:,}\n\nCurrent: {stats.current_password}\n"
        layout["progress"].update(Panel(info, title="⚡ Live Progress"))
        layout["footer"].update(Panel(f"Press Ctrl+C to stop safely | Output: {stats.output_file}"))

class PassBotFixed:
    def __init__(self):
        self.ui = MatrixUI()
        self.live = LiveStats()
        self.input: Optional[InputProfile] = None
        self.generated: Set[str] = set()
        self.interrupted = False
        self.progress_pkl = "passbot_progress.pkl"
        self.backup_interval = 5000
        self.current_phase = 1
        self.phase_position = 0
        # Separators: only empty by default. Optional underscore if user allows. No '.' or '-'.
        self.separators: List[str] = [""]
        signal.signal(signal.SIGINT, self._on_interrupt)
        # Output handle for incremental write
        self._out = None

    # ---------- Persistence ----------
    def _on_interrupt(self, *_):
        print(f"\n{Colors.YELLOW}[🛑] Interrupt detected — flushing output and saving progress...{Colors.RESET}")
        self.interrupted = True
        try:
            if self._out and not self._out.closed:
                self._out.flush()
                os.fsync(self._out.fileno())
        except Exception:
            pass
        self._save_progress()

    def _save_progress(self):
        try:
            state = ProgressState(
                generated_passwords=self.generated.copy(),
                current_phase=self.current_phase,
                phase_position=self.phase_position,
                total_generated=len(self.generated),
                generation_start_time=self.live.start_time,
                last_save_time=time.time(),
                input_profile_data=asdict(self.input) if self.input else {}
            )
            with open(self.progress_pkl, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            print(f"{Colors.RED}[❌] Failed to save progress: {e}{Colors.RESET}")

    def _load_progress(self) -> bool:
        try:
            if not os.path.exists(self.progress_pkl):
                return False
            with open(self.progress_pkl, 'rb') as f:
                state: ProgressState = pickle.load(f)
            self.generated = state.generated_passwords
            self.current_phase = state.current_phase
            self.phase_position = state.phase_position
            self.live.start_time = state.generation_start_time or time.time()
            if state.input_profile_data:
                self.input = InputProfile(**state.input_profile_data)
            print(f"{Colors.BRIGHT_GREEN}[📂] Resumed: {len(self.generated):,} passwords{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.YELLOW}[⚠️] Could not load previous progress: {e}{Colors.RESET}")
            return False

    # ---------- Inputs ----------
    def _clean_variants(self, word: str) -> List[str]:
        return list({word.lower(), word.upper(), word.capitalize()})

    def _extract_mobile_frags(self, mobile: str) -> List[str]:
        mobile = re.sub(r"\D", "", mobile)
        frags = set()
        for s in range(len(mobile)):
            for e in range(s+2, min(s+11, len(mobile)+1)):
                fr = mobile[s:e]
                if len(fr) >= 2:
                    frags.add(fr)
        return list(frags)

    def _parse_date_frags(self, dob: str) -> List[str]:
        s = re.sub(r"[/\-\s]", "", dob)
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
            combos3 = [f"{d}{m}{y2}", f"{d}{m}{y}", f"{m}{d}{y2}", f"{m}{d}{y}", f"{y2}{d}{m}", f"{y}{d}{m}"]
            out.update(combos3)
        return list(out)

    def _gen_num_patterns(self, p: str) -> List[str]:
        s = set()
        if p == "00":
            for i in range(100): s.add(f"{i:02d}")
        elif p == "000":
            for i in range(1000): s.add(f"{i:03d}")
        elif p == "0000":
            for i in range(10000): s.add(f"{i:04d}")
        elif p == "00000":
            for i in range(0, 100000, 100): s.add(f"{i:05d}")
        return list(s)

    def _estimate_total(self, words: List[str], numbers: List[str], specials: List[str]) -> int:
        # With separators only "" or "_" optionally
        seps = self.separators
        total = 0
        # 1-element
        total += len(words) + len(numbers)
        # 2-element
        total += len(words)*len(numbers)*len(seps)*2 if words and numbers else 0
        total += len(words)*len(specials)*len(seps)*2 if words and specials else 0
        total += len(numbers)*len(specials)*len(seps)*2 if numbers and specials else 0
        total += (len(words)*(len(words)-1))*len(seps) if len(words) >= 2 else 0
        # 3-element (subset typical)
        total += len(words)*len(numbers)*len(specials)*len(seps)*len(seps)*6 if (words and numbers and specials) else 0
        total += len(words)*(len(words)-1)*len(numbers)*len(seps)*len(seps)*3 if (len(words) >= 2 and numbers) else 0
        return total

    def collect_inputs(self) -> InputProfile:
        print(f"{Colors.CYAN}Starting input collection...{Colors.RESET}")
        if RICH_AVAILABLE:
            words_input = Prompt.ask("Enter words (comma-separated)").strip()
        else:
            words_input = input("Words (comma-separated): ").strip()
        words = [w.strip().lower() for w in words_input.split(',') if w.strip()]

        mobiles = []
        if RICH_AVAILABLE:
            mi = Prompt.ask("Enter mobile numbers (comma-separated, optional)", default="").strip()
        else:
            mi = input("Mobile numbers (optional): ").strip()
        if mi:
            for m in [x.strip() for x in mi.split(',') if x.strip()]:
                mobiles.extend(self._extract_mobile_frags(m))

        if RICH_AVAILABLE:
            dob = Prompt.ask("Enter date of birth (optional)", default="").strip()
        else:
            dob = input("DOB (optional): ").strip()
        date_frags = self._parse_date_frags(dob) if dob else []

        if RICH_AVAILABLE:
            yr = Prompt.ask("Enter year range YYYY-YYYY (optional)", default="").strip()
        else:
            yr = input("Year range YYYY-YYYY (optional): ").strip()
        years = []
        if yr and '-' in yr:
            try:
                a, b = yr.split('-')
                a, b = int(a), int(b)
                if 1900 <= a <= b <= 2035:
                    years = [str(y) for y in range(a, b+1)]
            except: pass

        if RICH_AVAILABLE:
            sc = Prompt.ask("Enter YOUR special characters (comma-separated, optional)", default="").strip()
        else:
            sc = input("Your special chars (optional): ").strip()
        specials = [c.strip() for c in sc.split(',') if c.strip()]

        # Ask underscore preference
        allow_underscore = False
        if RICH_AVAILABLE:
            allow_underscore = Confirm.ask("Allow underscore '_' as separator?", default=False)
        else:
            ans = input("Allow underscore '_' as separator? (y/N): ").strip().lower()
            allow_underscore = ans in ("y", "yes", "1", "true")
        self.separators = [""] + (["_"] if allow_underscore else [])

        if RICH_AVAILABLE:
            out = Prompt.ask("Output filename", default="passbot_final_dictionary.txt")
        else:
            out = input("Output filename [passbot_final_dictionary.txt]: ").strip() or "passbot_final_dictionary.txt"
        if not out.endswith('.txt'):
            out += '.txt'

        print(f"{Colors.CYAN}Continuous full generation enabled. Press Ctrl+C to stop; progress will be saved to output file.{Colors.RESET}")
        return InputProfile(
            words=words,
            mobile_numbers=mobiles,
            date_fragments=date_frags,
            year_ranges=years,
            special_chars=specials,
            number_patterns=[],
            output_filename=out,
            allow_underscore=allow_underscore,
            complete_generation=True,
        )

    # ---------- Generation ----------
    def _update_stats(self, cur: str, phase: str):
        self.live.current_password = cur
        self.live.current_phase = phase
        self.live.passwords_generated = len(self.generated)
        elapsed = max(1e-6, time.time() - self.live.start_time)
        self.live.generation_rate = self.live.passwords_generated / elapsed
        self.live.memory_usage_mb = SystemMonitor.mem_mb()
        self.live.disk_space_gb = SystemMonitor.disk_gb()
        if self.live.estimated_total > 0:
            rem = max(0, self.live.estimated_total - self.live.passwords_generated)
            if self.live.generation_rate > 0:
                self.live.eta_seconds = rem / self.live.generation_rate

    def _write_password(self, pw: str):
        if pw and pw not in self.generated:
            self.generated.add(pw)
            if self._out:
                self._out.write(pw + "\n")
                if len(self.generated) % 1000 == 0:
                    self._out.flush()
                    os.fsync(self._out.fileno())

    def _generate(self, words: List[str], numbers: List[str], specials: List[str], layout):
        # Phase 1: Single words
        phase_name = "Phase 1/7: Single words"
        for i, w in enumerate(words):
            if self.interrupted: return
            if i >= self.phase_position:
                for v in {w.lower(), w.upper(), w.capitalize()}:
                    self._write_password(v)
                self.phase_position = i + 1
                if len(self.generated) % 200 == 0:
                    self._update_stats(w, phase_name)
                    if layout: self.ui.update(layout, self.live)
                if len(self.generated) % self.backup_interval == 0:
                    self._save_progress()
        self.current_phase, self.phase_position = 2, 0

        # Phase 2: Single numbers
        phase_name = "Phase 2/7: Single numbers"
        for i, n in enumerate(numbers):
            if self.interrupted: return
            if i >= self.phase_position:
                self._write_password(str(n))
                self.phase_position = i + 1
                if len(self.generated) % 200 == 0:
                    self._update_stats(str(n), phase_name)
                    if layout: self.ui.update(layout, self.live)
                if len(self.generated) % self.backup_interval == 0:
                    self._save_progress()
        self.current_phase, self.phase_position = 3, 0

        seps = self.separators

        # Phase 3: Word + Number (both orders)
        phase_name = "Phase 3/7: Word+Number"
        combo_idx = 0
        for w in words:
            if self.interrupted: return
            for n in numbers:
                if self.interrupted: return
                for s in seps:
                    if self.interrupted: return
                    combos = [f"{w}{s}{n}", f"{n}{s}{w}"]
                    for c in combos:
                        if self.interrupted: return
                        if combo_idx >= self.phase_position:
                            self._write_password(c)
                            if len(self.generated) % 200 == 0:
                                self._update_stats(c, phase_name)
                                if layout: self.ui.update(layout, self.live)
                            if len(self.generated) % self.backup_interval == 0:
                                self._save_progress()
                        combo_idx += 1
                        self.phase_position = combo_idx
        self.current_phase, self.phase_position = 4, 0

        # Phase 4: Word + Special
        if specials:
            phase_name = "Phase 4/7: Word+Special"
            combo_idx = 0
            for w in words:
                if self.interrupted: return
                for sp in specials:
                    for s in seps:
                        combos = [f"{w}{s}{sp}", f"{sp}{s}{w}"]
                        for c in combos:
                            if combo_idx >= self.phase_position:
                                self._write_password(c)
                                if len(self.generated) % 200 == 0:
                                    self._update_stats(c, phase_name)
                                    if layout: self.ui.update(layout, self.live)
                                if len(self.generated) % self.backup_interval == 0:
                                    self._save_progress()
                            combo_idx += 1
                            self.phase_position = combo_idx
        self.current_phase, self.phase_position = 5, 0

        # Phase 5: Number + Special
        if specials:
            phase_name = "Phase 5/7: Number+Special"
            combo_idx = 0
            for n in numbers:
                if self.interrupted: return
                for sp in specials:
                    for s in seps:
                        combos = [f"{n}{s}{sp}", f"{sp}{s}{n}"]
                        for c in combos:
                            if combo_idx >= self.phase_position:
                                self._write_password(c)
                                if len(self.generated) % 200 == 0:
                                    self._update_stats(c, phase_name)
                                    if layout: self.ui.update(layout, self.live)
                                if len(self.generated) % self.backup_interval == 0:
                                    self._save_progress()
                            combo_idx += 1
                            self.phase_position = combo_idx
        self.current_phase, self.phase_position = 6, 0

        # Phase 6: Word + Word
        phase_name = "Phase 6/7: Word+Word"
        combo_idx = 0
        for i, w1 in enumerate(words):
            if self.interrupted: return
            for j, w2 in enumerate(words):
                if i == j: continue
                for s in seps:
                    c = f"{w1}{s}{w2}"
                    if combo_idx >= self.phase_position:
                        self._write_password(c)
                        if len(self.generated) % 200 == 0:
                            self._update_stats(c, phase_name)
                            if layout: self.ui.update(layout, self.live)
                        if len(self.generated) % self.backup_interval == 0:
                            self._save_progress()
                    combo_idx += 1
                    self.phase_position = combo_idx
        self.current_phase, self.phase_position = 7, 0

        # Phase 7: Three elements (subset)
        phase_name = "Phase 7/7: 3-Element"
        combo_idx = 0
        for w in words:
            if self.interrupted: return
            for n in numbers:
                for s1 in seps:
                    for s2 in seps:
                        combos = [
                            f"{w}{s1}{n}{s2}",
                            f"{n}{s1}{w}{s2}",
                        ]
                        for c in combos:
                            if combo_idx >= self.phase_position:
                                self._write_password(c)
                                if len(self.generated) % 200 == 0:
                                    self._update_stats(c, phase_name)
                                    if layout: self.ui.update(layout, self.live)
                                if len(self.generated) % self.backup_interval == 0:
                                    self._save_progress()
                            combo_idx += 1
                            self.phase_position = combo_idx

    def generate(self, profile: InputProfile):
        self.input = profile
        self.live.start_time = time.time()
        self.live.output_file = profile.output_filename

        # Build elements
        words = sorted({v for w in profile.words for v in (w.lower(), w.upper(), w.capitalize())})
        numbers = sorted(set(profile.mobile_numbers + profile.date_fragments + profile.year_ranges + profile.number_patterns))
        specials = sorted(set(profile.special_chars))

        self.live.estimated_total = self._estimate_total(words, numbers, specials)

        # Open output for incremental write; if resuming, avoid duplications by reading existing file into set
        append_mode = 'a' if os.path.exists(profile.output_filename) else 'w'
        if append_mode == 'a':
            try:
                with open(profile.output_filename, 'r', encoding='utf-8', errors='ignore') as rf:
                    for line in rf:
                        pw = line.rstrip('\n')
                        if pw and not pw.startswith('#'):
                            self.generated.add(pw)
            except Exception:
                pass
        self._out = open(profile.output_filename, append_mode, encoding='utf-8')

        layout = self.ui.layout() if RICH_AVAILABLE else None
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2) as live:
                    self._update_stats("", "Initializing")
                    self.ui.update(layout, self.live)
                    self._generate(words, numbers, specials, layout)
            else:
                self._generate(words, numbers, specials, None)
        finally:
            try:
                if self._out and not self._out.closed:
                    self._out.flush()
                    os.fsync(self._out.fileno())
                    self._out.close()
            except Exception:
                pass

        if self.interrupted:
            print(f"{Colors.YELLOW}🔄 Generation interrupted. Progress saved in: {profile.output_filename}{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_GREEN}✅ Generation complete. Output saved to: {profile.output_filename}{Colors.RESET}")
            # Clean progress state on successful completion
            try:
                if os.path.exists(self.progress_pkl):
                    os.remove(self.progress_pkl)
            except Exception:
                pass

    def run(self):
        # Resume?
        resumed = False
        if os.path.exists(self.progress_pkl):
            if RICH_AVAILABLE:
                resume = Confirm.ask("Previous progress found. Resume?", default=True)
            else:
                resume = (input("Previous progress found. Resume? (Y/n): ").strip().lower() not in ("n", "no", "0"))
            if resume:
                resumed = self._load_progress()

        if not resumed:
            self.input = self.collect_inputs()

        self.generate(self.input)


def main():
    bot = PassBotFixed()
    bot.run()

if __name__ == "__main__":
    sys.exit(main())
