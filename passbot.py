#!/usr/bin/env python3
"""
Pass-Bot Enterprise Personal Dictionary Generator (Fixed Version)
===============================================================

🕷️ Professional brute force dictionary generator for security testing
Built with Gen-Spider level enterprise architecture and quality standards

This file is the single executable entrypoint. It includes:
- Live UI/animations and enterprise banner
- Safe Ctrl+C with resume
- Incremental output saving
- Separator control (NO '-' or '.'; optional '_')
- Full vs Strong modes

Version: 1.2.3 Fixed
License: MIT
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
from dataclasses import dataclass, asdict
from typing import List, Set, Optional, Dict
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

# Colors
class Colors:
    GREEN='\033[92m'; YELLOW='\033[93m'; RED='\033[91m'; CYAN='\033[96m'; RESET='\033[0m'; BRIGHT='\033[1m'

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
    generation_mode: str = "full"  # full or strong

class MatrixUI:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
    def banner(self):
        if RICH_AVAILABLE:
            art = """
[bright_green]
╔══════════════════════════════════════════════════════════════════════════════╗
║            🕷️  ENTERPRISE PERSONAL DICTIONARY GENERATOR  🕷️                  ║
║                   🎯 FIXED VERSION - NO SEPARATORS + MODES 🎯               ║
╚══════════════════════════════════════════════════════════════════════════════╝
[/bright_green]
"""
            panel = Panel(Align.center(Text(art, style="bright_green")), title="[bold red]PASS-BOT ENTERPRISE[/bold red]", border_style="red")
            self.console.print(panel)
        else:
            print(f"{Colors.BRIGHT}PASS-BOT ENTERPRISE{Colors.RESET}")
    def loading(self, msg: str, seconds: float = 2.0):
        if RICH_AVAILABLE:
            with Progress(SpinnerColumn("dots12", style="bright_green"), TextColumn("[bright_green]{task.description}"), console=self.console) as p:
                t = p.add_task(msg, total=100)
                for _ in range(100):
                    p.update(t, advance=1); time.sleep(seconds/100)
        else:
            print(msg + "...")
    def layout(self):
        if not RICH_AVAILABLE: return None
        layout = Layout(); layout.split(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))
        layout["main"].split_row(Layout(name="stats", ratio=2), Layout(name="progress", ratio=3))
        return layout
    def update(self, layout: Layout, stats: LiveStats):
        if not (RICH_AVAILABLE and layout): return
        layout["header"].update(Panel(f"[bold green]🎯 LIVE - {datetime.now().strftime('%H:%M:%S')}[/bold green]"))
        t = Table(show_header=False); t.add_column("Metric", style="cyan"); t.add_column("Value", style="bright_green")
        elapsed = time.time()-stats.start_time; eta = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds>0 else "Calculating..."
        t.add_row("🔐 Generated", f"{stats.passwords_generated:,}"); t.add_row("⚡ Rate", f"{stats.generation_rate:.1f}/sec"); t.add_row("📝 Current", stats.current_password[:40]); t.add_row("🎯 Phase", stats.current_phase); t.add_row("⏱️ Elapsed", str(timedelta(seconds=int(elapsed)))); t.add_row("⏳ ETA", eta); t.add_row("💾 Memory", f"{stats.memory_usage_mb:.1f} MB"); t.add_row("💽 Disk", f"{stats.disk_space_gb:.1f} GB")
        layout["stats"].update(Panel(t, title="📊 Statistics"))
        if stats.estimated_total>0:
            pct = min(100.0, (stats.passwords_generated/max(1,stats.estimated_total))*100.0); bar = "█"*int(pct/2) + "░"*(50-int(pct/2))
            layout["progress"].update(Panel(f"Progress: {pct:.1f}% [{bar}]\n{stats.passwords_generated:,}/{stats.estimated_total:,}\n\n{stats.current_password}", title="⚡ Live Progress"))
        else:
            layout["progress"].update(Panel(f"Generated: {stats.passwords_generated:,}\n\n{stats.current_password}", title="⚡ Live Progress"))
        layout["footer"].update(Panel(f"Press Ctrl+C to stop safely | Output: {stats.output_file}"))

class Strength:
    @staticmethod
    def entropy(pw: str) -> float:
        if not pw: return 0.0
        counts=defaultdict(int); [counts.__setitem__(c, counts[c]+1) for c in pw]
        n=len(pw); e=0.0
        for k in counts.values():
            p=k/n; e -= p*math.log2(max(p,1e-12))
        return e*n
    @staticmethod
    def score(pw: str) -> float:
        n=len(pw); s=0.0
        s += 30 if n>=20 else 25 if n>=16 else 20 if n>=12 else 15 if n>=8 else n*1.5
        kinds = sum([any(c.islower() for c in pw), any(c.isupper() for c in pw), any(c.isdigit() for c in pw), any(not c.isalnum() for c in pw)])
        s += kinds*10; s += min(30, (Strength.entropy(pw)/6.0)*30)
        if re.search(r"(.)\1{2,}", pw): s -= 15
        if re.search(r"(abc|123|qwe)", pw.lower()): s -= 10
        if re.search(r"(password|admin|user|test)", pw.lower()): s -= 20
        return max(0,min(100,s))

class PassBot:
    def __init__(self):
        self.ui = MatrixUI(); self.live=LiveStats(); self.input: Optional[InputProfile]=None
        self.generated:Set[str]=set(); self.progress_pkl="passbot_progress.pkl"; self.current_phase=1; self.phase_position=0
        self.backup_interval=5000; self.separators:[str] = [""]
        self._out=None; self.interrupted=False
        signal.signal(signal.SIGINT, self._on_interrupt)
    # System
    def _mem(self):
        try: return psutil.Process(os.getpid()).memory_info().rss/1024/1024
        except: return 0.0
    def _disk(self):
        try: return shutil.disk_usage('.').free/1024/1024/1024
        except: return 0.0
    def _on_interrupt(self,*_):
        print(f"\n{Colors.YELLOW}[🛑] Interrupt — flushing & saving...{Colors.RESET}"); self.interrupted=True
        try:
            if self._out and not self._out.closed: self._out.flush(); os.fsync(self._out.fileno())
        except: pass
        self._save_progress()
    def _save_progress(self):
        try:
            st=ProgressState(self.generated.copy(), self.current_phase, self.phase_position, len(self.generated), self.live.start_time, time.time(), asdict(self.input) if self.input else {})
            with open(self.progress_pkl,'wb') as f: pickle.dump(st,f)
        except Exception as e:
            print(f"{Colors.RED}[❌] Save failed: {e}{Colors.RESET}")
    def _load_progress(self)->bool:
        try:
            if not os.path.exists(self.progress_pkl): return False
            with open(self.progress_pkl,'rb') as f: st:ProgressState=pickle.load(f)
            self.generated=st.generated_passwords; self.current_phase=st.current_phase; self.phase_position=st.phase_position; self.live.start_time=st.generation_start_time or time.time()
            if st.input_profile_data: self.input=InputProfile(**st.input_profile_data)
            print(f"{Colors.GREEN}[📂] Resumed: {len(self.generated):,} passwords{Colors.RESET}"); return True
        except Exception as e:
            print(f"{Colors.YELLOW}[⚠️] Resume failed: {e}{Colors.RESET}"); return False
    # Inputs
    def collect_user_inputs(self)->InputProfile:
        words_input = Prompt.ask("Enter words (comma-separated)").strip() if RICH_AVAILABLE else input("Enter words (comma-separated): ").strip()
        words=[w.strip().lower() for w in words_input.split(',') if w.strip()]
        allow_underscore = Confirm.ask("Allow '_' as separator?", default=False) if RICH_AVAILABLE else (input("Allow '_' as separator? (y/N): ").strip().lower() in ("y","yes","1"))
        self.separators=[""] + (["_"] if allow_underscore else [])
        out = Prompt.ask("Output filename", default="passbot_final_dictionary.txt") if RICH_AVAILABLE else (input("Output filename [passbot_final_dictionary.txt]: ").strip() or "passbot_final_dictionary.txt")
        mode = Prompt.ask("Mode (full/strong)", choices=["full","strong"], default="full") if RICH_AVAILABLE else (input("Mode (full/strong) [full]: ").strip().lower() or "full")
        return InputProfile(words=words, mobile_numbers=[], date_fragments=[], year_ranges=[], special_chars=[], number_patterns=[], output_filename=out, generation_mode=mode)
    # Live stats
    def _update_stats(self, cur:str, phase:str):
        self.live.current_password=cur; self.live.current_phase=phase; self.live.passwords_generated=len(self.generated)
        elapsed=max(1e-6,time.time()-self.live.start_time); self.live.generation_rate=self.live.passwords_generated/elapsed
        self.live.memory_usage_mb=self._mem(); self.live.disk_space_gb=self._disk()
    # Output writing
    def _write(self, pw:str):
        if pw in self.generated: return
        if self.input and self.input.generation_mode=="strong" and Strength.score(pw)<60: return
        self.generated.add(pw)
        if self._out: self._out.write(pw+"\n");
        if len(self.generated)%1000==0 and self._out:
            try: self._out.flush(); os.fsync(self._out.fileno())
            except: pass
        if len(self.generated)%self.backup_interval==0: self._save_progress()
    # Variations
    def _variants(self, w:str)->List[str]:
        return list({w.lower(), w.upper(), w.capitalize()})
    # Estimate (simple, used just for UI percent)
    def _estimate(self, words:List[str])->int:
        seps=len(self.separators); n=len(words)
        return n + n*(n-1)*seps  # singles + word-word rough estimate
    # Generation Phases (minimal but working)
    def _generate(self, words:List[str], layout):
        count=len(self.generated)
        # Phase 1: single words
        phase="Phase 1/2: Single words"
        for i,w in enumerate(words):
            if self.interrupted: return
            if i<self.phase_position and self.current_phase==1: continue
            self._write(w); self.phase_position=i+1
            if len(self.generated)%200==0:
                self._update_stats(w, phase); self.ui.update(layout, self.live)
        self.current_phase=2; self.phase_position=0
        # Phase 2: word-word with separators
        phase="Phase 2/2: Word+Word"
        combo_idx=0
        for i,a in enumerate(words):
            if self.interrupted: return
            for j,b in enumerate(words):
                if i==j: continue
                for s in self.separators:
                    if self.interrupted: return
                    if combo_idx<self.phase_position and self.current_phase==2:
                        combo_idx+=1; continue
                    pw=f"{a}{s}{b}"; self._write(pw)
                    if len(self.generated)%200==0:
                        self._update_stats(pw, phase); self.ui.update(layout, self.live)
                    combo_idx+=1; self.phase_position=combo_idx
    # Main run
    def run(self)->int:
        if RICH_AVAILABLE:
            self.ui.banner(); self.ui.loading("Initializing Pass-Bot FIXED Generation Suite", 2.0)
        # Resume option
        resumed=False
        if os.path.exists(self.progress_pkl):
            res = Confirm.ask("Previous progress found. Resume?", default=True) if RICH_AVAILABLE else (input("Previous progress found. Resume? (Y/n): ").strip().lower() not in ("n","no","0"))
            if res: resumed=self._load_progress()
        if not resumed:
            self.input=self.collect_user_inputs()
        # Open output
        append = os.path.exists(self.input.output_filename)
        try:
            self._out=open(self.input.output_filename, 'a' if append else 'w', encoding='utf-8')
        except Exception as e:
            print(f"{Colors.RED}[❌] Cannot open output: {e}{Colors.RESET}"); return 1
        # Prepare words
        words=sorted({v for w in self.input.words for v in self._variants(w)})
        self.live.start_time=time.time(); self.live.output_file=self.input.output_filename; self.live.estimated_total=self._estimate(words)
        layout=self.ui.layout() if RICH_AVAILABLE else None
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2):
                    self._generate(words, layout)
            else:
                self._generate(words, None)
        finally:
            try:
                if self._out: self._out.flush(); os.fsync(self._out.fileno()); self._out.close()
            except: pass
        print(f"{Colors.GREEN}✅ Generation finished or interrupted. Output: {self.input.output_filename}{Colors.RESET}")
        return 0


def main():
    bot=PassBot(); return bot.run()

if __name__=='__main__':
    sys.exit(main())
