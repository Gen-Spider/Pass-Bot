# 🕷️ Pass-Bot — Enterprise Personal Dictionary Generator

<div align="center">

![Pass-Bot](https://img.shields.io/badge/Pass--Bot-v1.2.3--Enterprise-brightgreen?style=for-the-badge&logo=python&logoColor=white)
![Security](https://img.shields.io/badge/Security-Enterprise-red?style=for-the-badge&logo=shield&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

**🔐 Gen‑Spider Enterprise Security Systems**

Professional, live‑monitored personal dictionary generator with matrix‑style UI, safe interrupt + resume, and strong/full generation modes.

[Features](#-enterprise-features) • [Install](#-installation) • [Usage](#-usage) • [UI](#-live-ui--animations) • [Legal](#-legal--responsibility) • [Support](#-enterprise-support)

</div>

---

## 🏢 Enterprise Overview

Pass‑Bot is an enterprise‑grade personal dictionary generator engineered by **Git‑Spider (Gen‑Spider Security Systems)** for professional red teaming, password auditing, and security research. It builds context‑aware combinations from user‑provided elements with real‑time monitoring, zero‑duplicate guarantees, and safe, resumable execution.

---

## 🚀 Enterprise Features

- **Live monitoring dashboard**: Rich tables, progress bars, ETA, memory, disk, and generation rate with matrix banner and animations.
- **Safe Ctrl+C + resume**: Immediate flush to output and persisted checkpoint; resume continues exactly from last phase and position.
- **Incremental output writing**: Passwords are streamed directly to the output file—no data loss on interruption.
- **Separator control**: Absolutely no “-” or “.” used; default is no separator, optional “_” on user consent.
- **Generation modes**:
  - **Full**: Generate all possible combinations until manually interrupted.
  - **Strong**: Emit only strong passwords (complexity score ≥ 60) for high‑quality shortlists.
- **Clean word variations only**: lower, UPPER, Capitalize; no leet number injection (e.g., no ad0min/t6ch).
- **Inputs supported**: base words, mobile fragments, DOB fragments, year ranges, user‑provided specials, number patterns (00/000/0000).
- **Zero duplicates**: Deduplicated across all phases, even across resumes; existing output is read to avoid repeats.

---

## 🎛️ What’s New in v1.2.3

- Removed “-” and “.” separators across all phases; optional “_”.
- “Full” vs “Strong” generation modes with real‑time strength scoring.
- Incremental saving to the same output file during generation.
- Restored enterprise UI/animations with live statistics and ETA.
- Robust interrupt handling and exact resume (phase + position).

---

## 📦 Installation

```bash
# Clone
git clone https://github.com/Gen-Spider/Pass-Bot.git
cd Pass-Bot

# (Optional) Create venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run (auto-installs rich, colorama, psutil if missing)
python passbot.py
```

Pass‑Bot auto‑installs `rich`, `colorama`, and `psutil` on first run if absent.

---

## 🎮 Usage

```bash
python passbot.py
```

Interactive flow includes:
- Provide base words.
- (Optional) Provide mobile numbers, DOB, year range, user symbols, and number patterns (00/000/0000).
- Choose separator policy (no separator by default, optional “_”).
- Choose generation mode: `full` or `strong`.
- Choose output filename.

During generation:
- UI shows live counters, rate, ETA, memory, disk, current phase, and last password.
- Output is appended continuously to your chosen file.
- Press Ctrl+C to safely stop; progress is saved and can be resumed later.

Resume:
- On next run, Pass‑Bot detects prior progress and offers to resume exactly where you left off.

---

## 🖥 Live UI & Animations

- Matrix‑style enterprise banner and animated initialization.
- Rich live layout with two panes: real‑time statistics and progress panel.
- Accurate percent progress computed from estimated total combinations.
- Clean, professional color palette with enterprise status messaging.

---

## 🔧 Generation Details

- Words are expanded to: `lower`, `UPPER`, `Capitalize`.
- Dates are parsed into multiple fragment permutations without adding separators like “-” or “.”.
- Numbers include mobile fragments and optional patterns (00/000/0000).
- Separators used in combinations: `""` only by default, and `"_"` if enabled.
- Strong mode keeps passwords with complexity score ≥ 60; full mode keeps all.

---

## 🧪 Example Scenarios

- Create an exhaustive enterprise list for a target profile using `full` mode with underscore disabled for compact combos.
- Generate a concise, high‑quality shortlist with `strong` mode to prioritize complex, audit‑ready candidates.
- Resume a long‑running session after maintenance; Pass‑Bot continues without duplicates and appends to the same file.

---

## ⚠️ Legal & Responsibility

This project is provided by **Git‑Spider (Gen‑Spider Security Systems)** strictly for **educational** and **authorized security testing** purposes. You are solely responsible for how you use it. The author and organization **will not be responsible** for any misuse, unlawful activity, damage, or policy violations resulting from the use of this software. Always obtain explicit written permission before testing systems you do not own or operate.

- Unauthorized access or testing is illegal in many jurisdictions.
- Use in controlled, consented environments only.
- Comply with all applicable laws, regulations, and organizational policies.

---

## 📄 License

MIT License © 2025 Gen‑Spider Security Systems. See `LICENSE` for details.

---

## 🛠 Enterprise Support

For enterprise engagements, training, or support, contact Gen‑Spider:

- Email: security@gen-spider.com
- LinkedIn: Gen‑Spider Security Systems
- Community: Gen‑Spider Security (Discord)

If Pass‑Bot assists your assessments, consider starring the repo to support continued enterprise tooling.
