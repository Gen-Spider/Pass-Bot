#!/usr/bin/env python3
"""
PassBot Enterprise - Complete 9-Chapter Logic Implementation
==========================================================

🕷️ Gen-Spider Enterprise Security Systems
🎯 Professional Password Dictionary Generator

Chapters Implemented:
1. Words Input Logic - Multi-case variations (lower, UPPER, Capitalize)
2. Mobile Numbers Logic - Smart fragment extraction (2-10 digit chunks)
3. Date of Birth Logic - Multiple date format combinations
4. Year Range Logic - Comprehensive year sequences for life events
5. Special Characters Logic - Personal symbol preferences
6. Separator Choice Logic - Clean combinations vs readable with underscores
7. Number Patterns Logic - Systematic number pattern generation (00/000/0000)
8. Generation Mode Logic - Full vs Strong filtering with complexity scoring
9. Resume Logic - Exact checkpoint recovery with phase and position tracking

Usage:
  python passbot.py

Features:
  • Live monitoring dashboard with ETA, memory, disk usage
  • Safe Ctrl+C interrupt with exact resume capability
  • Zero duplicate guarantee across all phases
  • Incremental output saving with real-time progress
  • Interactive prompts with confirmation dialogs
  • Enterprise-grade UI with matrix animations
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
import json
from dataclasses import dataclass, asdict
from typing import List, Set, Optional, Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

# Auto-install required packages
def auto_install_packages():
    required_packages = ['rich', 'colorama', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        import subprocess
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    return True

# Install packages first
if not auto_install_packages():
    print("Failed to install required packages. Please install manually: pip install rich colorama psutil")
    sys.exit(1)

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
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Using fallback UI.")

try:
    import colorama
    colorama.init()
except ImportError:
    pass

# Color definitions
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m' 
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BRIGHT = '\033[1m'
    DIM = '\033[2m'

@dataclass
class LiveStats:
    """Real-time generation statistics"""
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
    """Persistent state for resume functionality"""
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
    """User input configuration"""
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
    """Chapter 8: Generation Mode Logic - Password strength analysis"""
    
    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calculate Shannon entropy for password complexity"""
        if not password:
            return 0.0
            
        char_counts = defaultdict(int)
        for char in password:
            char_counts[char] += 1
            
        length = len(password)
        entropy = 0.0
        
        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(max(probability, 1e-12))
            
        return entropy * length
    
    @staticmethod
    def calculate_score(password: str) -> float:
        """Calculate comprehensive password strength score (0-100)"""
        if not password:
            return 0.0
            
        length = len(password)
        score = 0.0
        
        # Length scoring
        if length >= 20:
            score += 30
        elif length >= 16:
            score += 25
        elif length >= 12:
            score += 20
        elif length >= 8:
            score += 15
        else:
            score += length * 1.5
        
        # Character variety scoring
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        char_variety = sum([has_lower, has_upper, has_digit, has_special])
        score += char_variety * 10
        
        # Entropy bonus
        entropy = PasswordStrength.calculate_entropy(password)
        score += min(30, (entropy / 6.0) * 30)
        
        # Penalties for patterns
        if re.search(r"(.)\1{2,}", password):  # Repeated characters
            score -= 15
        if re.search(r"(abc|123|qwe|password|admin|user|test)", password.lower()):
            score -= 20
        
        return max(0, min(100, score))
    
    @staticmethod
    def is_strong(password: str, threshold: float = 60.0) -> bool:
        """Determine if password meets strength threshold"""
        return PasswordStrength.calculate_score(password) >= threshold

class MatrixUI:
    """Enterprise-grade UI with Gen-Spider brand styling"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def show_banner(self):
        """Display Gen-Spider branded banner"""
        if RICH_AVAILABLE:
            # Gen-Spider brand style banner text
            banner_text = Text(
                "PASSBOT ENTERPRISE SUITE v2.0\n"
                "Professional Password Generation & Analysis System\n"
                "Complete 9-Chapter Logic Implementation",
                style="bold green"
            )
            
            panel = Panel(
                Align.center(banner_text),
                title="[bold red]🔐 GEN-SPIDER SECURITY SYSTEMS 🔐[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(panel)
            
            # Chapter implementation list
            chapters_text = """
