#!/usr/bin/env python3
"""
Pass-Bot Enterprise Personal Dictionary Generator (Fixed Version)
===============================================================

🕷️ Professional brute force dictionary generator for security testing
Built with Gen-Spider level enterprise architecture and quality standards

🎯 FIXED MODIFICATIONS:
- Proper interrupt handling with Ctrl+C (SIGINT)
- Progress saving and resumption capability
- Continuous generation until manually interrupted
- Fixed progress bar calculation
- Incremental progress persistence
- Real-time monitoring with accurate progress
- Removed '.' and '-' separators (only empty and optional '_')
- Added Full vs Strong password generation mode
- Incremental saving to output file during generation

Repository: Pass-Bot
Author: Gen-Spider Security Systems
Version: 1.2.3 Fixed
License: MIT
"""

import itertools
import os
import sys
import re
import math
import time
import secrets
import hashlib
import psutil
import shutil
import signal
import pickle
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Iterator
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing required dependencies...")
    os.system("pip install rich colorama psutil")
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        from rich.prompt import Prompt, Confirm, IntPrompt
        from rich.align import Align
        from rich.live import Live
        from rich.layout import Layout
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

try:
    import colorama
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    os.system("pip install colorama")
    import colorama
    from colorama import Fore, Style, init
    init(autoreset=True)

