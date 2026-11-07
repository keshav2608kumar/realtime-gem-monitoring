"""
GeM BidWatch — Official Product Category Service
Maintains the 7 canonical GeM product categories, stable identifiers,
controlled normalization, exact matching, and mapping verification.

Exact Category Requirements:
1. Toner Cartridges / Ink Cartridges / Consumables for Printers  -> TONER_INK_PRINTER_CONSUMABLES
2. Scanner (V3)                                                  -> SCANNER_V3
3. A4 and Legal Size Multifunction Printer (MFP)                 -> A4_LEGAL_SIZE_MFP
4. A3 Size Multifunction Printer (MFP)                           -> A3_SIZE_MFP
5. Computer Printer (V2)                                         -> COMPUTER_PRINTER_V2
6. High End Desktop Computer                                     -> HIGH_END_DESKTOP
7. High End Laptop - Notebook                                    -> HIGH_END_LAPTOP_NOTEBOOK
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryDefinition:
    id: str
    display_name: str
    short_code: str
    description: str


# The 7 canonical product categories with exact display names
TARGET_CATEGORIES: List[CategoryDefinition] = [
    CategoryDefinition(
        id="TONER_INK_PRINTER_CONSUMABLES",
        display_name="Toner Cartridges / Ink Cartridges / Consumables for Printers",
        short_code="TONER_CART",
        description="Printer consumables including laser toner, inkjet cartridges, drum units, and ribbons."
    ),
    CategoryDefinition(
        id="SCANNER_V3",
        display_name="Scanner (V3)",
        short_code="SCANNER_V3",
        description="GeM Version 3 document and flatbed scanners."
    ),
    CategoryDefinition(
        id="A4_LEGAL_SIZE_MFP",
        display_name="A4 and Legal Size Multifunction Printer (MFP)",
        short_code="A4_MFP",
        description="A4 and Legal format multi-function printing and scanning devices."
    ),
    CategoryDefinition(
        id="A3_SIZE_MFP",
        display_name="A3 Size Multifunction Printer (MFP)",
        short_code="A3_MFP",
        description="Heavy duty A3 format multifunction commercial digital printers and copiers."
    ),
    CategoryDefinition(
        id="COMPUTER_PRINTER_V2",
        display_name="Computer Printer (V2)",
        short_code="PRINTER_V2",
        description="GeM Version 2 standard departmental and desktop computer printers."
    ),
    CategoryDefinition(
        id="HIGH_END_DESKTOP",
        display_name="High End Desktop Computer",
        short_code="HIGH_END_PC",
        description="Enterprise workstations and high-performance desktop computing systems."
    ),
    CategoryDefinition(
        id="HIGH_END_LAPTOP_NOTEBOOK",
        display_name="High End Laptop - Notebook",
        short_code="HIGH_END_LAPTOP",
        description="High-performance laptops, mobile workstations, and executive notebooks."
    ),
]

CATEGORIES_BY_ID: Dict[str, CategoryDefinition] = {cat.id: cat for cat in TARGET_CATEGORIES}

# Exact source category alias mapping
EXACT_SOURCE_ALIASES: Dict[str, str] = {
    "toner cartridges / ink cartridges / consumables for printers": "TONER_INK_PRINTER_CONSUMABLES",
    "toner cartridges / ink cartridges / consumables for printers (v2)": "TONER_INK_PRINTER_CONSUMABLES",
    "cartridges / consumables for printers": "TONER_INK_PRINTER_CONSUMABLES",
    "scanner (v3)": "SCANNER_V3",
    "scanner v3": "SCANNER_V3",
    "a4 and legal size multifunction printer (mfp)": "A4_LEGAL_SIZE_MFP",
    "a4 and legal size mfp": "A4_LEGAL_SIZE_MFP",
    "a4 & legal size multifunction printer (mfp)": "A4_LEGAL_SIZE_MFP",
    "a3 size multifunction printer (mfp)": "A3_SIZE_MFP",
    "a3 size mfp": "A3_SIZE_MFP",
    "computer printer (v2)": "COMPUTER_PRINTER_V2",
    "computer printer v2": "COMPUTER_PRINTER_V2",
    "high end desktop computer": "HIGH_END_DESKTOP",
    "high end desktop": "HIGH_END_DESKTOP",
    "high end laptop - notebook": "HIGH_END_LAPTOP_NOTEBOOK",
    "high end laptop / notebook": "HIGH_END_LAPTOP_NOTEBOOK",
    "high end laptop": "HIGH_END_LAPTOP_NOTEBOOK",
}

# Regex patterns for controlled matching with explicit version guardrails
CATEGORY_REGEX_RULES = [
    # 1. Toner / Ink / Consumables
    (
        "TONER_INK_PRINTER_CONSUMABLES",
        re.compile(
            r"(?i)\b(?:toner\s*cartridges?|ink\s*cartridges?|consumables\s*for\s*printers?|printer\s*cartridges?)\b"
        ),
    ),
    # 2. Scanner (V3) — Requires explicit Scanner + V3 or standalone Scanner V3
    (
        "SCANNER_V3",
        re.compile(r"(?i)\bscanner\s*\(?v\s*3\)?\b"),
    ),
    # 3. A4 and Legal Size MFP
    (
        "A4_LEGAL_SIZE_MFP",
        re.compile(r"(?i)\ba4\s*(?:and|&)?\s*legal\s*size\s*(?:multifunction(?:\s+\w+)?\s*(?:printer)?|\(?mfp\)?)\b"),
    ),
    # 4. A3 Size MFP
    (
        "A3_SIZE_MFP",
        re.compile(r"(?i)\ba3\s*size\s*(?:multifunction(?:\s+\w+)?\s*(?:printer)?|\(?mfp\)?)\b"),
    ),
    # 5. Computer Printer (V2) — Must distinguish V2 and not confuse with MFP or general printer
    (
        "COMPUTER_PRINTER_V2",
        re.compile(r"(?i)\bcomputer\s*printer\s*\(?v\s*2\)?\b"),
    ),
    # 6. High End Desktop
    (
        "HIGH_END_DESKTOP",
        re.compile(r"(?i)\bhigh\s*end\s*desktop\s*(?:computer)?\b"),
    ),
    # 7. High End Laptop - Notebook
    (
        "HIGH_END_LAPTOP_NOTEBOOK",
        re.compile(r"(?i)\bhigh\s*end\s*laptop\s*[-–/]?\s*(?:notebook)?\b"),
    ),
]


def clean_category_text(text: Optional[str]) -> str:
    """Normalize whitespace and strip punctuation artifacts."""
    if not text:
        return ""
    # Collapse multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def get_all_target_categories() -> List[CategoryDefinition]:
    """Return all 7 target category definitions."""
    return TARGET_CATEGORIES


def is_valid_category_id(cat_id: str) -> bool:
    """Check if category ID is one of the 7 official IDs."""
    return cat_id in CATEGORIES_BY_ID


def get_category_display_name(cat_id: str) -> Optional[str]:
    """Get the exact official display name for a category ID."""
    cat = CATEGORIES_BY_ID.get(cat_id)
    return cat.display_name if cat else None


def match_category(
    category_name: Optional[str],
    cat_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Match and verify a GeM category against the 7 target categories.
    
    Returns:
        (category_key, exact_display_name, mapping_status)
        where mapping_status is:
            'VERIFIED': Exact alias or authoritative code match
            'MAPPED': Controlled regex match against authoritative category text
            'UNMAPPED': Category exists but does not belong to the 7 targets
            'UNKNOWN': Category text is missing or completely ambiguous
    """
    if not category_name and not cat_id:
        return None, None, "UNKNOWN"

    # 1. Check cat_id if directly matches one of our IDs
    if cat_id:
        norm_cid = cat_id.strip().upper()
        if norm_cid in CATEGORIES_BY_ID:
            cat = CATEGORIES_BY_ID[norm_cid]
            return cat.id, cat.display_name, "VERIFIED"

    raw_text = clean_category_text(category_name)
    if not raw_text:
        return None, None, "UNKNOWN"

    norm_lower = raw_text.lower()

    # 2. Exact match against canonical display names
    for cat in TARGET_CATEGORIES:
        if norm_lower == cat.display_name.lower():
            return cat.id, cat.display_name, "VERIFIED"

    # 3. Exact match against known source aliases
    if norm_lower in EXACT_SOURCE_ALIASES:
        target_id = EXACT_SOURCE_ALIASES[norm_lower]
        cat = CATEGORIES_BY_ID[target_id]
        return cat.id, cat.display_name, "VERIFIED"

    # 4. Controlled regex match with strict boundaries and version protection
    for cat_key, pattern in CATEGORY_REGEX_RULES:
        if pattern.search(raw_text):
            cat = CATEGORIES_BY_ID[cat_key]
            return cat.id, cat.display_name, "MAPPED"

    # If category text exists but doesn't match any of the 7 targets:
    return None, None, "UNMAPPED"
