#!/usr/bin/env python3
"""
Pass-Bot Enterprise Personal Dictionary Generator
==============================================

🕷️ Professional brute force dictionary generator for security testing
Built with Gen-Spider level enterprise architecture and quality standards

Repository: Pass-Bot
Author: Gen-Spider Security Systems
Version: 1.0.0
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
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

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
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing required dependencies...")
    os.system("pip install rich colorama")
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
class GenerationStats:
    """Generation statistics tracking"""
    total_generated: int = 0
    duplicates_removed: int = 0
    total_combinations: int = 0
    generation_time: float = 0.0
    strongest_password: str = ""
    weakest_password: str = ""
    average_strength: float = 0.0
    memory_usage: float = 0.0

@dataclass
class InputProfile:
    """User input profile for generation"""
    words: List[str]
    mobile_numbers: List[str] 
    date_fragments: List[str]
    year_ranges: List[str]
    special_chars: List[str]
    number_patterns: List[str]
    min_passwords: int
    max_passwords: int
    output_filename: str

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
║                     Professional Security Research Tool                      ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │  🔐 Gen-Spider Security Systems          📊 Version 1.0.0 Enterprise  │ ║
║  │  🛡️ Advanced Pattern Recognition         ⚡ High-Performance Core      │ ║
║  │  🧠 Intelligent Combination Engine       🎯 Professional Grade Tool    │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
            
            panel = Panel(
                Align.center(Text(banner_art, style="bright_green")),
                title="[bold red]🔐 PASS-BOT ENTERPRISE SECURITY SUITE 🔐[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            
            if self.console:
                self.console.print(panel)
        else:
            print(f"""{Colors.BRIGHT_GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                            PASS-BOT ENTERPRISE                               ║
║                    Professional Dictionary Generator                         ║
║                        🕷️ Gen-Spider Security Systems 🕷️                    ║
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

    def show_generation_progress(self, current: int, total: int, current_item: str = ""):
        """Show generation progress with professional styling"""
        if RICH_AVAILABLE and self.console:
            progress_text = f"[bright_green]Generating: {current_item}[/bright_green]"
            self.console.print(f"Progress: {current}/{total} - {progress_text}")
        else:
            percent = (current / total) * 100 if total > 0 else 0
            bar_length = 50
            filled_length = int(bar_length * current / total) if total > 0 else 0
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"\r{Colors.CYAN}[{bar}] {percent:.1f}% - {current_item}{Colors.RESET}", end="", flush=True)

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

