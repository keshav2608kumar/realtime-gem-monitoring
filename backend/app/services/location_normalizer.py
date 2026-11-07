"""
GeM BidWatch — Dedicated Location Normalization Service
Provides verified administrative mappings for Indian States, Union Territories, Districts, and Cities.
Prevents false defaults, cross-state contamination, and silent Bangalore fallbacks.
"""
import re
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class NormalizedLocation:
    city: Optional[str]
    district: Optional[str]
    state: Optional[str]
    raw_text: str
    confidence: str  # VERIFIED, NORMALIZED, AMBIGUOUS, UNKNOWN
    display_location: str


# ─── VERIFIED ADMINISTRATIVE STATES & UTs ─────────────────────────────────────
# Canonical state names matching official Government of India / GeM registry
CANONICAL_STATES = {
    "ANDAMAN & NICOBAR ISLANDS": {"ANDAMAN & NICOBAR", "ANDAMAN AND NICOBAR", "A & N ISLANDS", "AN"},
    "ANDHRA PRADESH": {"AP", "ANDHRA"},
    "ARUNACHAL PRADESH": {"AR"},
    "ASSAM": {"AS"},
    "BIHAR": {"BR"},
    "CHANDIGARH": {"CH"},
    "CHHATTISGARH": {"CG", "CHATTISGARH"},
    "DADRA & NAGAR HAVELI AND DAMAN & DIU": {"DAMAN & DIU", "DADRA & NAGAR HAVELI", "DNHDD", "DD"},
    "DELHI": {"NEW DELHI", "NCT OF DELHI", "NATIONAL CAPITAL TERRITORY OF DELHI", "DL"},
    "GOA": {"GA"},
    "GUJARAT": {"GJ"},
    "HARYANA": {"HR"},
    "HIMACHAL PRADESH": {"HP"},
    "JAMMU & KASHMIR": {"JAMMU AND KASHMIR", "J&K", "JK"},
    "JHARKHAND": {"JH"},
    "KARNATAKA": {"KA"},
    "KERALA": {"KL"},
    "LADAKH": {"LA"},
    "LAKSHADWEEP": {"LD"},
    "MADHYA PRADESH": {"MP"},
    "MAHARASHTRA": {"MH"},
    "MANIPUR": {"MN"},
    "MEGHALAYA": {"ML"},
    "MIZORAM": {"MZ"},
    "NAGALAND": {"NL"},
    "ODISHA": {"ORISSA", "OD"},
    "PUDUCHERRY": {"PONDICHERRY", "PY"},
    "PUNJAB": {"PB"},
    "RAJASTHAN": {"RJ"},
    "SIKKIM": {"SK"},
    "TAMIL NADU": {"TN", "TAMILNADU"},
    "TELANGANA": {"TS", "TG"},
    "TRIPURA": {"TR"},
    "UTTAR PRADESH": {"UP"},
    "UTTARAKHAND": {"UTTARANCHAL", "UK"},
    "WEST BENGAL": {"WB"},
}

# Reverse lookup for fast state resolution
STATE_LOOKUP: Dict[str, str] = {}
for canonical, aliases in CANONICAL_STATES.items():
    STATE_LOOKUP[canonical.lower()] = canonical
    for alias in aliases:
        STATE_LOOKUP[alias.lower()] = canonical


