"""
GeM BidWatch — Dedicated Location Normalization Service
Provides verified administrative mappings for Indian States, Union Territories, Districts, and Cities.
Prevents false defaults, cross-state contamination, and silent Bangalore fallbacks.
"""
import re
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


# ─── BENGALURU URBAN TARGET CONSTANTS & STATUSES ────────────────────────────
TARGET_COUNTRY = "India"
TARGET_STATE = "KARNATAKA"
TARGET_DISTRICT = "Bengaluru Urban"
TARGET_CITY = "Bengaluru"
TARGET_DISPLAY = "Bengaluru Urban, Karnataka"

# Exact required verification lifecycle statuses
STATUS_VERIFIED_BENGALURU_URBAN = "VERIFIED_BENGALURU_URBAN"
STATUS_VERIFIED_BENGALURU_CITY = "VERIFIED_BENGALURU_CITY"
STATUS_PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_OUTSIDE_TARGET = "OUTSIDE_TARGET"
STATUS_UNKNOWN = "UNKNOWN"

# Bengaluru Urban Postal PIN Code Range: 560001 - 560110
BENGALURU_URBAN_PIN_MIN = 560001
BENGALURU_URBAN_PIN_MAX = 560110

# Known Bengaluru Rural / Peripheral taluks & towns
BENGALURU_RURAL_TOWNS = {
    "doddaballapur", "doddaballapura", "nelamangala", "devanahalli",
    "hoskote", "hosakote", "kanakapura", "ramanagara", "channapatna", "magadi"
}

# Verified institutional & industrial campuses strictly within Bengaluru Urban
BENGALURU_URBAN_CAMPUSES = {
    "raj bhavan", "ursc", "isro", "drdo", "ade", "iisc", "hal", "c-dac",
    "vidhana soudha", "vikasa soudha", "ms building", "vimanapura", "malleswaram",
    "koramangala", "indiranagar", "jayanagar", "whitefield", "electronic city",
    "peenya", "shivajinagar", "yelahanka", "hebbal", "rajajinagar", "bellary road",
    "queens road", "mg road", "richmond road", "kengeri", "btm layout", "hsr layout",
    "banashankari", "basavanagudi", "ulsoor", "frazer town", "domlur", "marathahalli",
    "cv raman nagar", "bannerghatta road", "byappanahalli", "yeshwanthpur", "kr puram",
    "victoria hospital", "bowring hospital", "nimhans", "central revenue building"
}


@dataclass
class NormalizedLocation:
    city: Optional[str]
    district: Optional[str]
    state: Optional[str]
    raw_text: str
    confidence: str  # VERIFIED, NORMALIZED, AMBIGUOUS, UNKNOWN
    display_location: str
    target_status: str = STATUS_UNKNOWN


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

    target_st, _, norm_c, norm_d, norm_s = classify_bengaluru_urban(
        city=canonical_city,
        district=canonical_district,
        state=resolved_state,
        raw_text=raw_combined,
    )

    return NormalizedLocation(
        city=canonical_city,
        district=canonical_district,
        state=resolved_state,
        raw_text=raw_combined,
        confidence=confidence,
        display_location=display,
        target_status=target_st,
    )