class EnterprisePassBot:
    """Enterprise-grade personal dictionary generator with advanced features"""
    
    def __init__(self):
        self.ui = MatrixUI()
        self.generated_passwords: Set[str] = set()
        self.password_strength_map: Dict[float, List[str]] = defaultdict(list)
        self.generation_stats = GenerationStats()
        self.input_profile: Optional[InputProfile] = None
        
        # Common patterns for enhanced generation
        self.common_separators = ['', '@', '$', '!', '#', '%', '&', '*', '_', '-']
        self.leet_substitutions = {
            'a': ['@', '4'], 'e': ['3'], 'i': ['1', '!'], 'o': ['0'],
            's': ['$', '5'], 't': ['7', '+'], 'l': ['1', '|']
        }
        
    def print_status(self, message: str, status_type: str = "info"):
        """Print professional status messages with icons"""
        icons = {
            "info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌",
            "generate": "⚙️", "input": "📝", "pattern": "🔄", "mobile": "📱",
            "calendar": "📅", "symbol": "🔣", "security": "🔐", "analyze": "🔍"
        }
        
        colors = {
            "info": Colors.INFO, "success": Colors.SUCCESS, "warning": Colors.WARNING,
            "error": Colors.ERROR, "generate": Colors.BRIGHT_GREEN, "input": Colors.CYAN,
            "pattern": Colors.GREEN, "mobile": Colors.YELLOW, "calendar": Colors.CYAN,
            "symbol": Colors.MAGENTA, "security": Colors.BRIGHT_GREEN, "analyze": Colors.BLUE
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
        self.print_status("Starting comprehensive input collection", "input")
        
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
        self.print_status("Step 2: Mobile numbers (optional) - extracts 2,4,6,8,10 digit fragments", "mobile")
        mobile_fragments = []
        
        if RICH_AVAILABLE:
            mobile_input = Prompt.ask("Enter mobile numbers (comma-separated, or press Enter to skip)", default="").strip()
        else:
            mobile_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter mobile numbers (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if mobile_input:
            mobiles = [num.strip() for num in mobile_input.split(',') if num.strip().isdigit()]
            for mobile in mobiles:
                fragments = self._extract_mobile_fragments(mobile)
                mobile_fragments.extend(fragments)
                self.print_status(f"Mobile {mobile} → extracted {len(fragments)} fragments", "mobile")
        
        # Date of birth
        self.print_status("Step 3: Date of birth (optional) - DD/MM/YYYY, DD-MM-YYYY, DDMMYYYY", "calendar")
        date_fragments = []
        
        if RICH_AVAILABLE:
            dob_input = Prompt.ask("Enter date of birth (or press Enter to skip)", default="").strip()
        else:
            dob_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter date of birth (or press Enter to skip): {Colors.RESET}").strip()
            
        if dob_input:
            date_fragments = self._parse_date_of_birth(dob_input)
            self.print_status(f"Extracted {len(date_fragments)} date fragments", "calendar")
        
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
        
        # Special characters
        self.print_status("Step 5: Special characters ($, @, %, !, #)", "symbol")
        special_chars = []
        
        if RICH_AVAILABLE:
            special_input = Prompt.ask("Enter special characters (comma-separated, or press Enter to skip)", default="").strip()
        else:
            special_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter special characters (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if special_input:
            special_chars = [char.strip() for char in special_input.split(',') if char.strip()]
            self.print_status(f"Added {len(special_chars)} special characters: {', '.join(special_chars)}", "symbol")
        
        # Number patterns
        self.print_status("Step 6: Number patterns (000 for 3-digit, 0000 for 4-digit)", "pattern")
        number_patterns = []
        
        if RICH_AVAILABLE:
            pattern_input = Prompt.ask("Enter pattern types (comma-separated, or press Enter to skip)", default="").strip()
        else:
            pattern_input = input(f"{Colors.BRIGHT_GREEN}➤ Enter pattern types (comma-separated, or press Enter to skip): {Colors.RESET}").strip()
            
        if pattern_input:
            pattern_types = [p.strip() for p in pattern_input.split(',') if p.strip()]
            for pattern_type in pattern_types:
                patterns = self._generate_number_patterns(pattern_type)
                number_patterns.extend(patterns)
                self.print_status(f"Pattern {pattern_type} → generated {len(patterns)} combinations", "pattern")
        
        # Output settings
        self.print_status("Step 7: Output configuration", "generate")
        
        if RICH_AVAILABLE:
            min_passwords = IntPrompt.ask("Minimum password count", default=1000, show_default=True)
            max_passwords = IntPrompt.ask("Maximum password count", default=1000000, show_default=True)
            output_filename = Prompt.ask("Output filename", default="passbot_dictionary.txt")
        else:
            try:
                min_input = input(f"{Colors.BRIGHT_GREEN}➤ Minimum password count [1000]: {Colors.RESET}").strip()
                min_passwords = int(min_input) if min_input else 1000
            except ValueError:
                min_passwords = 1000
                
            try:
                max_input = input(f"{Colors.BRIGHT_GREEN}➤ Maximum password count [1000000]: {Colors.RESET}").strip()
                max_passwords = int(max_input) if max_input else 1000000
            except ValueError:
                max_passwords = 1000000
                
            filename_input = input(f"{Colors.BRIGHT_GREEN}➤ Output filename [passbot_dictionary.txt]: {Colors.RESET}").strip()
            output_filename = filename_input if filename_input else "passbot_dictionary.txt"
        
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
            
        self.print_status(f"Configuration: {min_passwords:,}-{max_passwords:,} passwords → {output_filename}", "success")
        
        return InputProfile(
            words=words,
            mobile_numbers=mobile_fragments,
            date_fragments=date_fragments,
            year_ranges=year_ranges,
            special_chars=special_chars,
            number_patterns=number_patterns,
            min_passwords=min_passwords,
            max_passwords=max_passwords,
            output_filename=output_filename
        )

    def _extract_mobile_fragments(self, mobile: str) -> List[str]:
        """Extract intelligent fragments from mobile number"""
        mobile = str(mobile).strip()
        fragments = []
        
        # Extract first N digits
        for length in [2, 4, 6, 8, 10]:
            if len(mobile) >= length:
                fragments.append(mobile[:length])
        
        # Extract last N digits  
        for length in [4, 6]:
            if len(mobile) >= length:
                fragments.append(mobile[-length:])
        
        # Extract middle segments
        if len(mobile) >= 8:
            fragments.append(mobile[2:6])  # Middle 4 digits
        if len(mobile) >= 10:
            fragments.append(mobile[3:7])  # Middle 4 digits offset
            
        return list(set(fragments))

    def _parse_date_of_birth(self, dob_str: str) -> List[str]:
        """Parse DOB with multiple format support"""
        clean_dob = re.sub(r'[/\-\s]', '', dob_str)
        fragments = []
        
        # 8-digit format (DDMMYYYY)
        if len(clean_dob) == 8 and clean_dob.isdigit():
            day, month, year = clean_dob[:2], clean_dob[2:4], clean_dob[4:]
            
            fragments.extend([
                day, month, year, clean_dob,
                year[-2:], day + month, month + year[-2:],
                day + year[-2:], month + day
            ])
        
        # Extract any 4-digit year
        year_match = re.search(r'(19|20)\d{2}', dob_str)
        if year_match:
            year = year_match.group()
            fragments.extend([year, year[-2:]])
            
        return list(set(fragments))

    def _generate_number_patterns(self, pattern_type: str) -> List[str]:
        """Generate common number patterns"""
        patterns = {
            "000": [
                '123', '321', '231', '132', '213', '312',
                '456', '654', '564', '465', '645', '546',
                '789', '987', '879', '798', '897', '978',
                '000', '111', '222', '333', '444', '555',
                '666', '777', '888', '999', '101', '010',
                '121', '212', '131', '313', '141', '414'
            ],
            "0000": [
                '1234', '4321', '2341', '1342', '3124', '2143',
                '1111', '2222', '3333', '4444', '5555', '6666',
                '7777', '8888', '9999', '0000', '1010', '2020',
                '1212', '2121', '1357', '2468', '9876', '5678',
                '8765', '7654', '6543', '5432', '1001', '0101'
            ]
        }
        
        return patterns.get(pattern_type, [])

    def create_word_variations(self, word: str) -> List[str]:
        """Create comprehensive word variations"""
        variations = set()
        
        # Basic case variations
        variations.add(word.lower())
        variations.add(word.upper())
        variations.add(word.capitalize())
        variations.add(word.title())
        
        # Advanced variations
        if len(word) > 1:
            # First letter variations
            variations.add(word[0].lower() + word[1:].upper())
            variations.add(word[0].upper() + word[1:].lower())
            
            # Alternating case patterns
            if len(word) > 2:
                alt1 = ''.join(ch.upper() if i % 2 == 0 else ch.lower() for i, ch in enumerate(word))
                alt2 = ''.join(ch.lower() if i % 2 == 0 else ch.upper() for i, ch in enumerate(word))
                variations.add(alt1)
                variations.add(alt2)
        
        # Leet speak variations
        if len(word) >= 3:
            leet_word = word.lower()
            for char, replacements in self.leet_substitutions.items():
                if char in leet_word:
                    for replacement in replacements:
                        leet_variation = leet_word.replace(char, replacement, 1)
                        variations.add(leet_variation)
                        variations.add(leet_variation.capitalize())
        
        return list(variations)

    def generate_comprehensive_dictionary(self, profile: InputProfile) -> None:
        """Generate comprehensive password dictionary with enterprise-grade algorithms"""
        start_time = time.time()
        self.input_profile = profile
        
        self.print_status("Initializing enterprise dictionary generation engine", "generate")
        self.ui.show_matrix_loading("Preparing advanced algorithms", 2.0)
        
        # Create word variations
        all_words = []
        for word in profile.words:
            variations = self.create_word_variations(word)
            all_words.extend(variations)
            
        self.print_status(f"Generated {len(all_words)} word variations from {len(profile.words)} base words", "success")
        
        # Collect all numerical elements
        all_numbers = (profile.mobile_numbers + profile.date_fragments + 
                      profile.year_ranges + profile.number_patterns)
        all_numbers = list(set(all_numbers))  # Remove duplicates
        
        self.print_status(f"Collected {len(all_numbers)} numerical elements", "success")
        
        # Generation phases
        total_phases = 6
        current_phase = 0
        
        # Phase 1: Basic elements
        current_phase += 1
        self.print_status(f"Phase {current_phase}/{total_phases}: Basic elements", "generate")
        
        for word in all_words[:100]:  # Limit to prevent memory issues
            self._add_password_with_strength(word)
            
        for number in all_numbers[:100]:
            self._add_password_with_strength(str(number))
        
        # Phase 2: Word + Number combinations
        current_phase += 1
        self.print_status(f"Phase {current_phase}/{total_phases}: Word-Number combinations", "generate")
        
        combination_count = 0
        for word in all_words[:50]:
            for number in all_numbers[:50]:
                if combination_count >= 10000:  # Limit combinations
                    break
                    
                # Multiple arrangements
                combinations = [
                    f"{word}{number}",
                    f"{number}{word}",
                    f"{word}_{number}",
                    f"{number}_{word}"
                ]
                
                for combo in combinations:
                    self._add_password_with_strength(combo)
                    combination_count += 1
            
            if combination_count >= 10000:
                break
        
        # Phase 3: Symbol integration
        if profile.special_chars:
            current_phase += 1
            self.print_status(f"Phase {current_phase}/{total_phases}: Symbol integration", "generate")
            
            symbol_count = 0
            for word in all_words[:30]:
                for symbol in profile.special_chars:
                    for number in all_numbers[:30]:
                        if symbol_count >= 15000:
                            break
                            
                        # Advanced symbol arrangements
                        symbol_combinations = [
                            f"{word}{symbol}{number}",
                            f"{word}{number}{symbol}",
                            f"{number}{symbol}{word}",
                            f"{symbol}{word}{number}",
                            f"{number}{word}{symbol}",
                            f"{word}{symbol}{symbol}{number}"
                        ]
                        
                        for combo in symbol_combinations:
                            self._add_password_with_strength(combo)
                            symbol_count += 1
                    
                    if symbol_count >= 15000:
                        break
                        
                if symbol_count >= 15000:
                    break
        
        # Phase 4: Multi-word combinations
        current_phase += 1
        self.print_status(f"Phase {current_phase}/{total_phases}: Multi-word combinations", "generate")
        
        if len(all_words) >= 2:
            multi_word_count = 0
            for word1 in all_words[:20]:
                for word2 in all_words[:20]:
                    if word1 != word2 and multi_word_count < 5000:
                        multi_combinations = [
                            f"{word1}{word2}",
                            f"{word1}_{word2}",
                            f"{word1}.{word2}"
                        ]
                        
                        for combo in multi_combinations:
                            self._add_password_with_strength(combo)
                            multi_word_count += 1
                            
                        # With numbers
                        for number in all_numbers[:10]:
                            if multi_word_count < 5000:
                                self._add_password_with_strength(f"{word1}{word2}{number}")
                                multi_word_count += 1
        
        # Phase 5: Advanced patterns
        current_phase += 1
        self.print_status(f"Phase {current_phase}/{total_phases}: Advanced patterns", "generate")
        
        pattern_count = 0
        for word in all_words[:20]:
            for separator in ['', '.', '_', '-']:
                for number in all_numbers[:20]:
                    if pattern_count >= 3000:
                        break
                        
                    if separator:
                        pattern = f"{word}{separator}{number}"
                        self._add_password_with_strength(pattern)
                        pattern_count += 1
                        
                        # Reverse pattern
                        reverse_pattern = f"{number}{separator}{word}"
                        self._add_password_with_strength(reverse_pattern)
                        pattern_count += 1
                
                if pattern_count >= 3000:
                    break
                    
            if pattern_count >= 3000:
                break
        
        # Phase 6: Finalization
        current_phase += 1
        self.print_status(f"Phase {current_phase}/{total_phases}: Finalization and optimization", "generate")
        
        # Calculate generation statistics
        self.generation_stats.generation_time = time.time() - start_time
        self.generation_stats.total_generated = len(self.generated_passwords)
        self.generation_stats.total_combinations = sum(len(passwords) for passwords in self.password_strength_map.values())
        
        if self.password_strength_map:
            # Find strongest and weakest
            sorted_strengths = sorted(self.password_strength_map.keys(), reverse=True)
            if sorted_strengths:
                self.generation_stats.strongest_password = self.password_strength_map[sorted_strengths[0]][0]
                self.generation_stats.weakest_password = self.password_strength_map[sorted_strengths[-1]][-1]
                self.generation_stats.average_strength = sum(sorted_strengths) / len(sorted_strengths)
        
        self.print_status(f"Generation complete: {self.generation_stats.total_generated:,} unique passwords in {self.generation_stats.generation_time:.2f}s", "success")

    def _add_password_with_strength(self, password: str) -> None:
        """Add password with strength calculation for sorting"""
        if password and password not in self.generated_passwords:
            self.generated_passwords.add(password)
            strength = PasswordStrengthCalculator.calculate_complexity_score(password)
            self.password_strength_map[strength].append(password)

    def get_sorted_passwords(self) -> List[str]:
        """Get passwords sorted by strength (strongest first)"""
        sorted_passwords = []
        
        # Sort by strength (highest first)
        for strength in sorted(self.password_strength_map.keys(), reverse=True):
            # Shuffle passwords of same strength for variety
            passwords = self.password_strength_map[strength][:]
            secrets.SystemRandom().shuffle(passwords)
            sorted_passwords.extend(passwords)
        
        return sorted_passwords

    def save_dictionary(self) -> int:
        """Save generated dictionary with professional formatting"""
        if not self.input_profile:
            self.print_status("No input profile available", "error")
            return 0
            
        sorted_passwords = self.get_sorted_passwords()
        
        # Apply user limits
        if len(sorted_passwords) < self.input_profile.min_passwords:
            self.print_status(f"Warning: Only {len(sorted_passwords):,} passwords generated, less than minimum {self.input_profile.min_passwords:,}", "warning")
        
        passwords_to_save = sorted_passwords[:self.input_profile.max_passwords]
        
        # Create professional header
        header = f"""# Pass-Bot Enterprise Dictionary Generator
# ==========================================
# 
# 🕷️ Gen-Spider Security Systems - Professional Security Research Tool
# Repository: Pass-Bot Enterprise v1.0.0
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# GENERATION STATISTICS:
# ----------------------
# Total Passwords: {len(passwords_to_save):,}
# Generation Time: {self.generation_stats.generation_time:.2f} seconds
# Unique Combinations: {self.generation_stats.total_generated:,}
# Average Strength: {self.generation_stats.average_strength:.1f}/100
# 
# SORTING METHOD: Strength-Based (Strongest → Weakest)
# STRENGTH LEVELS: EXCEPTIONAL > VERY_STRONG > STRONG > GOOD > MODERATE > WEAK > VERY_WEAK
# 
# INPUT PROFILE:
# --------------
# Base Words: {len(self.input_profile.words)} ({', '.join(self.input_profile.words[:5])})
# Mobile Fragments: {len(self.input_profile.mobile_numbers)}
# Date Fragments: {len(self.input_profile.date_fragments)}  
# Year Range: {len(self.input_profile.year_ranges)} years
# Special Characters: {len(self.input_profile.special_chars)} ({', '.join(self.input_profile.special_chars)})
# Number Patterns: {len(self.input_profile.number_patterns)}
# 
# SECURITY NOTICE:
# ----------------
# This dictionary is generated for authorized security testing purposes only.
# Unauthorized use against systems you do not own is strictly prohibited.
# 
# {"="*80}

"""
        
        try:
            with open(self.input_profile.output_filename, 'w', encoding='utf-8') as f:
                f.write(header)
                
                # Add strength categories for better organization
                current_strength_level = None
                strength_counts = defaultdict(int)
                
                for password in passwords_to_save:
                    strength = PasswordStrengthCalculator.calculate_complexity_score(password)
                    level = PasswordStrengthCalculator.get_strength_level(strength)
                    strength_counts[level] += 1
                    
                    if level != current_strength_level:
                        f.write(f"\n# {level} PASSWORDS (Strength: {strength:.0f}+)\n")
                        f.write(f"# {'-' * 50}\n")
                        current_strength_level = level
                    
                    f.write(password + "\n")
                
                # Add statistics summary
                f.write(f"\n# STRENGTH DISTRIBUTION:\n")
                for level, count in strength_counts.items():
                    percentage = (count / len(passwords_to_save)) * 100
                    f.write(f"# {level}: {count:,} passwords ({percentage:.1f}%)\n")
            
            self.print_status(f"Dictionary saved successfully: {self.input_profile.output_filename}", "success")
            return len(passwords_to_save)
            
        except Exception as e:
            self.print_status(f"Failed to save dictionary: {str(e)}", "error")
            return 0

    def display_generation_summary(self, saved_count: int) -> None:
        """Display comprehensive generation summary with enterprise styling"""
        if RICH_AVAILABLE and self.ui.console:
            # Main statistics table
            stats_table = Table(title="🔐 Pass-Bot Generation Summary", show_header=True, header_style="bold cyan")
            stats_table.add_column("Metric", style="cyan", no_wrap=True)
            stats_table.add_column("Value", style="bright_green", justify="right")
            stats_table.add_column("Details", style="white")
            
            stats_table.add_row("Total Generated", f"{self.generation_stats.total_generated:,}", "Unique passwords created")
            stats_table.add_row("Saved to File", f"{saved_count:,}", f"Written to {self.input_profile.output_filename}")
            stats_table.add_row("Generation Time", f"{self.generation_stats.generation_time:.2f}s", "Total processing time")
            stats_table.add_row("Average Strength", f"{self.generation_stats.average_strength:.1f}/100", "Mean complexity score")
            stats_table.add_row("Sorting Method", "Strength-Based", "Strongest passwords first")
            
            self.ui.console.print("\n")
            self.ui.console.print(stats_table)
            
            # Sample passwords preview
            if saved_count > 0:
                sorted_passwords = self.get_sorted_passwords()[:15]
                
                preview_table = Table(title="🎯 Sample Strongest Passwords", show_header=True, header_style="bold green")
                preview_table.add_column("#", style="cyan", width=3, justify="right")
                preview_table.add_column("Password", style="bright_green", no_wrap=True)
                preview_table.add_column("Strength", style="yellow", width=12)
                preview_table.add_column("Score", style="white", width=8, justify="right")
                
                for i, pwd in enumerate(sorted_passwords, 1):
                    strength_score = PasswordStrengthCalculator.calculate_complexity_score(pwd)
                    strength_level = PasswordStrengthCalculator.get_strength_level(strength_score)
                    
                    preview_table.add_row(
                        str(i),
                        pwd[:30] + "..." if len(pwd) > 30 else pwd,
                        strength_level,
                        f"{strength_score:.1f}"
                    )
                
                self.ui.console.print("\n")
                self.ui.console.print(preview_table)
                
        else:
            print(f"\n{Colors.HEADER}{'='*80}")
            print(f"{Colors.HEADER}{'PASS-BOT GENERATION SUMMARY'.center(80)}")
            print(f"{Colors.HEADER}{'='*80}{Colors.RESET}")
            
            print(f"{Colors.SUCCESS}✅ Total Generated: {Colors.BRIGHT_GREEN}{self.generation_stats.total_generated:,}{Colors.RESET}")
            print(f"{Colors.SUCCESS}✅ Saved to File: {Colors.BRIGHT_GREEN}{saved_count:,}{Colors.RESET}")
            print(f"{Colors.SUCCESS}✅ Output File: {Colors.GREEN}{self.input_profile.output_filename}{Colors.RESET}")
            print(f"{Colors.SUCCESS}✅ Generation Time: {Colors.GREEN}{self.generation_stats.generation_time:.2f}s{Colors.RESET}")
            print(f"{Colors.SUCCESS}✅ Average Strength: {Colors.GREEN}{self.generation_stats.average_strength:.1f}/100{Colors.RESET}")
            
            # Sample passwords
            if saved_count > 0:
                sorted_passwords = self.get_sorted_passwords()[:10]
                print(f"\n{Colors.INFO}Sample Strongest Passwords:{Colors.RESET}")
                for i, pwd in enumerate(sorted_passwords, 1):
                    strength = PasswordStrengthCalculator.calculate_complexity_score(pwd)
                    level = PasswordStrengthCalculator.get_strength_level(strength)
                    print(f"{Colors.GREEN}  {i:2d}. {Colors.WHITE}{pwd:<25} {Colors.CYAN}({level}, {strength:.1f}){Colors.RESET}")

    def run_interactive_mode(self) -> int:
        """Main interactive mode execution"""
        try:
            # Display enterprise banner
            self.ui.show_enterprise_banner()
            self.ui.show_matrix_loading("Initializing Pass-Bot Enterprise Security Suite", 2.5)
            
            # Collect user inputs
            self.input_profile = self.collect_user_inputs()
            
            # Generate dictionary
            print(f"\n{Colors.HEADER}🚀 Initiating Enterprise Dictionary Generation...{Colors.RESET}")
            self.generate_comprehensive_dictionary(self.input_profile)
            
            # Save results
            self.print_status("Saving enterprise dictionary to file", "generate")
            saved_count = self.save_dictionary()
            
            # Display comprehensive summary
            self.display_generation_summary(saved_count)
            
            # Final message with matrix effect
            self.ui.show_matrix_loading("Finalizing security protocols", 1.5)
            
            print(f"\n{Colors.BRIGHT_GREEN}{'='*80}")
            print(f"{Colors.BRIGHT_GREEN}🎉 PASS-BOT ENTERPRISE GENERATION COMPLETE! 🎉")
            print(f"{Colors.BRIGHT_GREEN}🕷️ Gen-Spider Security Systems - Mission Accomplished 🕷️")
            print(f"{Colors.BRIGHT_GREEN}{'='*80}{Colors.RESET}")
            
            if RICH_AVAILABLE:
                input(f"\n{Colors.GREEN}Press Enter to exit Pass-Bot Enterprise...{Colors.RESET}")
            else:
                input(f"\n{Colors.GREEN}Press Enter to exit...{Colors.RESET}")
            
            return 0
            
        except KeyboardInterrupt:
            self.print_status("\nGeneration interrupted by user. Exiting safely...", "warning")
            return 1
        except Exception as e:
            self.print_status(f"Critical error occurred: {str(e)}", "error")
            return 1

def main():
    """Main entry point for Pass-Bot Enterprise"""
    try:
        passbot = EnterprisePassBot()
        return passbot.run_interactive_mode()
    except Exception as e:
        print(f"{Colors.ERROR}❌ Fatal error: {str(e)}{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())