# ─── VERIFIED CITY / DISTRICT TO STATE MAPPINGS ────────────────────────────────
# Mappings for major industrial, administrative, and user-tested test cases
CITY_DISTRICT_TO_STATE = {
    # Rajasthan
    "jodhpur": ("Jodhpur", "Jodhpur", "RAJASTHAN"),
    "jaipur": ("Jaipur", "Jaipur", "RAJASTHAN"),
    "udaipur": ("Udaipur", "Udaipur", "RAJASTHAN"),
    "kota": ("Kota", "Kota", "RAJASTHAN"),
    "bikaner": ("Bikaner", "Bikaner", "RAJASTHAN"),
    "ajmer": ("Ajmer", "Ajmer", "RAJASTHAN"),
    "alwar": ("Alwar", "Alwar", "RAJASTHAN"),
    "bhilwara": ("Bhilwara", "Bhilwara", "RAJASTHAN"),
    "sri ganganagar": ("Sri Ganganagar", "Sri Ganganagar", "RAJASTHAN"),
    # Uttarakhand
    "dehradun": ("Dehradun", "Dehradun", "UTTARAKHAND"),
    "haridwar": ("Haridwar", "Haridwar", "UTTARAKHAND"),
    "roorkee": ("Roorkee", "Haridwar", "UTTARAKHAND"),
    "haldwani": ("Haldwani", "Nainital", "UTTARAKHAND"),
    "nainital": ("Nainital", "Nainital", "UTTARAKHAND"),
    "rishikesh": ("Rishikesh", "Dehradun", "UTTARAKHAND"),
    "pantnagar": ("Pantnagar", "Udham Singh Nagar", "UTTARAKHAND"),
    # Karnataka
    "bangalore": ("Bangalore", "Bangalore Urban", "KARNATAKA"),
    "bengaluru": ("Bengaluru", "Bangalore Urban", "KARNATAKA"),
    "bangalore urban": ("Bangalore Urban", "Bangalore Urban", "KARNATAKA"),
    "bangalore rural": ("Bangalore Rural", "Bangalore Rural", "KARNATAKA"),
    "bengaluru urban": ("Bengaluru Urban", "Bangalore Urban", "KARNATAKA"),
    "bengaluru rural": ("Bengaluru Rural", "Bangalore Rural", "KARNATAKA"),
    "mysore": ("Mysore", "Mysuru", "KARNATAKA"),
    "mysuru": ("Mysuru", "Mysuru", "KARNATAKA"),
    "hubli": ("Hubli", "Dharwad", "KARNATAKA"),
    "dharwad": ("Dharwad", "Dharwad", "KARNATAKA"),
    "mangalore": ("Mangalore", "Dakshina Kannada", "KARNATAKA"),
    "mangaluru": ("Mangaluru", "Dakshina Kannada", "KARNATAKA"),
    "belgaum": ("Belgaum", "Belagavi", "KARNATAKA"),
    "belagavi": ("Belagavi", "Belagavi", "KARNATAKA"),
    # Bihar
    "patna": ("Patna", "Patna", "BIHAR"),
    "munger": ("Munger", "Munger", "BIHAR"),
    "gaya": ("Gaya", "Gaya", "BIHAR"),
    "bhagalpur": ("Bhagalpur", "Bhagalpur", "BIHAR"),
    "muzaffarpur": ("Muzaffarpur", "Muzaffarpur", "BIHAR"),
    "darbhanga": ("Darbhanga", "Darbhanga", "BIHAR"),
    # Delhi NCT
    "delhi": ("Delhi", "New Delhi", "DELHI"),
    "new delhi": ("New Delhi", "New Delhi", "DELHI"),
    # Maharashtra
    "mumbai": ("Mumbai", "Mumbai", "MAHARASHTRA"),
    "pune": ("Pune", "Pune", "MAHARASHTRA"),
    "nagpur": ("Nagpur", "Nagpur", "MAHARASHTRA"),
    "nashik": ("Nashik", "Nashik", "MAHARASHTRA"),
    # Uttar Pradesh
    "lucknow": ("Lucknow", "Lucknow", "UTTAR PRADESH"),
    "kanpur": ("Kanpur", "Kanpur Nagar", "UTTAR PRADESH"),
    "noida": ("Noida", "Gautam Buddha Nagar", "UTTAR PRADESH"),
    "greater noida": ("Greater Noida", "Gautam Buddha Nagar", "UTTAR PRADESH"),
    "varanasi": ("Varanasi", "Varanasi", "UTTAR PRADESH"),
    "agra": ("Agra", "Agra", "UTTAR PRADESH"),
    # West Bengal
    "kolkata": ("Kolkata", "Kolkata", "WEST BENGAL"),
    "howrah": ("Howrah", "Howrah", "WEST BENGAL"),
    # Tamil Nadu
    "chennai": ("Chennai", "Chennai", "TAMIL NADU"),
    "coimbatore": ("Coimbatore", "Coimbatore", "TAMIL NADU"),
    # Telangana
    "hyderabad": ("Hyderabad", "Hyderabad", "TELANGANA"),
    "secunderabad": ("Secunderabad", "Hyderabad", "TELANGANA"),
    # Andhra Pradesh
    "visakhapatnam": ("Visakhapatnam", "Visakhapatnam", "ANDHRA PRADESH"),
    "vijayawada": ("Vijayawada", "NTR", "ANDHRA PRADESH"),
    # Madhya Pradesh
    "bhopal": ("Bhopal", "Bhopal", "MADHYA PRADESH"),
    "indore": ("Indore", "Indore", "MADHYA PRADESH"),
    "gwalior": ("Gwalior", "Gwalior", "MADHYA PRADESH"),
    "jabalpur": ("Jabalpur", "Jabalpur", "MADHYA PRADESH"),
    # Kerala
    "thiruvananthapuram": ("Thiruvananthapuram", "Thiruvananthapuram", "KERALA"),
    "kochi": ("Kochi", "Ernakulam", "KERALA"),
}