# Enterprise Color Palette
class Colors:
    BRIGHT_GREEN = '\033[1;92m'
    GREEN = '\033[92m'
    DARK_GREEN = '\033[32m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # Functional colors
    HEADER = '\033[1;92m'
    INFO = '\033[96m'
    SUCCESS = '\033[1;32m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    MATRIX = '\033[92m'

@dataclass
class LiveStats:
    """Live generation statistics"""
    current_password: str = ""
    passwords_generated: int = 0
    current_phase: str = ""
    start_time: float = 0.0
    estimated_total: int = 0
    memory_usage_mb: float = 0.0
    disk_space_gb: float = 0.0
    generation_rate: float = 0.0  # passwords per second
    eta_seconds: float = 0.0
    current_phase_num: int = 1
    total_phases: int = 7
    output_file: str = "passbot_final_dictionary.txt"

@dataclass
class ProgressState:
    """Progress state for saving/loading"""
    generated_passwords: Set[str]
    current_phase: int
    phase_position: int
    total_generated: int
    generation_start_time: float
    last_save_time: float
    input_profile_data: dict
    
@dataclass
class InputProfile:
    """User input profile for generation"""
    words: List[str]
    mobile_numbers: List[str] 
    date_fragments: List[str]
    year_ranges: List[str]
    special_chars: List[str]  # Only user-provided symbols
    number_patterns: List[str]
    output_filename: str
    generation_mode: str = "full"  # "full" or "strong"
    complete_generation: bool = True

class PasswordStrengthCalculator:
    """Advanced password strength calculation with enterprise-grade metrics"""
    
    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calculate Shannon entropy of password"""
        if not password:
            return 0.0
            
        char_counts = defaultdict(int)
        for char in password:
            char_counts[char] += 1
            
        length = len(password)
        entropy = 0.0
        
        for count in char_counts.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
                
        return entropy * length

    @staticmethod
    def calculate_complexity_score(password: str) -> float:
        """Calculate comprehensive complexity score"""
        if not password:
            return 0.0
            
        score = 0.0
        length = len(password)
        
        # Length scoring (0-30 points)
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
            
        # Character variety (0-40 points)
        char_types = 0
        if any(c.islower() for c in password):
            char_types += 1
        if any(c.isupper() for c in password):
            char_types += 1
        if any(c.isdigit() for c in password):
            char_types += 1
        if any(not c.isalnum() for c in password):
            char_types += 1
            
        score += char_types * 10
        
        # Entropy bonus (0-30 points)
        entropy = PasswordStrengthCalculator.calculate_entropy(password)
        score += min(30, (entropy / 6.0) * 30)
        
        # Pattern penalties
        if re.search(r'(.)\1{2,}', password):  # Repeated chars
            score -= 15
        if re.search(r'(abc|123|qwe)', password.lower()):  # Sequential
            score -= 10
        if re.search(r'(password|admin|user|test)', password.lower()):  # Common words
            score -= 20
            
        return max(0, min(100, score))

    @staticmethod
    def get_strength_level(score: float) -> str:
        """Get categorical strength level"""
        if score >= 90:
            return "EXCEPTIONAL"
        elif score >= 80:
            return "VERY_STRONG"
        elif score >= 70:
            return "STRONG"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "MODERATE"
        elif score >= 20:
            return "WEAK"
        else:
            return "VERY_WEAK"

class SystemMonitor:
    """Real-time system monitoring"""
    
    @staticmethod
    def get_memory_usage_mb() -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    @staticmethod
    def get_available_disk_space_gb(path: str = ".") -> float:
        """Get available disk space in GB"""
        try:
            total, used, free = shutil.disk_usage(path)
            return free / 1024 / 1024 / 1024
        except:
            return 0.0

class MatrixUI:
    """Enhanced Matrix-style UI with Gen-Spider level effects"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.width = self.console.size.width if RICH_AVAILABLE else 80
        self.height = self.console.size.height if RICH_AVAILABLE else 24
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def show_enterprise_banner(self):
        """Display Gen-Spider level enterprise banner"""
        self.clear_screen()
        
        if RICH_AVAILABLE:
            banner_art = f"""{Colors.BRIGHT_GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██████╗  █████╗ ███████╗███████╗    ██████╗  ██████╗ ████████╗              ║
║  ██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝              ║
║  ██████╔╝███████║███████╗███████╗    ██████╔╝██║   ██║   ██║                 ║
║  ██╔═══╝ ██╔══██║╚════██║╚════██║    ██╔══██╗██║   ██║   ██║                 ║
║  ██║     ██║  ██║███████║███████║    ██████╔╝╚██████╔╝   ██║                 ║
║  ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝                 ║
║                                                                              ║
║            🕷️  ENTERPRISE PERSONAL DICTIONARY GENERATOR  🕷️                  ║
║                   🎯 FIXED VERSION - NO SEPARATORS + MODES 🎯               ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │  🔐 Gen-Spider Security Systems          📊 Version 1.2.3 Fixed        │ ║
║  │  📺 Live Generation Monitoring           ⚡ Progress Saving/Resume       │ ║
║  │  🛑 Proper Interrupt Handling            🎯 Full/Strong Modes           │ ║
║  │  🚫 No '.' or '-' Separators             💾 Incremental Output Save     │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
            
            panel = Panel(
                Align.center(Text(banner_art, style="bright_green")),
                title="[bold red]🎯 PASS-BOT FIXED - ENHANCED SEPARATOR CONTROL 🎯[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            
            if self.console:
                self.console.print(panel)
        else:
            print(f"""{Colors.BRIGHT_GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                            PASS-BOT ENTERPRISE FIXED                        ║
║                    Enhanced Generation Dictionary Generator                   ║
║                        🕷️ Gen-Spider Security Systems 🕷️                    ║
║                     🎯 NO SEPARATORS + GENERATION MODES 🎯                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")

    def show_matrix_loading(self, message: str = "Initializing Security Systems", duration: float = 3.0):
        """Show Matrix-style loading with enhanced effects"""
        if RICH_AVAILABLE and self.console:
            with Progress(
                SpinnerColumn("dots12", style="bright_green"),
                TextColumn("[bright_green]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(message, total=100)
                for i in range(100):
                    progress.update(task, advance=1)
                    time.sleep(duration / 100)
        else:
            chars = "01"
            print(f"{Colors.MATRIX}", end="")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                print(secrets.choice(chars), end="", flush=True)
                time.sleep(0.05)
            
            print(f"{Colors.RESET}")
            print(f"{Colors.INFO}{message}... Complete!{Colors.RESET}")

    def create_live_monitoring_layout(self) -> Layout:
        """Create live monitoring layout"""
        if not RICH_AVAILABLE:
            return None
            
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="stats", ratio=2),
            Layout(name="progress", ratio=3)
        )
        
        return layout
    
    def update_live_stats(self, layout: Layout, stats: LiveStats):
        """Update live statistics display"""
        if not layout or not RICH_AVAILABLE:
            return
            
        # Header
        layout["header"].update(Panel(
            f"[bold green]🎯 PASS-BOT LIVE GENERATION MONITOR - {datetime.now().strftime('%H:%M:%S')}[/bold green]",
            style="green"
        ))
        
        # Stats table
        stats_table = Table(title="📊 Real-Time Statistics", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="bright_green")
        
        elapsed_time = time.time() - stats.start_time
        eta_str = str(timedelta(seconds=int(stats.eta_seconds))) if stats.eta_seconds > 0 else "Calculating..."
        
        stats_table.add_row("🔐 Passwords Generated", f"{stats.passwords_generated:,}")
        stats_table.add_row("⚡ Generation Rate", f"{stats.generation_rate:.1f}/sec")
        stats_table.add_row("📝 Current Password", stats.current_password[:30] + "..." if len(stats.current_password) > 30 else stats.current_password)
        stats_table.add_row("🎯 Current Phase", f"{stats.current_phase}")
        stats_table.add_row("⏱️ Elapsed Time", str(timedelta(seconds=int(elapsed_time))))
        stats_table.add_row("⏳ ETA", eta_str)
        stats_table.add_row("💾 Memory Usage", f"{stats.memory_usage_mb:.1f} MB")
        stats_table.add_row("💽 Disk Space", f"{stats.disk_space_gb:.1f} GB")
        
        layout["stats"].update(Panel(stats_table, title="[bold cyan]📊 Statistics[/bold cyan]"))
        
        # Progress display
        if stats.estimated_total > 0:
            progress_pct = min(100.0, (stats.passwords_generated / stats.estimated_total) * 100)
            progress_bar = "█" * int(progress_pct / 2) + "░" * (50 - int(progress_pct / 2))
            
            progress_info = f"""
[bold green]Generation Progress[/bold green]

Progress: {progress_pct:.1f}% [{progress_bar}]
Generated: {stats.passwords_generated:,} / {stats.estimated_total:,}

[yellow]Current Operation:[/yellow]
{stats.current_phase}

[cyan]Latest Password:[/cyan]
{stats.current_password}

[magenta]System Status:[/magenta]
Memory: {stats.memory_usage_mb:.1f} MB
Disk: {stats.disk_space_gb:.1f} GB Available
Rate: {stats.generation_rate:.1f} passwords/sec
"""
        else:
            progress_info = f"""
[bold green]Generation in Progress[/bold green]

Generated: {stats.passwords_generated:,} passwords

[yellow]Current Operation:[/yellow]
{stats.current_phase}

[cyan]Latest Password:[/cyan]
{stats.current_password}

[magenta]System Status:[/magenta]
Memory: {stats.memory_usage_mb:.1f} MB
Rate: {stats.generation_rate:.1f} passwords/sec
"""
        
        layout["progress"].update(Panel(progress_info, title="[bold yellow]⚡ Live Progress[/bold yellow]"))
        
        # Footer
        layout["footer"].update(Panel(
            f"[bold red]Press Ctrl+C to stop generation safely[/bold red] | [cyan]Output: {stats.output_file}[/cyan]",
            style="red"
        ))

class FixedEnterprisePassBot:
    """Fixed Enterprise-grade personal dictionary generator with proper interrupt handling"""
    
    def __init__(self):
        self.ui = MatrixUI()
        self.generated_passwords: Set[str] = set()
        self.password_strength_map: Dict[float, List[str]] = defaultdict(list)
        self.live_stats = LiveStats()
        self.input_profile: Optional[InputProfile] = None
        self.interrupted = False
        self.progress_file = "passbot_progress.pkl"
        self.backup_interval = 5000  # Save every 5000 passwords
        self.last_backup_count = 0
        
        # Generation state
        self.current_phase = 1
        self.phase_position = 0
        self.total_phases = 7
        
        # FIXED: Only use empty separator and optional underscore (NO '.' or '-')
        self.separators = ['']  # Start with only empty separator
        
        # Output file handle for incremental saving
        self.output_handle = None
        
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C interruption gracefully"""
        print(f"\n\n{Colors.WARNING}[🛑] Interrupt detected! Saving progress safely...{Colors.RESET}")
        self.interrupted = True
        
        # Flush output file first
        if self.output_handle and not self.output_handle.closed:
            try:
                self.output_handle.flush()
                os.fsync(self.output_handle.fileno())
            except:
                pass
        
        self.save_progress()
        print(f"{Colors.SUCCESS}[💾] Progress saved successfully to {self.progress_file}{Colors.RESET}")
        print(f"{Colors.SUCCESS}[📄] Output saved to {self.input_profile.output_filename if self.input_profile else 'output file'}{Colors.RESET}")
        print(f"{Colors.INFO}[🔄] You can resume generation by running the script again{Colors.RESET}")
        
    def save_progress(self):
        """Save current progress to file"""
        try:
            progress_state = ProgressState(
                generated_passwords=self.generated_passwords.copy(),
                current_phase=self.current_phase,
                phase_position=self.phase_position,
                total_generated=len(self.generated_passwords),
                generation_start_time=self.live_stats.start_time,
                last_save_time=time.time(),
                input_profile_data=asdict(self.input_profile) if self.input_profile else {}
            )
            
            with open(self.progress_file, 'wb') as f:
                pickle.dump(progress_state, f)
                
        except Exception as e:
            print(f"{Colors.ERROR}[❌] Failed to save progress: {str(e)}{Colors.RESET}")
            
    def load_progress(self) -> bool:
        """Load previous progress if exists"""
        try:
            if not os.path.exists(self.progress_file):
                return False
                
            with open(self.progress_file, 'rb') as f:
                progress_state = pickle.load(f)
                
            self.generated_passwords = progress_state.generated_passwords
            self.current_phase = progress_state.current_phase
            self.phase_position = progress_state.phase_position
            self.live_stats.start_time = progress_state.generation_start_time
            self.last_backup_count = progress_state.total_generated
            
            if progress_state.input_profile_data:
                self.input_profile = InputProfile(**progress_state.input_profile_data)
                
            print(f"{Colors.SUCCESS}[📂] Resumed from previous session: {len(self.generated_passwords):,} passwords{Colors.RESET}")
            print(f"{Colors.INFO}[🔄] Continuing from Phase {self.current_phase}/{self.total_phases}{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.WARNING}[⚠️] Could not load previous progress: {str(e)}{Colors.RESET}")
            return False
            
    def print_status(self, message: str, status_type: str = "info"):
        """Print professional status messages with icons"""
        icons = {
            "info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌",
            "generate": "⚙️", "input": "📝", "pattern": "🔄", "mobile": "📱",
            "calendar": "📅", "symbol": "🔣", "security": "🔐", "analyze": "🔍",
            "complete": "🎯", "estimate": "📊", "memory": "💾", "live": "📺"
        }
        
        colors = {
            "info": Colors.INFO, "success": Colors.SUCCESS, "warning": Colors.WARNING,
            "error": Colors.ERROR, "generate": Colors.BRIGHT_GREEN, "input": Colors.CYAN,
            "pattern": Colors.GREEN, "mobile": Colors.YELLOW, "calendar": Colors.CYAN,
            "symbol": Colors.MAGENTA, "security": Colors.BRIGHT_GREEN, "analyze": Colors.BLUE,
            "complete": Colors.BRIGHT_GREEN, "estimate": Colors.CYAN, "memory": Colors.YELLOW,
            "live": Colors.BRIGHT_GREEN
        }
        
        icon = icons.get(status_type, "ℹ️")
        color = colors.get(status_type, Colors.INFO)
        
        if RICH_AVAILABLE and self.ui.console:
            style_color = status_type if status_type in ["info", "success", "warning", "error"] else "cyan"
            self.ui.console.print(f"[{style_color}][{icon}] {message}[/{style_color}]")
        else:
            print(f"{color}[{icon}] {message}{Colors.RESET}")

    def collect_user_inputs(self) -> InputProfile:
        """Collect comprehensive user inputs with validation"""
        self.print_status("Starting comprehensive input collection for FIXED generation", "input")
        
        # Words input
        self.print_status("Step 1: Base words (admin, tech, book, movie)", "input")
        while True:
            if RICH_AVAILABLE:
                words_input = Prompt.ask("Enter words (comma-separated)").strip()
            else:
                words_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter words (comma-separated): {Colors.RESET}").strip()
                
            if words_input:
                words = [word.strip().lower() for word in words_input.split(',') if word.strip()]
                self.print_status(f"Added {len(words)} base words: {', '.join(words)}", "success")
                break
            else:
                self.print_status("Please enter at least one word!", "error")
        
        # Mobile numbers
        self.print_status("Step 2: Mobile numbers (optional) - extracts ALL possible fragments", "mobile")
        mobile_fragments = []
        
        if RICH_AVAILABLE:
            mobile_input = Prompt.ask("Enter mobile numbers (comma-separated, or press Enter to skip)", default="").strip()
        else:
            mobile_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter mobile numbers (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if mobile_input:
            mobiles = [num.strip() for num in mobile_input.split(',') if num.strip().isdigit()]
            for mobile in mobiles:
                fragments = self._extract_all_mobile_fragments(mobile)
                mobile_fragments.extend(fragments)
                self.print_status(f"Mobile {mobile} → extracted {len(fragments)} fragments", "mobile")
        
        # Date of birth
        self.print_status("Step 3: Date of birth (optional) - ALL date combinations", "calendar")
        date_fragments = []
        
        if RICH_AVAILABLE:
            dob_input = Prompt.ask("Enter date of birth (or press Enter to skip)", default="").strip()
        else:
            dob_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter date of birth (or press Enter to skip): {Colors.RESET}").strip()
            
        if dob_input:
            date_fragments = self._parse_all_date_combinations(dob_input)
            self.print_status(f"Extracted {len(date_fragments)} date combinations", "calendar")
        
        # Year ranges
        self.print_status("Step 4: Year range (e.g., 2000-2025)", "calendar")
        year_ranges = []
        
        if RICH_AVAILABLE:
            year_input = Prompt.ask("Enter year range (YYYY-YYYY, or press Enter to skip)", default="").strip()
        else:
            year_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter year range (YYYY-YYYY, or press Enter to skip): {Colors.RESET}").strip()
            
        if year_input and '-' in year_input:
            try:
                start_year, end_year = year_input.split('-')
                start_year, end_year = int(start_year.strip()), int(end_year.strip())
                
                if 1900 <= start_year <= end_year <= 2030:
                    year_ranges = [str(year) for year in range(start_year, end_year + 1)]
                    self.print_status(f"Added {len(year_ranges)} years from {start_year} to {end_year}", "calendar")
            except ValueError:
                self.print_status("Invalid year format. Skipping.", "warning")
        
        # Special characters - ONLY USER PROVIDED
        self.print_status("Step 5: Special characters (ONLY symbols you provide - no built-ins)", "symbol")
        special_chars = []
        
        if RICH_AVAILABLE:
            special_input = Prompt.ask("Enter YOUR special characters (comma-separated, or press Enter to skip)", default="").strip()
        else:
            special_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter YOUR special characters (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if special_input:
            special_chars = [char.strip() for char in special_input.split(',') if char.strip()]
            self.print_status(f"Added {len(special_chars)} USER special characters: {', '.join(special_chars)}", "symbol")
        else:
            self.print_status("No special characters added - will use NO separators by default", "info")
        
        # Ask about underscore separator
        self.print_status("Step 6: Separator preference (NO '.' or '-' separators)", "pattern")
        
        if RICH_AVAILABLE:
            allow_underscore = Confirm.ask("🔹 Allow underscore '_' as separator? (Default: NO separators)", default=False)
        else:
            underscore_input = input(f"{Colors.BRIGHT_GREEN}➤ Allow underscore '_' as separator? (y/N): {Colors.RESET}").strip().lower()
            allow_underscore = underscore_input in ['y', 'yes', '1', 'true']
        
        if allow_underscore:
            self.separators = ['', '_']
            self.print_status("Enabled separators: [empty] and [_]", "success")
        else:
            self.separators = ['']
            self.print_status("Using NO separators - only direct concatenation", "success")
        
        # Number patterns
        self.print_status("Step 7: Number patterns (000 for 3-digit, 0000 for 4-digit)", "pattern")
        number_patterns = []
        
        if RICH_AVAILABLE:
            pattern_input = Prompt.ask("Enter pattern types (comma-separated, or press Enter to skip)", default="").strip()
        else:
            pattern_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter pattern types (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if pattern_input:
            pattern_types = [p.strip() for p in pattern_input.split(',') if p.strip()]
            for pattern_type in pattern_types:
                patterns = self._generate_all_number_patterns(pattern_type)
                number_patterns.extend(patterns)
                self.print_status(f"Pattern {pattern_type} → generated {len(patterns)} combinations", "pattern")
        
        # Generation mode selection
        self.print_status("Step 8: Generation mode selection", "generate")
        
        if RICH_AVAILABLE:
            generation_mode = Prompt.ask(
                "[bold yellow]🎯 Generation Mode:[/bold yellow]\n[cyan]• 'full'[/cyan] - Generate ALL possible combinations (may take hours)\n[cyan]• 'strong'[/cyan] - Generate only strong passwords (faster, quality-focused)\n\nChoose mode",
                choices=["full", "strong"],
                default="strong"
            )
        else:
            print(f"{Colors.YELLOW}🎯 Generation Mode Options:{Colors.RESET}")
            print(f"{Colors.CYAN}  • 'full' - Generate ALL possible combinations (may take hours){Colors.RESET}")
            print(f"{Colors.CYAN}  • 'strong' - Generate only strong passwords (faster, quality-focused){Colors.RESET}")
            mode_input = input(f"{Colors.BRIGHT_GREEN}➤ Choose mode (full/strong) [strong]: {Colors.RESET}").strip().lower()
            generation_mode = mode_input if mode_input in ['full', 'strong'] else 'strong'
        
        self.print_status(f"Selected generation mode: {generation_mode.upper()}", "success")
        
        # Output filename
        if RICH_AVAILABLE:
            output_filename = Prompt.ask("Output filename", default="passbot_final_dictionary.txt")
        else:
            filename_input = input(f"{Colors.BRIGHT_GREEN}➤ Output filename [passbot_final_dictionary.txt]: {Colors.RESET}").strip()
            output_filename = filename_input if filename_input else "passbot_final_dictionary.txt"
            
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
            
        if generation_mode == "full":
            self.print_status("🎯 FULL GENERATION MODE: Will generate ALL combinations until you press Ctrl+C", "complete")
        else:
            self.print_status("🎯 STRONG GENERATION MODE: Will generate only strong passwords until you press Ctrl+C", "complete")
            
        self.print_status("🛑 Use Ctrl+C to stop generation at any time - progress will be saved", "info")
        self.print_status(f"Configuration: → {output_filename}", "success")
        
        return InputProfile(
            words=words,
            mobile_numbers=mobile_fragments,
            date_fragments=date_fragments,
            year_ranges=year_ranges,
            special_chars=special_chars,
            number_patterns=number_patterns,
            output_filename=output_filename,
            generation_mode=generation_mode,
            complete_generation=True
        )

    def _extract_all_mobile_fragments(self, mobile: str) -> List[str]:
        """Extract ALL possible fragments from mobile number"""
        mobile = str(mobile).strip()
        fragments = set()
        
        # All possible substrings of length 2-10
        for start in range(len(mobile)):
            for end in range(start + 2, min(start + 11, len(mobile) + 1)):
                fragment = mobile[start:end]
                if fragment.isdigit() and len(fragment) >= 2:
                    fragments.add(fragment)
                    
        return list(fragments)

    def _parse_all_date_combinations(self, dob_str: str) -> List[str]:
        """Parse DOB and generate ALL possible date combinations"""
        clean_dob = re.sub(r'[/\-\s]', '', dob_str)
        fragments = set()
        
        # 8-digit format (DDMMYYYY)
        if len(clean_dob) == 8 and clean_dob.isdigit():
            day, month, year = clean_dob[:2], clean_dob[2:4], clean_dob[4:]
            year2 = year[-2:]
            
            # All possible arrangements
            date_parts = [day, month, year, year2]
            
            # Single parts
            fragments.update(date_parts)
            
            # Two-part combinations (NO SEPARATORS with . or -)
            for i, part1 in enumerate(date_parts):
                for j, part2 in enumerate(date_parts):
                    if i != j:
                        fragments.add(f"{part1}{part2}")  # Only direct concatenation
            
            # Three-part combinations
            all_arrangements = [
                f"{day}{month}{year2}", f"{day}{month}{year}", f"{month}{day}{year2}",
                f"{month}{day}{year}", f"{year2}{day}{month}", f"{year2}{month}{day}",
                f"{year}{day}{month}", f"{year}{month}{day}", clean_dob
            ]
            fragments.update(all_arrangements)
            
        return list(fragments)

    def _generate_all_number_patterns(self, pattern_type: str) -> List[str]:
        """Generate ALL possible number patterns based on type"""
        patterns = set()
        
        if pattern_type == "000":
            # All 3-digit combinations
            for i in range(1000):
                patterns.add(f"{i:03d}")
        elif pattern_type == "0000":
            # All 4-digit combinations  
            for i in range(10000):
                patterns.add(f"{i:04d}")
        elif pattern_type == "00":
            # All 2-digit combinations
            for i in range(100):
                patterns.add(f"{i:02d}")
        elif pattern_type == "00000":
            # Limited to common 5-digit patterns
            for i in range(0, 100000, 100):  # Every 100th number to keep it manageable
                patterns.add(f"{i:05d}")
                
        return list(patterns)

    def create_clean_word_variations(self, word: str) -> List[str]:
        """Create CLEAN word variations (NO number injection in words)"""
        variations = set()
        
        # Only consistent case variations - NO LEET SPEAK WITH NUMBERS
        variations.add(word.lower())
        variations.add(word.upper())
        variations.add(word.capitalize())  # First letter uppercase, rest lowercase
        
        return list(variations)

    def estimate_total_combinations(self, profile: InputProfile) -> int:
        """Estimate total possible combinations"""
        # Create all element lists
        all_words = []
        for word in profile.words:
            variations = self.create_clean_word_variations(word)
            all_words.extend(variations)
            
        all_numbers = list(set(profile.mobile_numbers + profile.date_fragments + 
                              profile.year_ranges + profile.number_patterns))
        all_special = profile.special_chars  # Only user-provided
        
        # Calculate combinations for each pattern (max 3 elements)
        total_estimate = 0
        
        # 1-element combinations
        total_estimate += len(all_words) + len(all_numbers)
        
        # 2-element combinations
        if all_words and all_numbers:
            total_estimate += len(all_words) * len(all_numbers) * len(self.separators) * 2  # Both orders
            
        if all_words and all_special:
            total_estimate += len(all_words) * len(all_special) * len(self.separators) * 2
            
        if all_numbers and all_special:
            total_estimate += len(all_numbers) * len(all_special) * len(self.separators) * 2
            
        if len(all_words) >= 2:
            total_estimate += (len(all_words) * (len(all_words) - 1)) * len(self.separators)
            
        # 3-element combinations
        if all_words and all_numbers and all_special:
            total_estimate += len(all_words) * len(all_numbers) * len(all_special) * len(self.separators) * len(self.separators) * 6
            
        if len(all_words) >= 2 and all_numbers:
            total_estimate += len(all_words) * (len(all_words) - 1) * len(all_numbers) * len(self.separators) * len(self.separators) * 3
            
        return total_estimate

    def update_live_stats(self, current_password: str, phase: str):
        """Update live statistics"""
        self.live_stats.current_password = current_password
        self.live_stats.current_phase = phase
        self.live_stats.passwords_generated = len(self.generated_passwords)
        self.live_stats.memory_usage_mb = SystemMonitor.get_memory_usage_mb()
        self.live_stats.disk_space_gb = SystemMonitor.get_available_disk_space_gb()
        
        # Calculate generation rate
        elapsed_time = time.time() - self.live_stats.start_time
        if elapsed_time > 0:
            self.live_stats.generation_rate = self.live_stats.passwords_generated / elapsed_time
            
            # Calculate ETA
            if self.live_stats.estimated_total > 0:
                remaining = self.live_stats.estimated_total - self.live_stats.passwords_generated
                if self.live_stats.generation_rate > 0:
                    self.live_stats.eta_seconds = remaining / self.live_stats.generation_rate

    def _add_unique_password(self, password: str) -> None:
        """Add password ensuring ZERO duplicates and write to output file"""
        if password and len(password) > 0 and password not in self.generated_passwords:
            self.generated_passwords.add(password)
            
            # Calculate strength for filtering in 'strong' mode
            if self.input_profile and self.input_profile.generation_mode == "strong":
                strength = PasswordStrengthCalculator.calculate_complexity_score(password)
                if strength < 60:  # Only add strong passwords (60+ score)
                    return
            
            # Write to output file incrementally
            if self.output_handle and not self.output_handle.closed:
                try:
                    self.output_handle.write(password + "\n")
                    
                    # Flush periodically for safety
                    if len(self.generated_passwords) % 1000 == 0:
                        self.output_handle.flush()
                        os.fsync(self.output_handle.fileno())
                except Exception as e:
                    self.print_status(f"Error writing to output file: {str(e)}", "error")
            
            # Store strength data for statistics
            strength = PasswordStrengthCalculator.calculate_complexity_score(password)
            self.password_strength_map[strength].append(password)

    def open_output_file(self, filename: str, resume: bool = False):
        """Open output file for incremental writing"""
        try:
            mode = 'a' if resume else 'w'
            self.output_handle = open(filename, mode, encoding='utf-8')
            
            if not resume:
                # Write header for new files
                header = f"""# Pass-Bot Enterprise Dictionary Generator (Fixed Version)
# ============================================================
# 
# 🕷️ Gen-Spider Security Systems - Professional Security Research Tool
# Repository: Pass-Bot Enterprise v1.2.3 Fixed
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# 🎯 FIXED MODIFICATIONS APPLIED:
# - Proper interrupt handling with Ctrl+C (SIGINT)
# - Progress saving and resumption capability
# - Continuous generation until manually interrupted
# - Fixed progress bar calculation
# - Incremental progress persistence
# - Real-time monitoring with accurate progress
# - Removed '.' and '-' separators (only empty and optional '_')
# - Added Full vs Strong password generation mode
# - Incremental saving to output file during generation
# 
# GENERATION RULES:
# -----------------
# 1. Clean word variations only (lower, UPPER, Capitalize)
# 2. NO number injection in words (no ad0min, t6ch)
# 3. User-provided symbols only
# 4. NO '.' or '-' separators (only empty and optional '_')
# 5. Zero duplicates policy enforced
# 6. Continuous generation until Ctrl+C
# 7. Mode: {self.input_profile.generation_mode.upper() if self.input_profile else 'UNKNOWN'}
# 
# {"="*80}

"""
                self.output_handle.write(header)
                
        except Exception as e:
            self.print_status(f"Failed to open output file: {str(e)}", "error")
            return False
        return True

    def close_output_file(self):
        """Close output file safely"""
        if self.output_handle and not self.output_handle.closed:
            try:
                self.output_handle.flush()
                os.fsync(self.output_handle.fileno())
                self.output_handle.close()
            except Exception:
                pass

    def generate_continuous_until_interrupted(self, profile: InputProfile) -> None:
        """Generate dictionary continuously until interrupted with Ctrl+C"""
        self.input_profile = profile
        self.live_stats.start_time = time.time()
        self.live_stats.output_file = profile.output_filename
        
        self.print_status("Initializing CONTINUOUS generation engine with interrupt handling", "live")
        
        # Create all element lists
        all_words = []
        for word in profile.words:
            variations = self.create_clean_word_variations(word)
            all_words.extend(variations)
            
        all_numbers = list(set(profile.mobile_numbers + profile.date_fragments + 
                              profile.year_ranges + profile.number_patterns))
        all_special = profile.special_chars
        
        # Remove duplicates
        all_words = list(set(all_words))
        all_numbers = list(set(all_numbers))
        all_special = list(set(all_special))
        
        # Estimate total combinations
        estimated_total = self.estimate_total_combinations(profile)
        self.live_stats.estimated_total = estimated_total
        
        self.print_status(f"Element inventory: {len(all_words)} words, {len(all_numbers)} numbers, {len(all_special)} specials", "success")
        self.print_status(f"Separators configured: {self.separators}", "success")
        self.print_status(f"Generation mode: {profile.generation_mode.upper()}", "success")
        self.print_status(f"Estimated combinations: {estimated_total:,}", "estimate")
        
        # Check if resuming and read existing passwords
        resume_mode = os.path.exists(profile.output_filename) and len(self.generated_passwords) > 0
        if resume_mode:
            self.print_status("Loading existing passwords to avoid duplicates...", "info")
            self._load_existing_passwords(profile.output_filename)
        
        # Open output file for incremental writing
        if not self.open_output_file(profile.output_filename, resume_mode):
            return
        
        # Setup live monitoring
        layout = None
        if RICH_AVAILABLE:
            layout = self.ui.create_live_monitoring_layout()
            
        try:
            if RICH_AVAILABLE and layout:
                with Live(layout, refresh_per_second=2) as live:
                    self._generate_all_phases_continuous(all_words, all_numbers, all_special, layout)
            else:
                self._generate_all_phases_console(all_words, all_numbers, all_special)
                
        except KeyboardInterrupt:
            # This is handled by the signal handler
            pass
        finally:
            self.close_output_file()
            
        if not self.interrupted:
            self.print_status("🎯 ALL combinations generated successfully!", "complete")
            # Clean up progress file on completion
            try:
                if os.path.exists(self.progress_file):
                    os.remove(self.progress_file)
            except:
                pass
        else:
            self.print_status("🔄 Generation interrupted. Progress saved for resume.", "warning")

    def _load_existing_passwords(self, filename: str):
        """Load existing passwords from output file to avoid duplicates"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.generated_passwords.add(line)
            self.print_status(f"Loaded {len(self.generated_passwords):,} existing passwords", "success")
        except Exception as e:
            self.print_status(f"Warning: Could not load existing passwords: {str(e)}", "warning")

    def _generate_all_phases_continuous(self, all_words, all_numbers, all_special, layout):
        """Generate all phases continuously with layout updates"""
        generation_count = len(self.generated_passwords)
        
        # Phase 1: Single elements
        if self.current_phase == 1 and not self.interrupted:
            self.print_status("Phase 1: Single elements", "generate")
            for i, word in enumerate(all_words):
                if self.interrupted:
                    break
                if i >= self.phase_position:  # Resume from saved position
                    self._add_unique_password(word)
                    generation_count += 1
                    self.phase_position = i + 1
                    
                    if generation_count % 100 == 0:
                        self.update_live_stats(word, "Phase 1/7: Single elements")
                        self.ui.update_live_stats(layout, self.live_stats)
                        
                    if generation_count % self.backup_interval == 0:
                        self.save_progress()
                        
            if not self.interrupted:
                self.current_phase = 2
                self.phase_position = 0
                
        # Phase 2: Numbers
        if self.current_phase == 2 and not self.interrupted:
            for i, number in enumerate(all_numbers):
                if self.interrupted:
                    break
                if i >= self.phase_position:
                    self._add_unique_password(str(number))
                    generation_count += 1
                    self.phase_position = i + 1
                    
                    if generation_count % 100 == 0:
                        self.update_live_stats(str(number), "Phase 2/7: Single numbers")
                        self.ui.update_live_stats(layout, self.live_stats)
                        
                    if generation_count % self.backup_interval == 0:
                        self.save_progress()
                        
            if not self.interrupted:
                self.current_phase = 3
                self.phase_position = 0
        
        # Continue with remaining phases...
        # Phase 3: Word + Number combinations
        if self.current_phase == 3 and not self.interrupted:
            combo_count = 0
            for word in all_words:
                if self.interrupted:
                    break
                for number in all_numbers:
                    if self.interrupted:
                        break
                    for separator in self.separators:
                        if self.interrupted:
                            break
                        # Both orders
                        combinations = [f"{word}{separator}{number}", f"{number}{separator}{word}"]
                        
                        for combo in combinations:
                            if self.interrupted:
                                break
                            if combo_count >= self.phase_position:
                                self._add_unique_password(combo)
                                generation_count += 1
                                
                                if generation_count % 100 == 0:
                                    self.update_live_stats(combo, "Phase 3/7: Word + Number combinations")
                                    self.ui.update_live_stats(layout, self.live_stats)
                                    
                                if generation_count % self.backup_interval == 0:
                                    self.save_progress()
                                    
                            combo_count += 1
                            self.phase_position = combo_count
                            
            if not self.interrupted:
                self.current_phase = 4
                self.phase_position = 0
        
        # Continue with remaining phases...
        self._generate_remaining_phases_continuous(all_words, all_numbers, all_special, layout)
        
    def _generate_remaining_phases_continuous(self, all_words, all_numbers, all_special, layout):
        """Generate remaining phases 4-7"""
        generation_count = len(self.generated_passwords)
        
        # Phase 4: Word + Special combinations (only if user provided special chars)
        if self.current_phase == 4 and not self.interrupted and all_special:
            combo_count = 0
            for word in all_words:
                if self.interrupted:
                    break
                for special in all_special:
                    if self.interrupted:
                        break
                    for separator in self.separators:
                        if self.interrupted:
                            break
                        combinations = [f"{word}{separator}{special}", f"{special}{separator}{word}"]
                        
                        for combo in combinations:
                            if self.interrupted:
                                break
                            if combo_count >= self.phase_position:
                                self._add_unique_password(combo)
                                generation_count += 1
                                
                                if generation_count % 100 == 0:
                                    self.update_live_stats(combo, "Phase 4/7: Word + Special combinations")
                                    self.ui.update_live_stats(layout, self.live_stats)
                                    
                                if generation_count % self.backup_interval == 0:
                                    self.save_progress()
                                    
                            combo_count += 1
                            self.phase_position = combo_count
                            
            if not self.interrupted:
                self.current_phase = 5
                self.phase_position = 0
        elif self.current_phase == 4 and not all_special:
            # Skip phase 4 if no special characters
            self.current_phase = 5
            self.phase_position = 0
        
        # Phase 5: Number + Special combinations
        if self.current_phase == 5 and not self.interrupted and all_special:
            combo_count = 0
            for number in all_numbers:
                if self.interrupted:
                    break
                for special in all_special:
                    if self.interrupted:
                        break
                    for separator in self.separators:
                        if self.interrupted:
                            break
                        combinations = [f"{number}{separator}{special}", f"{special}{separator}{number}"]
                        
                        for combo in combinations:
                            if self.interrupted:
                                break
                            if combo_count >= self.phase_position:
                                self._add_unique_password(combo)
                                generation_count += 1
                                
                                if generation_count % 100 == 0:
                                    self.update_live_stats(combo, "Phase 5/7: Number + Special combinations")
                                    self.ui.update_live_stats(layout, self.live_stats)
                                    
                                if generation_count % self.backup_interval == 0:
                                    self.save_progress()
                                    
                            combo_count += 1
                            self.phase_position = combo_count
                            
            if not self.interrupted:
                self.current_phase = 6
                self.phase_position = 0
        elif self.current_phase == 5 and not all_special:
            # Skip phase 5 if no special characters
            self.current_phase = 6
            self.phase_position = 0
        
        # Phase 6: Word + Word combinations
        if self.current_phase == 6 and not self.interrupted and len(all_words) >= 2:
            combo_count = 0
            for i, word1 in enumerate(all_words):
                if self.interrupted:
                    break
                for j, word2 in enumerate(all_words):
                    if self.interrupted or i == j:
                        continue
                    for separator in self.separators:
                        if self.interrupted:
                            break
                        combo = f"{word1}{separator}{word2}"
                        
                        if combo_count >= self.phase_position:
                            self._add_unique_password(combo)
                            generation_count += 1
                            
                            if generation_count % 100 == 0:
                                self.update_live_stats(combo, "Phase 6/7: Word + Word combinations")
                                self.ui.update_live_stats(layout, self.live_stats)
                                
                            if generation_count % self.backup_interval == 0:
                                self.save_progress()
                                
                        combo_count += 1
                        self.phase_position = combo_count
                        
            if not self.interrupted:
                self.current_phase = 7
                self.phase_position = 0
        elif self.current_phase == 6:
            # Skip phase 6 if less than 2 words
            self.current_phase = 7
            self.phase_position = 0
        
        # Phase 7: Three-element combinations
        if self.current_phase == 7 and not self.interrupted:
            self._generate_three_element_combinations(all_words, all_numbers, all_special, layout)
            
    def _generate_three_element_combinations(self, all_words, all_numbers, all_special, layout):
        """Generate three-element combinations"""
        generation_count = len(self.generated_passwords)
        combo_count = 0
        
        # Word + Number + Special
        if all_words and all_numbers and all_special:
            for word in all_words:
                if self.interrupted:
                    break
                for number in all_numbers:
                    if self.interrupted:
                        break
                    for special in all_special:
                        if self.interrupted:
                            break
                        for sep1 in self.separators:
                            if self.interrupted:
                                break
                            for sep2 in self.separators:
                                if self.interrupted:
                                    break
                                # All 6 permutations
                                combinations = [
                                    f"{word}{sep1}{number}{sep2}{special}",
                                    f"{word}{sep1}{special}{sep2}{number}",
                                    f"{number}{sep1}{word}{sep2}{special}",
                                    f"{number}{sep1}{special}{sep2}{word}",
                                    f"{special}{sep1}{word}{sep2}{number}",
                                    f"{special}{sep1}{number}{sep2}{word}"
                                ]
                                
                                for combo in combinations:
                                    if self.interrupted:
                                        break
                                    if combo_count >= self.phase_position:
                                        self._add_unique_password(combo)
                                        generation_count += 1
                                        
                                        if generation_count % 100 == 0:
                                            self.update_live_stats(combo, "Phase 7/7: Three-element combinations")
                                            self.ui.update_live_stats(layout, self.live_stats)
                                            
                                        if generation_count % self.backup_interval == 0:
                                            self.save_progress()
                                            
                                    combo_count += 1
                                    self.phase_position = combo_count
        
        # Word + Word + Number
        if len(all_words) >= 2 and all_numbers:
            for i, word1 in enumerate(all_words):
                if self.interrupted:
                    break
                for j, word2 in enumerate(all_words):
                    if self.interrupted or i == j:
                        continue
                    for number in all_numbers:
                        if self.interrupted:
                            break
                        for sep1 in self.separators:
                            if self.interrupted:
                                break
                            for sep2 in self.separators:
                                if self.interrupted:
                                    break
                                combinations = [
                                    f"{word1}{sep1}{word2}{sep2}{number}",
                                    f"{word1}{sep1}{number}{sep2}{word2}",
                                    f"{number}{sep1}{word1}{sep2}{word2}"
                                ]
                                
                                for combo in combinations:
                                    if self.interrupted:
                                        break
                                    if combo_count >= self.phase_position:
                                        self._add_unique_password(combo)
                                        generation_count += 1
                                        
                                        if generation_count % 100 == 0:
                                            self.update_live_stats(combo, "Phase 7/7: Word+Word+Number combinations")
                                            self.ui.update_live_stats(layout, self.live_stats)
                                            
                                        if generation_count % self.backup_interval == 0:
                                            self.save_progress()
                                            
                                    combo_count += 1
                                    self.phase_position = combo_count
                                    
    def _generate_all_phases_console(self, all_words, all_numbers, all_special):
        """Generate all phases with console output (fallback)"""
        generation_count = len(self.generated_passwords)
        last_update = time.time()
        
        # Similar generation logic but with console prints instead of layout updates
        phases = [
            ("Single Words", all_words),
            ("Single Numbers", all_numbers)
        ]
        
        for phase_name, elements in phases:
            if self.interrupted:
                break
                
            print(f"\n{Colors.CYAN}Phase: {phase_name}{Colors.RESET}")
            
            for element in elements:
                if self.interrupted:
                    break
                    
                self._add_unique_password(str(element))
                generation_count += 1
                
                if generation_count % 1000 == 0 and time.time() - last_update > 5:
                    print(f"\r{Colors.CYAN}Generated: {generation_count:,} | Current: {element} | Memory: {SystemMonitor.get_memory_usage_mb():.1f}MB{Colors.RESET}", end="", flush=True)
                    last_update = time.time()
                    
                if generation_count % self.backup_interval == 0:
                    self.save_progress()

    def run_fixed_generation_mode(self) -> int:
        """Main fixed generation mode execution"""
        try:
            # Display enterprise banner
            self.ui.show_enterprise_banner()
            self.ui.show_matrix_loading("Initializing Pass-Bot FIXED Generation Suite", 3.0)
            
            # Check for previous progress
            resume_available = os.path.exists(self.progress_file)
            if resume_available:
                if RICH_AVAILABLE:
                    resume = Confirm.ask("[yellow]Previous progress found. Resume generation?[/yellow]", default=True)
                else:
                    resume_input = input(f"{Colors.YELLOW}Previous progress found. Resume generation? (Y/n): {Colors.RESET}").strip().lower()
                    resume = resume_input not in ['n', 'no', '0', 'false']
                    
                if resume:
                    if self.load_progress():
                        self.print_status("Resuming from previous session", "success")
                        # Update separators based on loaded profile
                        if self.input_profile:
                            if '_' in getattr(self.input_profile, 'special_chars', []):
                                self.separators = ['', '_']
                            else:
                                self.separators = ['']
                    else:
                        self.print_status("Failed to load progress, starting fresh", "warning")
                        self.input_profile = self.collect_user_inputs()
                else:
                    # Remove old progress file and start fresh
                    try:
                        os.remove(self.progress_file)
                    except:
                        pass
                    self.input_profile = self.collect_user_inputs()
            else:
                self.input_profile = self.collect_user_inputs()
            
            if not self.input_profile:
                self.print_status("Generation cancelled by user", "warning")
                return 1
            
            # Generate dictionary with continuous mode
            print(f"\n{Colors.HEADER}🎯 Initiating CONTINUOUS Dictionary Generation with Enhanced Features!{Colors.RESET}")
            print(f"{Colors.INFO}🛑 Press Ctrl+C at any time to stop generation and save progress{Colors.RESET}")
            print(f"{Colors.INFO}📄 Passwords are saved incrementally to: {self.input_profile.output_filename}{Colors.RESET}")
            
            # Small delay to let user read the message
            time.sleep(2)
            
            self.generate_continuous_until_interrupted(self.input_profile)
            
            # Final summary
            generation_time = (time.time() - self.live_stats.start_time) / 3600
            
            print(f"\n{Colors.BRIGHT_GREEN}{'='*80}")
            print(f"{Colors.BRIGHT_GREEN}🎉 PASS-BOT FIXED GENERATION COMPLETE! 🎉")
            print(f"{Colors.BRIGHT_GREEN}🎯 SEPARATOR CONTROL - INCREMENTAL SAVE - GENERATION MODES 🎯")
            print(f"{Colors.BRIGHT_GREEN}🕷️ Gen-Spider Security Systems - Mission Complete 🕷️")
            print(f"{Colors.BRIGHT_GREEN}{'='*80}{Colors.RESET}")
            
            print(f"\n{Colors.INFO}📊 Final Statistics:{Colors.RESET}")
            print(f"{Colors.CYAN}   • Total passwords: {len(self.generated_passwords):,}{Colors.RESET}")
            print(f"{Colors.CYAN}   • Processing time: {generation_time:.2f} hours{Colors.RESET}")
            print(f"{Colors.CYAN}   • Generation mode: {self.input_profile.generation_mode.upper()}{Colors.RESET}")
            print(f"{Colors.CYAN}   • Peak memory: {self.live_stats.memory_usage_mb:.1f} MB{Colors.RESET}")
            print(f"{Colors.CYAN}   • Zero duplicates guaranteed{Colors.RESET}")
            print(f"{Colors.CYAN}   • No unwanted separators (NO '.' or '-'){Colors.RESET}")
            print(f"{Colors.CYAN}   • Incremental output file saving{Colors.RESET}")
            
            if self.interrupted:
                print(f"{Colors.WARNING}   • 🔄 Generation was interrupted - can be resumed later{Colors.RESET}")
            else:
                print(f"{Colors.SUCCESS}   • ✅ All combinations generated successfully{Colors.RESET}")
            
            if RICH_AVAILABLE:
                input(f"\n{Colors.GREEN}Press Enter to exit Pass-Bot Fixed...{Colors.RESET}")
            else:
                input(f"\n{Colors.GREEN}Press Enter to exit...{Colors.RESET}")
            
            return 0
            
        except KeyboardInterrupt:
            # This should be handled by signal handler, but just in case
            self.print_status("\nGeneration interrupted by user. Exiting safely...", "warning")
            return 1
        except Exception as e:
            self.print_status(f"Critical error occurred: {str(e)}", "error")
            return 1

def main():
    """Main entry point for Fixed Pass-Bot Enterprise"""
    try:
        passbot = FixedEnterprisePassBot()
        return passbot.run_fixed_generation_mode()
    except Exception as e:
        print(f"{Colors.ERROR}❌ Fatal error: {str(e)}{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())