def classify_bengaluru_urban(
    city: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    raw_text: Optional[str] = None,
    pincode: Optional[str] = None,
) -> Tuple[str, float, Optional[str], Optional[str], Optional[str]]:
    """
    Authoritative classification for Bengaluru Urban, Karnataka.
    
    Returns:
        (status, confidence, normalized_city, normalized_district, normalized_state)
    where status is strictly one of:
        - VERIFIED_BENGALURU_URBAN
        - PARTIALLY_VERIFIED
        - AMBIGUOUS
        - OUTSIDE_TARGET
        - UNKNOWN
    """
    all_elements = [str(x) for x in [city, district, state, raw_text, pincode] if x]
    if not all_elements:
        return STATUS_UNKNOWN, 0.0, None, None, None

    combined = clean_text(" ".join(all_elements)).lower()
    if not combined:
        return STATUS_UNKNOWN, 0.0, None, None, None

    # 1. Explicit Bengaluru Rural rejection
    if re.search(r"\b(?:bengaluru|bangalore)\s+rural\b", combined) or (district and "rural" in str(district).lower()):
        return STATUS_OUTSIDE_TARGET, 0.0, "Bengaluru Rural", "Bengaluru Rural", "KARNATAKA"

    for r_town in BENGALURU_RURAL_TOWNS:
        if re.search(r"\b" + re.escape(r_town) + r"\b", combined) and not re.search(r"\burban\b", combined):
            return STATUS_OUTSIDE_TARGET, 0.0, r_town.title(), "Bengaluru Rural", "KARNATAKA"

    # 2. Check for explicit outside states and known outside cities
    outside_states = [
        "rajasthan", "uttarakhand", "bihar", "delhi", "maharashtra", "uttar pradesh",
        "west bengal", "gujarat", "punjab", "haryana", "kerala", "tamil nadu",
        "telangana", "andhra pradesh", "madhya pradesh", "odisha", "assam", "jharkhand"
    ]
    outside_cities = [
        "jodhpur", "jaipur", "udaipur", "kota", "bikaner", "ajmer", "alwar",
        "dehradun", "haridwar", "roorkee", "rishikesh", "nainital",
        "patna", "munger", "gaya", "bhagalpur", "muzaffarpur",
        "mumbai", "pune", "nagpur", "nashik", "lucknow", "kanpur", "noida",
        "chennai", "coimbatore", "kolkata", "howrah", "hyderabad", "secunderabad",
        "mysore", "mysuru", "hubli", "dharwad", "belgaum", "belagavi", "mangalore", "mangaluru"
    ]

    has_outside_city = any(re.search(r"\b" + re.escape(c) + r"\b", combined) for c in outside_cities)
    has_outside_state = any(re.search(r"\b" + re.escape(s) + r"\b", combined) for s in outside_states)

    # If explicitly points to another location and has no Bangalore mention
    if (has_outside_city or has_outside_state) and not re.search(r"\b(?:bengaluru|bangalore)\b", combined):
        out_state = None
        for s in outside_states:
            if re.search(r"\b" + re.escape(s) + r"\b", combined):
                out_state = resolve_state(s)
                break
        return STATUS_OUTSIDE_TARGET, 0.0, city, district, out_state or state

    # If it has both an outside location and Bangalore without clear resolution -> AMBIGUOUS
    if has_outside_city and re.search(r"\b(?:bengaluru|bangalore)\b", combined):
        return STATUS_AMBIGUOUS, 0.35, "Bengaluru", "Ambiguous", "KARNATAKA"

    # 3. Check Postal PIN Code
    if pincode:
        try:
            pin_digits = re.findall(r"\b([1-9][0-9]{5})\b", str(pincode))
            if pin_digits:
                pin_int = int(pin_digits[0])
                if BENGALURU_URBAN_PIN_MIN <= pin_int <= BENGALURU_URBAN_PIN_MAX:
                    return STATUS_VERIFIED_BENGALURU_URBAN, 0.95, "Bengaluru", "Bengaluru Urban", "KARNATAKA"
                elif 561000 <= pin_int <= 562999:
                    return STATUS_OUTSIDE_TARGET, 0.0, "Bengaluru Rural", "Bengaluru Rural", "KARNATAKA"
                elif pin_int < 560000 or pin_int >= 600000:
                    return STATUS_OUTSIDE_TARGET, 0.0, city, district, state
        except Exception:
            pass

    # 4. Explicit Bengaluru Urban district check
    if (
        re.search(r"\b(?:bengaluru|bangalore)\s*urban\b", combined)
        or (district and "urban" in str(district).lower() and re.search(r"\b(?:bengaluru|bangalore)\b", combined))
        or re.search(r"\bverified\s+bengaluru\s+urban\s+district\b", combined)
        or re.search(r"\bverified\s+bangalore\s+urban\s+district\b", combined)
    ):
        return STATUS_VERIFIED_BENGALURU_URBAN, 0.95, "Bengaluru", "Bengaluru Urban", "KARNATAKA"

    # 5. Check 'district unknown' or generic Bangalore without urban validation -> REVIEW
    if "district unknown" in combined or re.search(r"\bdistrict\s+unknown\b", combined):
        return STATUS_PARTIALLY_VERIFIED, 0.50, "Bengaluru", "District Unknown", "KARNATAKA"

    # 6. Check verified institutional & industrial campuses within Bengaluru Urban
    if any(re.search(r"\b" + re.escape(campus) + r"\b", combined) for campus in BENGALURU_URBAN_CAMPUSES):
        return STATUS_VERIFIED_BENGALURU_URBAN, 0.90, "Bengaluru", "Bengaluru Urban", "KARNATAKA"

    # 7. Check verified aliases:
    # "Bengaluru", "Bangalore", "Bengaluru City", "Bangalore City", "Bengaluru, Karnataka", "Bangalore, Karnataka"
    has_blr = bool(re.search(r"\b(?:bengaluru|bangalore)\b", combined))
    has_karnataka = bool(re.search(r"\bkarnataka\b", combined)) or (state and resolve_state(state) == "KARNATAKA")

    if has_blr and has_karnataka:
        # City-level verified match (Bengaluru / Bangalore city in Karnataka)
        return STATUS_VERIFIED_BENGALURU_CITY, 0.90, "Bengaluru", "Bengaluru", "KARNATAKA"

    if has_blr and not has_karnataka:
        # Bare 'Bangalore' without verified state context -> PARTIALLY_VERIFIED (REVIEW)
        return STATUS_PARTIALLY_VERIFIED, 0.50, "Bengaluru", "District Unknown", "KARNATAKA"

    # 8. Everything else is outside target
    return STATUS_OUTSIDE_TARGET, 0.0, city, district, state


