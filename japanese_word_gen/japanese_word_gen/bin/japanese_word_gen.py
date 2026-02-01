from os import mkdir
from pathlib import Path
import re
from typing import List, Optional, Dict, Any
import random

WORD_BANK = Path(__file__).parent.parent / "data" / "wordbank.txt"
CACHE_FILE = Path(__file__).parent.parent / "cache" / "recent.txt"
MAX_ATTEMPTS = 1000

def load_word_bank() -> str:
    path = WORD_BANK
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def ensure_env() -> None:
    if not WORD_BANK.parent.exists() :
        mkdir(WORD_BANK.parent)
    if not CACHE_FILE.parent.exists() :
        mkdir(CACHE_FILE.parent)


def parse_line(line: str) -> Optional[Dict[str, Any]]:
    # normalize and skip non-content lines
    raw = line.rstrip("\n")
    stripped = raw.strip()
    if not stripped:
        return None
    if stripped.startswith(("==", "<!--", "-->")):
        return None

    lead = stripped
    if lead.startswith("*"):
        lead = lead[1:].strip()

    if lead.startswith("(") and "{{" not in lead and "[[" not in lead:
        return None

    # split into form and gloss
    parts = re.split(r"\s+[–-]\s+", lead, maxsplit=1)
    left = parts[0].strip()
    right = parts[1].strip() if len(parts) > 1 else ""

    forms: List[str] = []

    forms += [f.strip() for f in re.findall(r"\{\{\s*(?:l|m|link|term)\s*\|\s*ja\s*\|([^}|]+)", left)]
    forms += [f.strip() for f in re.findall(r"\{\{\s*l/ja\s*\|([^}|]+)", left)]
    forms += [f.strip() for f in re.findall(r"\[\[([^|\]]+)", left)]

    # fall back formatting
    if not forms:
        fallback = [seg.strip() for seg in re.split(r"[、,;/]", left) if seg.strip()]
        # strip surrounding braces/brackets/parentheses if any
        fallback = [re.sub(r"^[\{\}\[\]\(\)]+|[\{\}\[\]\(\)]+$", "", s) for s in fallback]
        forms.extend(fallback)

    dedup: List[str] = []
    seen = set()
    for f in forms:
        if not f or f in seen:
            continue
        if re.match(r"=+.*=+", f) or f.startswith("<!--") or f == "-->":
            continue
        seen.add(f)
        dedup.append(f)
    forms = dedup

    if not forms:
        return None

    note_match = re.search(r"\(''\s*([^']+?)\s*''\)", right)
    note = note_match.group(1) if note_match else None

    gloss = re.sub(r"\(''\s*([^']+?)\s*''\)", "", right).strip()
    gloss = re.sub(r"\s+", " ", gloss)

    return {
        "language": "ja",
        "forms": forms,
        "gloss": gloss if gloss else None,
        "note": note,
        "raw": raw,
    }


def parse_word_bank() -> List[Dict[str, Any]]:
    text = load_word_bank()
    entries: List[Dict[str, Any]] = []
    for line in text.splitlines():
        parsed = parse_line(line)
        if parsed:
            entries.append(parsed)
    return entries


def random_word_def(entries) -> str:
    if not entries:
        return ""
    
    if len(entries) == 1:
        cache(1)
        return entries[0]["forms"][0]
    choice = random.randint(0, len(entries) - 1)

    cached = load_cache()
    if len(cached) >= len(entries) - 100 :
        clear_cache() 
    attempts = 0
    while choice in cached and attempts < MAX_ATTEMPTS :
        choice = random.randint(0, len(entries) - 1)

    form = entries[choice]["forms"]
    gloss = entries[choice]["gloss"]

    cache(choice)

    return f"{form} - {gloss}."

def clear_cache() :
    try :
        with open(CACHE_FILE, "w") as f:
            pass
    except IOError as e:
        print(str(e))
        return False
    return True

def cache(choice) -> bool:
    try :
        with open(CACHE_FILE, "a+") as f:
            f.write(f"{choice}\n")
    except IOError as e:
        print(str(e))
        return False
    return True

def load_cache() -> List[str]:
    try :
        with open(CACHE_FILE, "r+") as f:
            return f.readlines()
    except IOError as e:
        print(str(e))
        return []

def main() -> None:
    ensure_env()
    entries = parse_word_bank()
    print(random_word_def(entries))


if __name__ == "__main__":
    main()