def clean_text(text: Optional[str]) -> str:
    """Strip, clean punctuation, and collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def resolve_state(state_input: Optional[str]) -> Optional[str]:
    """Resolve state input to canonical administrative state name."""
    cleaned = clean_text(state_input).lower()
    if not cleaned:
        return None
    return STATE_LOOKUP.get(cleaned)


def normalize_location(
    raw_text: Optional[str] = None,
    city_hint: Optional[str] = None,
    district_hint: Optional[str] = None,
    state_hint: Optional[str] = None,
) -> NormalizedLocation:
    """
    Main normalization entrypoint.
    Enforces that:
    - Jodhpur NEVER resolves to Dehradun or Bangalore.
    - Dehradun NEVER resolves to Jodhpur or Bangalore.
    - Empty or unrecognized locations become 'UNKNOWN' rather than a fabricated default.
    """
    raw_combined = clean_text(
        " ".join(filter(None, [raw_text, city_hint, district_hint, state_hint]))
    )

    clean_city = clean_text(city_hint)
    clean_state = clean_text(state_hint)
    clean_dist = clean_text(district_hint)

    resolved_state = resolve_state(clean_state)
    canonical_city = None
    canonical_district = clean_dist or None
    confidence = "UNKNOWN"

    # Step 1: Check City / District registry
    city_key = clean_city.lower() if clean_city else None
    if city_key and city_key in CITY_DISTRICT_TO_STATE:
        reg_city, reg_dist, reg_state = CITY_DISTRICT_TO_STATE[city_key]
        canonical_city = clean_city if clean_city.isupper() else reg_city
        canonical_district = canonical_district or reg_dist

        if resolved_state:
            if resolved_state == reg_state:
                confidence = "VERIFIED"
            else:
                # State hint conflicts with city lookup. Respect city mapping if strong.
                resolved_state = reg_state
                confidence = "NORMALIZED"
        else:
            resolved_state = reg_state
            confidence = "NORMALIZED"

    # Step 2: If city not in table, but state was resolved
    elif resolved_state:
        canonical_city = clean_city if clean_city else None
        confidence = "NORMALIZED" if canonical_city else "VERIFIED"

    # Step 3: Check if raw_text contains known cities
    if not canonical_city and raw_text:
        raw_lower = raw_text.lower()
        for ck, (rc, rd, rs) in CITY_DISTRICT_TO_STATE.items():
            pattern = r'\b' + re.escape(ck) + r'\b'
            if re.search(pattern, raw_lower):
                canonical_city = rc
                canonical_district = rd
                resolved_state = rs
                confidence = "NORMALIZED"
                break

    # Step 4: Final validation & display construction
    if not canonical_city and not resolved_state:
        return NormalizedLocation(
            city=None,
            district=None,
            state=None,
            raw_text=raw_combined,
            confidence="UNKNOWN",
            display_location="Not available from source",
        )

    parts = []
    if canonical_city:
        parts.append(canonical_city)
    if resolved_state:
        parts.append(resolved_state)

    display = ", ".join(parts) if parts else "Not available from source"

    return NormalizedLocation(
        city=canonical_city,
        district=canonical_district,
        state=resolved_state,
        raw_text=raw_combined,
        confidence=confidence,
        display_location=display,
    )