[cyan]📋 Implemented Chapters:[/cyan]
[yellow]1. Words Input Logic[/yellow] - Multi-case variations (lower, UPPER, Capitalize)
[yellow]2. Mobile Numbers Logic[/yellow] - Smart fragment extraction (2-10 digits)
[yellow]3. Date of Birth Logic[/yellow] - Multiple format combinations  
[yellow]4. Year Range Logic[/yellow] - Life event year sequences
[yellow]5. Special Characters Logic[/yellow] - Personal symbol preferences
[yellow]6. Separator Choice Logic[/yellow] - Clean vs readable combinations
[yellow]7. Number Patterns Logic[/yellow] - Systematic patterns (00/000/0000)
[yellow]8. Generation Mode Logic[/yellow] - Full vs Strong filtering
[yellow]9. Resume Logic[/yellow] - Exact checkpoint recovery
"""
            self.console.print(chapters_text)
        else:
            print(f"{Colors.BRIGHT}{Colors.GREEN}")
            print("╔" + "="*70 + "╗")
            print("║" + " "*10 + "🔐 GEN-SPIDER SECURITY SYSTEMS 🔐" + " "*10 + "║")
            print("║" + " "*5 + "PASSBOT ENTERPRISE SUITE v2.0" + " "*19 + "║")
            print("║" + " "*2 + "Professional Password Generation & Analysis" + " "*5 + "║")
            print("╚" + "="*70 + "╝")
            print(f"{Colors.RESET}")
    
    def show_loading(self, message: str, duration: float = 2.0):
        """Show animated loading spinner"""
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn("dots12", style="bright_green"),
                TextColumn("[bright_green]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(message, total=100)
                for _ in range(100):
                    progress.update(task, advance=1)
                    time.sleep(duration / 100)
        else:
            print(f"{message}...")
            time.sleep(duration)
    
    def create_live_layout(self) -> Optional[Layout]:
        """Create rich live layout for real-time updates"""
        if not RICH_AVAILABLE:
            return None
            
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=4)
        )
        
        layout["main"].split_row(
            Layout(name="stats", ratio=2),
            Layout(name="progress", ratio=3)
        )
        
        return layout
    
    def update_live_display(self, layout: Layout, stats: LiveStats):
        """Update live display with current statistics"""
        if not (RICH_AVAILABLE and layout):
            return
            
        # Header
        current_time = datetime.now().strftime('%H:%M:%S')
        layout["header"].update(
            Panel(
                f"[bold green]🎯 LIVE GENERATION - {current_time}[/bold green]",
                style="green"
            )
        )
        
        # Statistics table
        stats_table = Table(show_header=False, box=box.SIMPLE)
        stats_table.add_column("Metric", style="cyan", width=15)
        stats_table.add_column("Value", style="bright_green")
        
        elapsed_time = time.time() - stats.start_time
        eta_str = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds > 0 else "Calculating..."
        
        stats_table.add_row("🔐 Generated", f"{stats.passwords_generated:,}")
        stats_table.add_row("⚡ Rate", f"{stats.generation_rate:.1f}/sec")
        stats_table.add_row("📝 Current", stats.current_password[:35] + "..." if len(stats.current_password) > 35 else stats.current_password)
        stats_table.add_row("🎯 Phase", stats.current_phase)
        stats_table.add_row("⏱️ Elapsed", str(timedelta(seconds=int(elapsed_time))))
        stats_table.add_row("⏳ ETA", eta_str)
        stats_table.add_row("💾 Memory", f"{stats.memory_usage_mb:.1f} MB")
        stats_table.add_row("💽 Disk", f"{stats.disk_space_gb:.1f} GB")
        if stats.strong_mode_filtered > 0:
            stats_table.add_row("🛡️ Filtered", f"{stats.strong_mode_filtered:,}")
        
        layout["stats"].update(
            Panel(
                stats_table,
                title="📊 Live Statistics",
                border_style="cyan"
            )
        )
        
        # Progress panel
        if stats.estimated_total > 0:
            progress_percent = min(100.0, (stats.passwords_generated / max(1, stats.estimated_total)) * 100.0)
            progress_bar = "█" * int(progress_percent / 2) + "░" * (50 - int(progress_percent / 2))
            progress_text = f"Progress: {progress_percent:.1f}%\n[{progress_bar}]\n{stats.passwords_generated:,} / {stats.estimated_total:,}\n\n{stats.current_password}"
        else:
            progress_text = f"Generated: {stats.passwords_generated:,}\n\nCurrent Password:\n{stats.current_password}"
        
        layout["progress"].update(
            Panel(
                progress_text,
                title="⚡ Live Progress",
                border_style="yellow"
            )
        )
        
        # Footer
        layout["footer"].update(
            Panel(
                f"Press [bold red]Ctrl+C[/bold red] to stop safely and save progress\n"
                f"Output File: [bold yellow]{stats.output_file}[/bold yellow]\n"
                f"Mode: [bold cyan]{('Strong' if stats.strong_mode_filtered >= 0 else 'Full')}[/bold cyan]",
                style="dim"
            )
        )

class PassBotEnterprise:
    """Main PassBot Enterprise class implementing all 9 chapters"""
    
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
        
        # Setup signal handler for safe interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        """Chapter 9: Optimized safe interrupt handling"""
        print(f"\n{Colors.YELLOW}[🛑] Interrupt received - Safely stopping...{Colors.RESET}")
        self.interrupted = True
        
        # Immediate actions to speed up shutdown
        try:
            # Single flush and fsync
            if self.output_file and not self.output_file.closed:
                self.output_file.flush()
                os.fsync(self.output_file.fileno())
        except Exception:
            pass
        
        # Quick save without heavy processing
        try:
            self._save_progress()
        except Exception:
            pass
    
    def _get_system_stats(self) -> Tuple[float, float]:
        """Get current memory usage and disk space"""
        try:
            memory_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except Exception:
            memory_mb = 0.0
        
        try:
            disk_gb = shutil.disk_usage('.').free / 1024 / 1024 / 1024
        except Exception:
            disk_gb = 0.0
            
        return memory_mb, disk_gb
    
    def _save_progress(self):
        """Chapter 9: Save exact progress state for resume"""
        try:
            progress_state = ProgressState(
                generated_passwords=self.generated_passwords.copy(),
                current_phase=self.current_phase,
                phase_position=self.phase_position,
                total_generated=len(self.generated_passwords),
                generation_start_time=self.stats.start_time,
                last_save_time=time.time(),
                input_profile_data=asdict(self.input_profile) if self.input_profile else {},
                strong_mode_filtered=self.stats.strong_mode_filtered
            )
            
            with open(self.progress_file, 'wb') as f:
                pickle.dump(progress_state, f)
                
        except Exception as e:
            print(f"{Colors.RED}[❌] Failed to save progress: {e}{Colors.RESET}")
    
    def _load_progress(self) -> bool:
        """Chapter 9: Load and restore exact progress state"""
        try:
            if not os.path.exists(self.progress_file):
                return False
                
            with open(self.progress_file, 'rb') as f:
                progress_state: ProgressState = pickle.load(f)
            
            self.generated_passwords = progress_state.generated_passwords
            self.current_phase = progress_state.current_phase
            self.phase_position = progress_state.phase_position
            self.stats.start_time = progress_state.generation_start_time or time.time()
            self.stats.strong_mode_filtered = progress_state.strong_mode_filtered
            
            if progress_state.input_profile_data:
                self.input_profile = InputProfile(**progress_state.input_profile_data)
            
            print(f"{Colors.GREEN}[📂] Progress restored: {len(self.generated_passwords):,} passwords generated{Colors.RESET}")
            print(f"{Colors.CYAN}[📍] Resuming from Phase {self.current_phase}, Position {self.phase_position}{Colors.RESET}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.YELLOW}[⚠️] Failed to load progress: {e}{Colors.RESET}")
            return False
    
    # Chapter 1: Words Input Logic
    def _generate_word_variations(self, word: str) -> List[str]:
        """Generate case variations: lower, UPPER, Capitalize"""
        variations = [
            word.lower(),
            word.upper(),
            word.capitalize()
        ]
        return list(set(variations))  # Remove duplicates
    
    # Chapter 2: Mobile Numbers Logic
    def _extract_mobile_fragments(self, mobile_number: str) -> List[str]:
        """Extract all possible 2-10 digit chunks from mobile number"""
        # Clean mobile number - keep only digits
        clean_mobile = re.sub(r'\D', '', mobile_number)
        
        fragments = set()
        
        # Extract all possible chunks (2-10 digits)
        for start in range(len(clean_mobile)):
            for end in range(start + 2, min(start + 11, len(clean_mobile) + 1)):
                fragment = clean_mobile[start:end]
                if len(fragment) >= 2:  # Minimum 2 digits
                    fragments.add(fragment)
        
        return sorted(list(fragments))
    
    # Chapter 3: Date of Birth Logic
    def _parse_date_of_birth(self, dob_string: str) -> List[str]:
        """Parse DOB and create multiple format combinations"""
        if not dob_string:
            return []
            
        # Clean DOB string - remove separators
        clean_dob = re.sub(r'[/\-\s]', '', dob_string)
        
        date_fragments = set()
        
        # Assume DDMMYYYY format if 8 digits
        if len(clean_dob) == 8 and clean_dob.isdigit():
            day = clean_dob[:2]
            month = clean_dob[2:4]
            year = clean_dob[4:8]
            year_short = clean_dob[6:8]
            
            # Individual components
            components = [day, month, year, year_short]
            date_fragments.update(components)
            
            # Two-component combinations
            for i, comp1 in enumerate(components):
                for j, comp2 in enumerate(components):
                    if i != j:
                        date_fragments.add(f"{comp1}{comp2}")
            
            # Common date formats
            common_formats = [
                f"{day}{month}{year_short}",  # DDMMYY
                f"{day}{month}{year}",       # DDMMYYYY
                f"{month}{day}{year_short}",  # MMDDYY
                f"{month}{day}{year}",       # MMDDYYYY
                f"{year_short}{day}{month}",  # YYDDMM
                f"{year}{day}{month}",       # YYYYDDMM
                f"{year_short}{month}{day}",  # YYMMDD
                f"{year}{month}{day}",       # YYYYMMDD
            ]
            
            date_fragments.update(common_formats)
        
        return sorted(list(date_fragments))
    
    # Chapter 4: Year Range Logic
    def _generate_year_range(self, year_range_string: str) -> List[str]:
        """Generate all years in specified range for life events"""
        if not year_range_string or '-' not in year_range_string:
            return []
            
        try:
            start_year, end_year = year_range_string.split('-')
            start_year = int(start_year.strip())
            end_year = int(end_year.strip())
            
            # Validate reasonable year range
            if 1900 <= start_year <= end_year <= 2035:
                return [str(year) for year in range(start_year, end_year + 1)]
                
        except (ValueError, AttributeError):
            pass
            
        return []
    
    # Chapter 7: Number Patterns Logic
    def _generate_number_patterns(self, pattern: str) -> List[str]:
        """Generate systematic number patterns (00/000/0000)"""
        patterns = set()
        
        if pattern == "00":
            # Generate 00-99
            for i in range(100):
                patterns.add(f"{i:02d}")
        elif pattern == "000":
            # Generate 000-999
            for i in range(1000):
                patterns.add(f"{i:03d}")
        elif pattern == "0000":
            # Generate 0000-9999
            for i in range(10000):
                patterns.add(f"{i:04d}")
        
        return sorted(list(patterns))
    
    def _collect_user_inputs(self) -> InputProfile:
        """Interactive input collection with all options"""
        print(f"\n{Colors.CYAN}📝 PassBot Input Collection{Colors.RESET}\n")
        
        # Chapter 1: Words Input
        if RICH_AVAILABLE:
            words_input = Prompt.ask("[cyan]💬 Enter base words (comma-separated)[/cyan]").strip()
        else:
            words_input = input(f"{Colors.CYAN}💬 Enter base words (comma-separated): {Colors.RESET}").strip()
        
        words = [word.strip().lower() for word in words_input.split(',') if word.strip()]
        
        # Chapter 2: Mobile Numbers
        if RICH_AVAILABLE:
            mobile_input = Prompt.ask("[cyan]📱 Enter mobile numbers (comma-separated, optional)[/cyan]", default="").strip()
        else:
            mobile_input = input(f"{Colors.CYAN}📱 Enter mobile numbers (optional): {Colors.RESET}").strip()
        
        mobile_fragments = []
        if mobile_input:
            for mobile in [m.strip() for m in mobile_input.split(',') if m.strip()]:
                mobile_fragments.extend(self._extract_mobile_fragments(mobile))
        
        # Chapter 3: Date of Birth
        if RICH_AVAILABLE:
            dob_input = Prompt.ask("[cyan]🎂 Enter date of birth DD/MM/YYYY (optional)[/cyan]", default="").strip()
        else:
            dob_input = input(f"{Colors.CYAN}🎂 Enter date of birth DD/MM/YYYY (optional): {Colors.RESET}").strip()
        
        date_fragments = self._parse_date_of_birth(dob_input) if dob_input else []
        
        # Chapter 4: Year Range
        if RICH_AVAILABLE:
            year_input = Prompt.ask("[cyan]📅 Enter year range YYYY-YYYY (optional)[/cyan]", default="").strip()
        else:
            year_input = input(f"{Colors.CYAN}📅 Enter year range YYYY-YYYY (optional): {Colors.RESET}").strip()
        
        year_ranges = self._generate_year_range(year_input) if year_input else []
        
        # Chapter 5: Special Characters
        if RICH_AVAILABLE:
            special_input = Prompt.ask("[cyan]🔣 Enter YOUR special characters (comma-separated, optional)[/cyan]", default="").strip()
        else:
            special_input = input(f"{Colors.CYAN}🔣 Enter YOUR special characters (optional): {Colors.RESET}").strip()
        
        special_chars = [char.strip() for char in special_input.split(',') if char.strip()] if special_input else []
        
        # Chapter 6: Separator Choice
        if RICH_AVAILABLE:
            use_underscore = Confirm.ask("[cyan]🔗 Allow '_' as separator?[/cyan]", default=False)
        else:
            underscore_choice = input(f"{Colors.CYAN}🔗 Allow '_' as separator? (y/N): {Colors.RESET}").strip().lower()
            use_underscore = underscore_choice in ('y', 'yes', '1')
        
        # Chapter 7: Number Patterns
        if RICH_AVAILABLE:
            pattern_input = Prompt.ask("[cyan]🔢 Enter number patterns (choose from 00,000,0000; comma-separated, optional)[/cyan]", default="").strip()
        else:
            pattern_input = input(f"{Colors.CYAN}🔢 Enter number patterns 00,000,0000 (optional): {Colors.RESET}").strip()
        
        number_patterns = []
        if pattern_input:
            for pattern in [p.strip() for p in pattern_input.split(',') if p.strip()]:
                number_patterns.extend(self._generate_number_patterns(pattern))
        
        # Chapter 8: Generation Mode
        if RICH_AVAILABLE:
            generation_mode = Prompt.ask("[cyan]💪 Generation mode[/cyan]", choices=["full", "strong"], default="full")
        else:
            mode_input = input(f"{Colors.CYAN}💪 Generation mode (full/strong) [full]: {Colors.RESET}").strip().lower()
            generation_mode = mode_input if mode_input in ['full', 'strong'] else 'full'
        
        # Interactive prompts for output limits
        min_count = None
        max_count = None
        
        if RICH_AVAILABLE:
            set_limits = Confirm.ask("[cyan]🎯 Set minimum/maximum output limits?[/cyan]", default=False)
        else:
            limits_choice = input(f"{Colors.CYAN}🎯 Set minimum/maximum output limits? (y/N): {Colors.RESET}").strip().lower()
            set_limits = limits_choice in ('y', 'yes', '1')
        
        if set_limits:
            if RICH_AVAILABLE:
                min_count = IntPrompt.ask("[cyan]Minimum output count[/cyan]", default=0)
                max_count = IntPrompt.ask("[cyan]Maximum output count (0 = unlimited)[/cyan]", default=0)
            else:
                try:
                    min_count = int(input(f"{Colors.CYAN}Minimum output count [0]: {Colors.RESET}").strip() or "0")
                    max_count = int(input(f"{Colors.CYAN}Maximum output count (0 = unlimited) [0]: {Colors.RESET}").strip() or "0")
                except ValueError:
                    min_count = max_count = 0
            
            if max_count == 0:
                max_count = None
        
        # Output filename
        if RICH_AVAILABLE:
            output_filename = Prompt.ask("[cyan]💾 Output filename[/cyan]", default="passbot_dictionary.txt")
        else:
            output_filename = input(f"{Colors.CYAN}💾 Output filename [passbot_dictionary.txt]: {Colors.RESET}").strip()
            if not output_filename:
                output_filename = "passbot_dictionary.txt"
        
        return InputProfile(
            words=words,
            mobile_numbers=mobile_fragments,
            date_fragments=date_fragments,
            year_ranges=year_ranges,
            special_chars=special_chars,
            number_patterns=number_patterns,
            output_filename=output_filename,
            generation_mode=generation_mode,
            use_underscore_separator=use_underscore,
            min_output_count=min_count,
            max_output_count=max_count
        )
    
    def _write_password(self, password: str) -> bool:
        """Write password to output with deduplication and filtering"""
        if password in self.generated_passwords:
            return False
        
        # Chapter 8: Strong mode filtering
        if self.input_profile.generation_mode == "strong":
            if not PasswordStrength.is_strong(password):
                self.stats.strong_mode_filtered += 1
                return False
        
        # Check max count limit
        if (self.input_profile.max_output_count and 
            len(self.generated_passwords) >= self.input_profile.max_output_count):
            return False
        
        self.generated_passwords.add(password)
        
        # Write to file
        if self.output_file:
            try:
                self.output_file.write(password + "\n")
            except Exception:
                pass
        
        # Optimized periodic flush - reduced frequency during normal operation
        if len(self.generated_passwords) % 2000 == 0:
            try:
                if self.output_file and not self.interrupted:
                    self.output_file.flush()
            except Exception:
                pass
        
        if len(self.generated_passwords) % self.backup_interval == 0:
            self._save_progress()
        
        return True
    
    def _update_live_stats(self, current_password: str, phase_description: str):
        """Update live statistics for UI"""
        self.stats.current_password = current_password
        self.stats.current_phase = phase_description
        self.stats.passwords_generated = len(self.generated_passwords)
        
        elapsed_time = max(1e-6, time.time() - self.stats.start_time)
        self.stats.generation_rate = self.stats.passwords_generated / elapsed_time
        
        # Update system stats
        self.stats.memory_usage_mb, self.stats.disk_space_gb = self._get_system_stats()
        
        # Calculate ETA if we have an estimate
        if self.stats.estimated_total > 0 and self.stats.generation_rate > 0:
            remaining = max(0, self.stats.estimated_total - self.stats.passwords_generated)
            self.stats.eta_seconds = remaining / self.stats.generation_rate
    
    def _estimate_total_combinations(self) -> int:
        """Estimate total number of possible combinations"""
        if not self.input_profile:
            return 0
        
        # Prepare component lists
        words = []
        for word in self.input_profile.words:
            words.extend(self._generate_word_variations(word))
        words = list(set(words))
        
        numbers = list(set(
            self.input_profile.mobile_numbers +
            self.input_profile.date_fragments +
            self.input_profile.year_ranges +
            self.input_profile.number_patterns
        ))
        
        specials = self.input_profile.special_chars
        separators = [""]
        if self.input_profile.use_underscore_separator:
            separators.append("_")
        
        # Rough estimation
        total = 0
        
        # Single elements
        total += len(words)
        total += len(numbers)
        
        # Two-element combinations
        if words and numbers:
            total += len(words) * len(numbers) * len(separators) * 2  # Both orders
        
        if words and specials:
            total += len(words) * len(specials) * len(separators) * 2
        
        if numbers and specials:
            total += len(numbers) * len(specials) * len(separators) * 2
        
        if len(words) >= 2:
            total += len(words) * (len(words) - 1) * len(separators)
        
        # Three-element combinations (simplified)
        if words and numbers and specials:
            total += len(words) * len(numbers) * len(specials) * len(separators) * len(separators) * 6
        
        return total
    
    def _generate_passwords(self, layout):
        """Main password generation logic implementing all phases with fast interrupt checks"""
        if not self.input_profile:
            return
        
        # Prepare component lists
        words = []
        for word in self.input_profile.words:
            words.extend(self._generate_word_variations(word))
        words = sorted(list(set(words)))
        
        numbers = sorted(list(set(
            self.input_profile.mobile_numbers +
            self.input_profile.date_fragments +
            self.input_profile.year_ranges +
            self.input_profile.number_patterns
        )))
        
        specials = sorted(self.input_profile.special_chars)
        
        separators = [""]
        if self.input_profile.use_underscore_separator:
            separators.append("_")
        
        # Phase 1: Single words
        if self.current_phase == 1:
            phase_desc = "Phase 1/7: Single Words"
            for i, word in enumerate(words):
                if self.interrupted:  # Fast interrupt check
                    return
                if i < self.phase_position:
                    continue
                
                self._write_password(word)
                self.phase_position = i + 1
                
                if len(self.generated_passwords) % 200 == 0:
                    self._update_live_stats(word, phase_desc)
                    if layout:
                        self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 2
            self.phase_position = 0
        
        # Phase 2: Single numbers
        if self.current_phase == 2:
            phase_desc = "Phase 2/7: Single Numbers"
            for i, number in enumerate(numbers):
                if self.interrupted:  # Fast interrupt check
                    return
                if i < self.phase_position:
                    continue
                
                self._write_password(str(number))
                self.phase_position = i + 1
                
                if len(self.generated_passwords) % 200 == 0:
                    self._update_live_stats(str(number), phase_desc)
                    if layout:
                        self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 3
            self.phase_position = 0
        
        # Phase 3: Word + Number combinations
        if self.current_phase == 3:
            phase_desc = "Phase 3/7: Word + Number"
            combination_index = 0
            
            for word in words:
                if self.interrupted:  # Fast interrupt check
                    return
                for number in numbers:
                    if self.interrupted:  # Fast interrupt check in inner loop
                        return
                    for separator in separators:
                        # Both orders: word+number and number+word
                        combinations = [f"{word}{separator}{number}", f"{number}{separator}{word}"]
                        
                        for combo in combinations:
                            if self.interrupted:  # Fast interrupt check in deepest loop
                                return
                            if combination_index < self.phase_position:
                                combination_index += 1
                                continue
                            
                            self._write_password(combo)
                            combination_index += 1
                            self.phase_position = combination_index
                            
                            if len(self.generated_passwords) % 200 == 0:
                                self._update_live_stats(combo, phase_desc)
                                if layout:
                                    self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 4
            self.phase_position = 0
        
        # Phase 4: Word + Special combinations
        if self.current_phase == 4 and specials:
            phase_desc = "Phase 4/7: Word + Special"
            combination_index = 0
            
            for word in words:
                if self.interrupted:  # Fast interrupt check
                    return
                for special in specials:
                    if self.interrupted:  # Fast interrupt check in inner loop
                        return
                    for separator in separators:
                        combinations = [f"{word}{separator}{special}", f"{special}{separator}{word}"]
                        
                        for combo in combinations:
                            if self.interrupted:  # Fast interrupt check in deepest loop
                                return
                            if combination_index < self.phase_position:
                                combination_index += 1
                                continue
                            
                            self._write_password(combo)
                            combination_index += 1
                            self.phase_position = combination_index
                            
                            if len(self.generated_passwords) % 200 == 0:
                                self._update_live_stats(combo, phase_desc)
                                if layout:
                                    self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 5
            self.phase_position = 0
        elif self.current_phase == 4:
            self.current_phase = 5
            self.phase_position = 0
        
        # Phase 5: Number + Special combinations
        if self.current_phase == 5 and specials:
            phase_desc = "Phase 5/7: Number + Special"
            combination_index = 0
            
            for number in numbers:
                if self.interrupted:  # Fast interrupt check
                    return
                for special in specials:
                    if self.interrupted:  # Fast interrupt check in inner loop
                        return
                    for separator in separators:
                        combinations = [f"{number}{separator}{special}", f"{special}{separator}{number}"]
                        
                        for combo in combinations:
                            if self.interrupted:  # Fast interrupt check in deepest loop
                                return
                            if combination_index < self.phase_position:
                                combination_index += 1
                                continue
                            
                            self._write_password(combo)
                            combination_index += 1
                            self.phase_position = combination_index
                            
                            if len(self.generated_passwords) % 200 == 0:
                                self._update_live_stats(combo, phase_desc)
                                if layout:
                                    self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 6
            self.phase_position = 0
        elif self.current_phase == 5:
            self.current_phase = 6
            self.phase_position = 0
        
        # Phase 6: Word + Word combinations
        if self.current_phase == 6 and len(words) >= 2:
            phase_desc = "Phase 6/7: Word + Word"
            combination_index = 0
            
            for i, word1 in enumerate(words):
                if self.interrupted:  # Fast interrupt check
                    return
                for j, word2 in enumerate(words):
                    if self.interrupted:  # Fast interrupt check in inner loop
                        return
                    if i == j:  # Skip same word
                        continue
                    for separator in separators:
                        combo = f"{word1}{separator}{word2}"
                        
                        if self.interrupted:  # Fast interrupt check in deepest loop
                            return
                        if combination_index < self.phase_position:
                            combination_index += 1
                            continue
                        
                        self._write_password(combo)
                        combination_index += 1
                        self.phase_position = combination_index
                        
                        if len(self.generated_passwords) % 200 == 0:
                            self._update_live_stats(combo, phase_desc)
                            if layout:
                                self.ui.update_live_display(layout, self.stats)
            
            self.current_phase = 7
            self.phase_position = 0
        elif self.current_phase == 6:
            self.current_phase = 7
            self.phase_position = 0
        
        # Phase 7: Three-element combinations
        if self.current_phase == 7:
            phase_desc = "Phase 7/7: Three Elements"
            combination_index = 0
            
            # Word + Number + Special
            if words and numbers and specials:
                for word in words:
                    if self.interrupted:  # Fast interrupt check
                        return
                    for number in numbers:
                        if self.interrupted:  # Fast interrupt check
                            return
                        for special in specials:
                            if self.interrupted:  # Fast interrupt check
                                return
                            for sep1 in separators:
                                if self.interrupted:  # Fast interrupt check
                                    return
                                for sep2 in separators:
                                    # Multiple permutations
                                    combinations = [
                                        f"{word}{sep1}{number}{sep2}{special}",
                                        f"{word}{sep1}{special}{sep2}{number}",
                                        f"{number}{sep1}{word}{sep2}{special}",
                                        f"{number}{sep1}{special}{sep2}{word}",
                                        f"{special}{sep1}{word}{sep2}{number}",
                                        f"{special}{sep1}{number}{sep2}{word}"
                                    ]
                                    
                                    for combo in combinations:
                                        if self.interrupted:  # Fast interrupt check in deepest loop
                                            return
                                        if combination_index < self.phase_position:
                                            combination_index += 1
                                            continue
                                        
                                        self._write_password(combo)
                                        combination_index += 1
                                        self.phase_position = combination_index
                                        
                                        if len(self.generated_passwords) % 200 == 0:
                                            self._update_live_stats(combo, phase_desc)
                                            if layout:
                                                self.ui.update_live_display(layout, self.stats)
            
            # Word + Word + Number
            if len(words) >= 2 and numbers:
                for i, word1 in enumerate(words):
                    if self.interrupted:  # Fast interrupt check
                        return
                    for j, word2 in enumerate(words):
                        if self.interrupted:  # Fast interrupt check
                            return
                        if i == j:
                            continue
                        for number in numbers:
                            if self.interrupted:  # Fast interrupt check
                                return
                            for sep1 in separators:
                                if self.interrupted:  # Fast interrupt check
                                    return
                                for sep2 in separators:
                                    combinations = [
                                        f"{word1}{sep1}{word2}{sep2}{number}",
                                        f"{word1}{sep1}{number}{sep2}{word2}",
                                        f"{number}{sep1}{word1}{sep2}{word2}"
                                    ]
                                    
                                    for combo in combinations:
                                        if self.interrupted:  # Fast interrupt check in deepest loop
                                            return
                                        if combination_index < self.phase_position:
                                            combination_index += 1
                                            continue
                                        
                                        self._write_password(combo)
                                        combination_index += 1
                                        self.phase_position = combination_index
                                        
                                        if len(self.generated_passwords) % 200 == 0:
                                            self._update_live_stats(combo, phase_desc)
                                            if layout:
                                                self.ui.update_live_display(layout, self.stats)
    
    def run(self) -> int:
        """Main execution method"""
        try:
            # Show banner and initialization
            self.ui.show_banner()
            self.ui.show_loading("🚀 Initializing PassBot Enterprise Suite", 2.0)
            
            # Chapter 9: Check for resume
            resumed = False
            if os.path.exists(self.progress_file):
                if RICH_AVAILABLE:
                    should_resume = Confirm.ask("[yellow]📂 Previous progress found. Resume generation?[/yellow]", default=True)
                else:
                    resume_input = input(f"{Colors.YELLOW}📂 Previous progress found. Resume generation? (Y/n): {Colors.RESET}").strip().lower()
                    should_resume = resume_input not in ('n', 'no', '0')
                
                if should_resume:
                    resumed = self._load_progress()
            
            # Collect inputs if not resumed
            if not resumed:
                self.input_profile = self._collect_user_inputs()
                print(f"\n{Colors.GREEN}✅ Input collection complete!{Colors.RESET}")
            
            # Validate minimum requirements
            if not self.input_profile or not self.input_profile.words:
                print(f"{Colors.RED}❌ At least one base word is required!{Colors.RESET}")
                return 1
            
            # Interactive confirmation for all combinations
            if not resumed:
                if RICH_AVAILABLE:
                    generate_all = Confirm.ask("[cyan]🎯 Generate ALL possible combinations?[/cyan]", default=True)
                else:
                    all_input = input(f"{Colors.CYAN}🎯 Generate ALL possible combinations? (Y/n): {Colors.RESET}").strip().lower()
                    generate_all = all_input not in ('n', 'no', '0')
                
                if not generate_all:
                    print(f"{Colors.YELLOW}⚠️ Limited generation selected. Using min/max counts if specified.{Colors.RESET}")
            
            # Open output file
            try:
                file_mode = 'a' if (resumed and os.path.exists(self.input_profile.output_filename)) else 'w'
                self.output_file = open(self.input_profile.output_filename, file_mode, encoding='utf-8')
            except Exception as e:
                print(f"{Colors.RED}❌ Cannot open output file: {e}{Colors.RESET}")
                return 1
            
            # Initialize statistics
            self.stats.start_time = time.time()
            self.stats.output_file = self.input_profile.output_filename
            self.stats.estimated_total = self._estimate_total_combinations()
            
            print(f"\n{Colors.BRIGHT}{Colors.GREEN}🚀 Starting password generation...{Colors.RESET}")
            print(f"{Colors.CYAN}📊 Estimated combinations: {self.stats.estimated_total:,}{Colors.RESET}")
            print(f"{Colors.CYAN}💪 Mode: {self.input_profile.generation_mode.upper()}{Colors.RESET}")
            print(f"{Colors.CYAN}📝 Output: {self.input_profile.output_filename}{Colors.RESET}\n")
            
            # Create live layout and start generation
            layout = self.ui.create_live_layout()
            
            try:
                if RICH_AVAILABLE and layout:
                    with Live(layout, refresh_per_second=2) as live:
                        self._generate_passwords(layout)
                else:
                    self._generate_passwords(None)
            
            except KeyboardInterrupt:
                # This should be handled by signal handler, but just in case
                pass
            
            finally:
                # Ensure file is closed and progress saved
                if self.output_file and not self.output_file.closed:
                    try:
                        self.output_file.flush()
                        os.fsync(self.output_file.fileno())
                        self.output_file.close()
                    except Exception:
                        pass
                
                if not self.interrupted:
                    self._save_progress()
            
            # Final summary
            total_generated = len(self.generated_passwords)
            elapsed_time = time.time() - self.stats.start_time
            
            print(f"\n\n{Colors.BRIGHT}{Colors.GREEN}✅ Generation Complete!{Colors.RESET}")
            print(f"{Colors.GREEN}📊 Total passwords generated: {total_generated:,}{Colors.RESET}")
            print(f"{Colors.GREEN}⏱️ Total time: {str(timedelta(seconds=int(elapsed_time)))}{Colors.RESET}")
            print(f"{Colors.GREEN}⚡ Average rate: {total_generated/max(1, elapsed_time):.1f} passwords/sec{Colors.RESET}")
            
            if self.stats.strong_mode_filtered > 0:
                print(f"{Colors.YELLOW}🛡️ Filtered (weak): {self.stats.strong_mode_filtered:,} passwords{Colors.RESET}")
            
            print(f"{Colors.GREEN}💾 Output saved to: {self.input_profile.output_filename}{Colors.RESET}")
            
            # Check if minimum count was reached
            if (self.input_profile.min_output_count and 
                total_generated < self.input_profile.min_output_count):
                print(f"{Colors.YELLOW}⚠️ Warning: Only {total_generated:,} passwords generated, minimum was {self.input_profile.min_output_count:,}{Colors.RESET}")
            
            return 0
            
        except Exception as e:
            print(f"{Colors.RED}❌ Fatal error: {e}{Colors.RESET}")
            return 1
        
        finally:
            # Cleanup
            if hasattr(self, 'output_file') and self.output_file and not self.output_file.closed:
                try:
                    self.output_file.close()
                except Exception:
                    pass

def main():
    """Main entry point"""
    print(f"{Colors.BRIGHT}{Colors.CYAN}")
    print("🕷️ PassBot Enterprise - Complete 9-Chapter Logic Implementation")
    print("   Professional Password Dictionary Generator")
    print("   Gen-Spider Security Systems")
    print(f"{Colors.RESET}\n")
    
    passbot = PassBotEnterprise()
    return passbot.run()

if __name__ == '__main__':
    sys.exit(main())
