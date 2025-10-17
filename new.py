#!/usr/bin/env python3
"""
Pass-Bot Enterprise Personal Dictionary Generator (NEW Full Pipeline)
=====================================================================

This script restores the complete generation pipeline with:
- Big banner UI and live monitoring
- Safe Ctrl+C with resume
- Incremental output saving
- Strict separator policy: NO '-' or '.', optional '_'
- Inputs: words, mobiles (fragments), DOB fragments, year ranges, user specials, number patterns (00/000/0000)
- Phases 1–7: Single, pairwise, and three-element combos
- Modes: full (all) vs strong (complexity score ≥ 60)
- No leet/number injection inside words; only clean case variants

Usage:
  python new.py
"""

import os, sys, re, time, math, signal, pickle, shutil, psutil
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

class NewPassBot:
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
    # Helpers
    def _variants(self, w:str)->List[str]:
        return list({w.lower(), w.upper(), w.capitalize()})
    def _extract_mobile_frags(self, mobile:str)->List[str]:
        m=re.sub(r"\D","", mobile); fr=set()
        for s in range(len(m)):
            for e in range(s+2, min(s+11, len(m)+1)):
                fr.add(m[s:e])
        return list(fr)
    def _parse_dob(self, dob:str)->List[str]:
        s=re.sub(r"[/\-\s]","", dob); out=set()
        if len(s)==8 and s.isdigit():
            d,m,y=s[:2],s[2:4],s[4:]; y2=y[-2:]
            parts=[d,m,y,y2]
            out.update(parts)
            for i,a in enumerate(parts):
                for j,b in enumerate(parts):
                    if i!=j: out.add(f"{a}{b}")
            out.update([f"{d}{m}{y2}", f"{d}{m}{y}", f"{m}{d}{y2}", f"{m}{d}{y}", f"{y2}{d}{m}", f"{y}{d}{m}"])
        return list(out)
    def _gen_patterns(self, p:str)->List[str]:
        s=set()
        if p=="00":
            for i in range(100): s.add(f"{i:02d}")
        elif p=="000":
            for i in range(1000): s.add(f"{i:03d}")
        elif p=="0000":
            for i in range(10000): s.add(f"{i:04d}")
        return list(s)
    # Output
    def _write(self, pw:str):
        if pw in self.generated: return
        if self.input and self.input.generation_mode=="strong" and Strength.score(pw)<60: return
        self.generated.add(pw)
        if self._out: self._out.write(pw+"\n")
        if len(self.generated)%1000==0 and self._out:
            try: self._out.flush(); os.fsync(self._out.fileno())
            except: pass
        if len(self.generated)%5000==0: self._save_progress()
    def _update_stats(self, cur:str, phase:str):
        self.live.current_password=cur; self.live.current_phase=phase; self.live.passwords_generated=len(self.generated)
        elapsed=max(1e-6,time.time()-self.live.start_time); self.live.generation_rate=self.live.passwords_generated/elapsed
        self.live.memory_usage_mb=self._mem(); self.live.disk_space_gb=self._disk()
    # Collection
    def collect_user_inputs(self)->InputProfile:
        words_input = Prompt.ask("Enter words (comma-separated)").strip() if RICH_AVAILABLE else input("Enter words (comma-separated): ").strip()
        words=[w.strip().lower() for w in words_input.split(',') if w.strip()]
        mi = Prompt.ask("Enter mobile numbers (comma-separated, optional)", default="").strip() if RICH_AVAILABLE else input("Mobile numbers (optional): ").strip()
        mobiles=[]
        if mi:
            for m in [x.strip() for x in mi.split(',') if x.strip()]: mobiles.extend(self._extract_mobile_frags(m))
        dob = Prompt.ask("Enter date of birth (optional)", default="").strip() if RICH_AVAILABLE else input("DOB (optional): ").strip()
        dobf = self._parse_dob(dob) if dob else []
        yr = Prompt.ask("Enter year range YYYY-YYYY (optional)", default="").strip() if RICH_AVAILABLE else input("Year range YYYY-YYYY (optional): ").strip()
        years=[]
        if yr and '-' in yr:
            try:
                a,b=yr.split('-'); a,b=int(a),int(b)
                if 1900<=a<=b<=2035: years=[str(y) for y in range(a,b+1)]
            except: pass
        sc = Prompt.ask("Enter YOUR special characters (comma-separated, optional)", default="").strip() if RICH_AVAILABLE else input("Your special chars (optional): ").strip()
        specials=[c.strip() for c in sc.split(',') if c.strip()] if sc else []
        allow_underscore = Confirm.ask("Allow '_' as separator?", default=False) if RICH_AVAILABLE else (input("Allow '_' as separator? (y/N): ").strip().lower() in ("y","yes","1"))
        self.separators=[""] + (["_"] if allow_underscore else [])
        pat = Prompt.ask("Enter number patterns (choose from 00,000,0000; comma-separated, optional)", default="").strip() if RICH_AVAILABLE else input("Number patterns 00,000,0000 (optional): ").strip()
        patterns=[]
        if pat:
            for p in [x.strip() for x in pat.split(',') if x.strip()]: patterns.extend(self._gen_patterns(p))
        out = Prompt.ask("Output filename", default="passbot_final_dictionary.txt") if RICH_AVAILABLE else (input("Output filename [passbot_final_dictionary.txt]: ").strip() or "passbot_final_dictionary.txt")
        mode = Prompt.ask("Mode (full/strong)", choices=["full","strong"], default="full") if RICH_AVAILABLE else (input("Mode (full/strong) [full]: ").strip().lower() or "full")
        return InputProfile(words=words, mobile_numbers=mobiles, date_fragments=dobf, year_ranges=years, special_chars=specials, number_patterns=patterns, output_filename=out, generation_mode=mode)
    # Generation
    def _generate(self, words:List[str], numbers:List[str], specials:List[str], layout):
        # Phase 1: Single words
        if self.current_phase==1:
            phase="Phase 1/7: Single words"
            for i,w in enumerate(words):
                if self.interrupted: return
                if i<self.phase_position: continue
                self._write(w); self.phase_position=i+1
                if len(self.generated)%200==0: self._update_stats(w, phase); self.ui.update(layout, self.live)
            self.current_phase=2; self.phase_position=0
        # Phase 2: Single numbers
        if self.current_phase==2:
            phase="Phase 2/7: Single numbers"
            for i,n in enumerate(numbers):
                if self.interrupted: return
                if i<self.phase_position: continue
                self._write(str(n)); self.phase_position=i+1
                if len(self.generated)%200==0: self._update_stats(str(n), phase); self.ui.update(layout, self.live)
            self.current_phase=3; self.phase_position=0
        # Phase 3: Word + Number (both orders)
        if self.current_phase==3:
            phase="Phase 3/7: Word+Number"
            idx=0
            for w in words:
                if self.interrupted: return
                for n in numbers:
                    for s in self.separators:
                        if idx<self.phase_position: idx+=2; continue
                        a=f"{w}{s}{n}"; b=f"{n}{s}{w}"; self._write(a); self._write(b)
                        if len(self.generated)%200==0: self._update_stats(a, phase); self.ui.update(layout, self.live)
                        idx+=2; self.phase_position=idx
            self.current_phase=4; self.phase_position=0
        # Phase 4: Word + Special
        if self.current_phase==4 and specials:
            phase="Phase 4/7: Word+Special"
            idx=0
            for w in words:
                if self.interrupted: return
                for sp in specials:
                    for s in self.separators:
                        if idx<self.phase_position: idx+=2; continue
                        a=f"{w}{s}{sp}"; b=f"{sp}{s}{w}"; self._write(a); self._write(b)
                        if len(self.generated)%200==0: self._update_stats(a, phase); self.ui.update(layout, self.live)
                        idx+=2; self.phase_position=idx
            self.current_phase=5; self.phase_position=0
        else:
            if self.current_phase==4: self.current_phase=5; self.phase_position=0
        # Phase 5: Number + Special
        if self.current_phase==5 and specials:
            phase="Phase 5/7: Number+Special"
            idx=0
            for n in numbers:
                if self.interrupted: return
                for sp in specials:
                    for s in self.separators:
                        if idx<self.phase_position: idx+=2; continue
                        a=f"{n}{s}{sp}"; b=f"{sp}{s}{n}"; self._write(a); self._write(b)
                        if len(self.generated)%200==0: self._update_stats(a, phase); self.ui.update(layout, self.live)
                        idx+=2; self.phase_position=idx
            self.current_phase=6; self.phase_position=0
        else:
            if self.current_phase==5: self.current_phase=6; self.phase_position=0
        # Phase 6: Word + Word
        if self.current_phase==6 and len(words)>=2:
            phase="Phase 6/7: Word+Word"
            idx=0
            for i,a in enumerate(words):
                if self.interrupted: return
                for j,b in enumerate(words):
                    if i==j: continue
                    for s in self.separators:
                        if idx<self.phase_position: idx+=1; continue
                        pw=f"{a}{s}{b}"; self._write(pw)
                        if len(self.generated)%200==0: self._update_stats(pw, phase); self.ui.update(layout, self.live)
                        idx+=1; self.phase_position=idx
            self.current_phase=7; self.phase_position=0
        else:
            if self.current_phase==6: self.current_phase=7; self.phase_position=0
        # Phase 7: Three-element (Word+Number+Special; Word+Word+Number)
        if self.current_phase==7:
            phase="Phase 7/7: Three-element"
            idx=0
            if words and numbers and specials:
                for w in words:
                    if self.interrupted: return
                    for n in numbers:
                        for sp in specials:
                            for s1 in self.separators:
                                for s2 in self.separators:
                                    combos=[f"{w}{s1}{n}{s2}{sp}", f"{w}{s1}{sp}{s2}{n}", f"{n}{s1}{w}{s2}{sp}", f"{n}{s1}{sp}{s2}{w}", f"{sp}{s1}{w}{s2}{n}", f"{sp}{s1}{n}{s2}{w}"]
                                    for c in combos:
                                        if idx<self.phase_position: idx+=1; continue
                                        self._write(c); 
                                        if len(self.generated)%200==0: self._update_stats(c, phase); self.ui.update(layout, self.live)
                                        idx+=1; self.phase_position=idx
            if len(words)>=2 and numbers:
                for i,a in enumerate(words):
                    if self.interrupted: return
                    for j,b in enumerate(words):
                        if i==j: continue
                        for n in numbers:
                            for s1 in self.separators:
                                for s2 in self.separators:
                                    combos=[f"{a}{s1}{b}{s2}{n}", f"{a}{s1}{n}{s2}{b}", f"{n}{s1}{a}{s2}{b}"]
                                    for c in combos:
                                        if idx<self.phase_position: idx+=1; continue
                                        self._write(c)
                                        if len(self.generated)%200==0: self._update_stats(c, phase); self.ui.update(layout, self.live)
                                        idx+=1; self.phase_position=idx
    # Run
    def run(self)->int:
        if RICH_AVAILABLE:
            self.ui.banner(); self.ui.loading("Initializing Pass-Bot FIXED Generation Suite", 2.0)
        resumed=False
        if os.path.exists(self.progress_pkl):
            res = Confirm.ask("Previous progress found. Resume?", default=True) if RICH_AVAILABLE else (input("Previous progress found. Resume? (Y/n): ").strip().lower() not in ("n","no","0"))
            if res: resumed=self._load_progress()
        if not resumed:
            self.input=self.collect_user_inputs()
        # Prepare lists
        words=sorted({v for w in self.input.words for v in self._variants(w)})
        numbers=sorted(set(self.input.mobile_numbers + self.input.date_fragments + self.input.year_ranges + self.input.number_patterns))
        specials=sorted(set(self.input.special_chars))
        # Open output
        try:
            self._out=open(self.input.output_filename, 'a' if os.path.exists(self.input.output_filename) else 'w', encoding='utf-8')
        except Exception as e:
            print(f"{Colors.RED}[❌] Cannot open output: {e}{Colors.RESET}"); return 1
        # Stats
        self.live.start_time=time.time(); self.live.output_file=self.input.output_filename
        self.live.estimated_total = len(words) + len(numbers) + (len(words)*len(numbers)*len(self.separators)*2) + (len(words)*max(0,len(words)-1)*len(self.separators))
        layout=self.ui.layout() if RICH_AVAILABLE else None
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2):
                    self._generate(words, numbers, specials, layout)
            else:
                self._generate(words, numbers, specials, None)
        finally:
            try:
                if self._out: self._out.flush(); os.fsync(self._out.fileno()); self._out.close()
            except: pass
        print(f"{Colors.GREEN}✅ Generation finished or interrupted. Output: {self.input.output_filename}{Colors.RESET}")
        return 0


def main():
    bot=NewPassBot(); return bot.run()

if __name__=='__main__':
    sys.exit(main())