# Compatibility alias
classify_bengaluru_target = classify_bengaluru_urban


def resolve_effective_bid_delivery_location(
    bid_or_dict,
) -> Tuple[str, float, Optional[str], Optional[str], Optional[str]]:
    """
    Evaluates bid delivery location strictly by priority:
    1. Verified PDF delivery/consignee address (pdf_delivery_*)
    2. Structured source delivery location (delivery_*)
    3. Consignee location (consignee_*)
    
    IMPORTANT: Buyer location (buyer_*) is strictly excluded from delivery matching.
    """
    def g(key):
        if hasattr(bid_or_dict, key):
            return getattr(bid_or_dict, key)
        if isinstance(bid_or_dict, dict):
            return bid_or_dict.get(key)
        return None

    pdf_addr = g("pdf_delivery_address")
    pdf_city = g("pdf_delivery_city")
    pdf_dist = g("pdf_delivery_district")
    pdf_state = g("pdf_delivery_state")
    pdf_pin = g("pdf_delivery_pincode")

    # Priority 1: PDF Extracted Delivery Address
    # Check if address is a diagnostic/failure placeholder rather than an address
    is_placeholder = bool(
        pdf_addr and any(p in str(pdf_addr).lower() for p in [
            "could not be verified", "unavailable", "not available", "not found"
        ])
    )
    valid_pdf_addr = None if is_placeholder else pdf_addr

    if any([valid_pdf_addr, pdf_city, pdf_state, pdf_pin]):
        st, conf, c, d, s = classify_bengaluru_urban(
            city=pdf_city,
            district=pdf_dist,
            state=pdf_state,
            raw_text=valid_pdf_addr,
            pincode=pdf_pin,
        )
        if st in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_CITY, STATUS_PARTIALLY_VERIFIED, STATUS_AMBIGUOUS):
            return st, conf, c, d, s
        elif st == STATUS_OUTSIDE_TARGET and any([pdf_city, pdf_state, pdf_pin]):
            return st, conf, c, d, s

    # Priority 2: Structured source delivery location
    del_addr = g("delivery_address")
    del_city = g("delivery_city")
    del_dist = g("delivery_district")
    del_state = g("delivery_state")
    if any([del_addr, del_city, del_state]):
        st, conf, c, d, s = classify_bengaluru_urban(
            city=del_city,
            district=del_dist,
            state=del_state,
            raw_text=del_addr,
        )
        if st in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_CITY, STATUS_PARTIALLY_VERIFIED, STATUS_AMBIGUOUS):
            return st, conf, c, d, s
        elif st == STATUS_OUTSIDE_TARGET and any([del_city, del_state]):
            return st, conf, c, d, s

    # Priority 3: Consignee location
    cons_city = g("consignee_city")
    cons_dist = g("consignee_district")
    cons_state = g("consignee_state")
    raw_loc = g("raw_location_text") or g("dept_name")
    if any([cons_city, cons_state, raw_loc]):
        st, conf, c, d, s = classify_bengaluru_urban(
            city=cons_city,
            district=cons_dist,
            state=cons_state,
            raw_text=raw_loc,
        )
        return st, conf, c, d, s

    return STATUS_UNKNOWN, 0.0, None, None, None

