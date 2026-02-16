"""
Court names mapping for Indian High Courts
Based on official eCourts data
"""

COURT_NAMES = {
    ("1", None): "Bombay High Court - Appellate Side, Bombay",
    ("1", "2"): "Bombay High Court - Original Side, Bombay",
    ("1", "3"): "Bombay High Court - Bench At Aurangabad",
    ("1", "4"): "Bombay High Court - Bench At Nagpur",
    ("1", "5"): "Bombay High Court at Goa",
    ("1", "6"): "Bombay High Court - Special Court (TORTS)",
    ("2", None): "High Court of Andhra Pradesh",
    ("3", None): "High Court of Karnataka - Principal Bench at Bengaluru",
    ("3", "2"): "High Court of Karnataka - Dharwad Bench",
    ("3", "3"): "High Court of Karnataka - Kalburagi Bench",
    ("4", None): "High Court of Kerala",
    ("5", None): "High Court of Himachal Pradesh",
    ("6", None): "Gauhati High Court - Principal Seat at Guwahati",
    ("6", "2"): "Gauhati High Court - Kohima Bench",
    ("6", "3"): "Gauhati High Court - Aizawl Bench",
    ("6", "4"): "Gauhati High Court - Itanagar Bench",
    ("7", None): "High Court of Jharkhand",
    ("8", None): "High Court of Judicature at Patna",
    ("9", None): "Rajasthan High Court - Bench at Jaipur",
    ("9", "2"): "Rajasthan High Court - Principal Seat, Jodhpur",
    ("10", None): "Madras High Court - Principal Bench",
    ("10", "2"): "Madras High Court - Madurai Bench",
    ("11", None): "High Court of Orissa",
    ("12", None): "High Court of Jammu and Kashmir - Jammu Wing",
    ("12", "2"): "High Court of Jammu and Kashmir - Srinagar Wing",
    ("13", None): "High Court of Judicature at Allahabad",
    ("13", "2"): "Allahabad High Court - Lucknow Bench",
    ("15", None): "High Court of Uttarakhand",
    ("16", None): "Calcutta High Court - Original Side",
    ("16", "2"): "Calcutta High Court - Circuit Bench At Jalpaiguri",
    ("16", "3"): "Calcutta High Court - Appellate Side",
    ("16", "4"): "Calcutta High Court - Circuit Bench At Port Blair",
    ("17", None): "High Court of Gujarat",
    ("18", None): "High Court of Chhattisgarh",
    ("20", None): "High Court of Tripura",
    ("21", None): "High Court of Meghalaya",
    ("24", None): "High Court of Sikkim",
    ("25", None): "High Court of Manipur",
    ("29", None): "High Court for the State of Telangana",
}

def get_court_name(state_code: str, court_code: str = None) -> str:
    """Get the full court name from state and court codes"""
    # Normalize court_code
    if court_code == "1":
        court_code = None
    
    key = (state_code, court_code)
    return COURT_NAMES.get(key, f"High Court - State {state_code}" + 
                           (f" - Bench {court_code}" if court_code else ""))
