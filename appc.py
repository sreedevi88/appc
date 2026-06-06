import re
import csv
import io
import streamlit as st
import xml.etree.ElementTree as ET
from pathlib import Path

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KML → CSV Converter",
    page_icon="🗺️",
    layout="centered",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: #ffffff;
    color: #1a1a1a;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

section[data-testid="stFileUploadDropzone"] {
    background: #f8f9fa;
    border: 2px dashed #d1d5db;
    border-radius: 10px;
}
section[data-testid="stFileUploadDropzone"] > div {
    padding: 1rem;
}
section[data-testid="stFileUploadDropzone"] small,
section[data-testid="stFileUploadDropzone"] span[class*="uploadInstructions"],
div[data-testid="stFileUploaderDropzoneInstructions"] > div > small,
div[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    display: none !important;
}
.stFileUploader label {
    font-size: 0.85rem !important;
    color: #555 !important;
}
button[data-testid="baseButton-secondary"] {
    font-size: 0.8rem !important;
}

.stDownloadButton > button {
    background: #2563eb !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.55rem 2rem !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
    margin-top: 1rem;
}
.stDownloadButton > button:hover {
    background: #1d4ed8 !important;
}

.app-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #1a1a1a;
    text-align: center;
    margin: 0.5rem 0 1.2rem 0;
    letter-spacing: 0.01em;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Engine classes
# ═══════════════════════════════════════════════════════════════════════════════

class TransliterationEngine:
    CHAR_MAP = {
        "அ": "a",   "ஆ": "aa",  "இ": "i",   "ஈ": "ee",
        "உ": "u",   "ஊ": "oo",  "எ": "e",   "ஏ": "ae",
        "ஐ": "ai",  "ஒ": "o",   "ஓ": "o",   "ஔ": "ow",
        "க": "ka",  "கா": "kaa","கி": "ki", "கீ": "kee",
        "கு": "ku", "கூ": "koo","கெ": "ke", "கே": "ke",
        "கை": "kai","கொ": "ko", "கோ": "ko", "கௌ": "kow",
        "க்": "k",
        "ங": "nga", "ங்": "ng",
        "ச": "sa",  "சா": "saa","சி": "si", "சீ": "see",
        "சு": "su", "சூ": "soo","செ": "se", "சே": "se",
        "சை": "sai","சொ": "so", "சோ": "so", "சௌ": "sow",
        "ச்": "s",
        "ஞ": "gna", "ஞ்": "gn",
        "ட": "da",  "டா": "daa","டி": "di", "டீ": "dee",
        "டு": "du", "டூ": "doo","டெ": "de", "டே": "de",
        "டை": "dai","டொ": "do", "டோ": "do", "டௌ": "dow",
        "ட்": "t",
        "ண": "na",  "ணா": "naa","ணி": "ni", "ணீ": "nee",
        "ணு": "nu", "ணூ": "noo","ணெ": "ne", "ணே": "ne",
        "ணை": "nai","ணொ": "no", "ணோ": "no",
        "ண்": "n",
        "த": "tha", "தா": "thaa","தி": "thi","தீ": "thee",
        "து": "thu","தூ": "thoo","தெ": "the","தே": "the",
        "தை": "thai","தொ": "tho","தோ": "tho","தௌ": "thow",
        "த்": "th",
        "ந": "na",  "நா": "naa","நி": "ni", "நீ": "nee",
        "நு": "nu", "நூ": "noo","நெ": "ne", "நே": "ne",
        "நை": "nai","நொ": "no", "நோ": "no",
        "ந்": "n",
        "ப": "pa",  "பா": "paa","பி": "pi", "பீ": "pee",
        "பு": "pu", "பூ": "poo","பெ": "pe", "பே": "pe",
        "பை": "pai","பொ": "po", "போ": "po", "பௌ": "pow",
        "ப்": "p",
        "ம": "ma",  "மா": "maa","மி": "mi", "மீ": "mee",
        "மு": "mu", "மூ": "moo","மெ": "me", "மே": "me",
        "மை": "mai","மொ": "mo", "மோ": "mo", "மௌ": "mow",
        "ம்": "m",
        "ய": "ya",  "யா": "yaa","யி": "yi", "யீ": "yee",
        "யு": "yu", "யூ": "yoo","யெ": "ye", "யே": "ye",
        "யை": "yai","யொ": "yo", "யோ": "yo",
        "ய்": "y",
        "ர": "ra",  "ரா": "raa","ரி": "ri", "ரீ": "ree",
        "ரு": "ru", "ரூ": "roo","ரெ": "re", "ரே": "re",
        "ரை": "rai","ரொ": "ro", "ரோ": "ro",
        "ர்": "r",
        "ல": "la",  "லா": "laa","லி": "li", "லீ": "lee",
        "லு": "lu", "லூ": "loo","லெ": "le", "லே": "le",
        "லை": "lai","லொ": "lo", "லோ": "lo",
        "ல்": "l",
        "வ": "va",  "வா": "vaa","வி": "vi", "வீ": "vee",
        "வு": "vu", "வூ": "voo","வெ": "ve", "வே": "ve",
        "வை": "vai","வொ": "vo", "வோ": "vo",
        "வ்": "v",
        "ழ": "la",  "ழா": "laa","ழி": "li", "ழீ": "lee",
        "ழு": "lu", "ழூ": "loo","ழெ": "le", "ழே": "le",
        "ழை": "lai","ழொ": "lo", "ழோ": "lo",
        "ழ்": "l",
        "ள": "la",  "ளா": "laa","ளி": "li", "ளீ": "lee",
        "ளு": "lu", "ளூ": "loo","ளெ": "le", "ளே": "le",
        "ளை": "lai","ளொ": "lo", "ளோ": "lo",
        "ள்": "l",
        "ற": "ra",  "றா": "raa","றி": "ri", "றீ": "ree",
        "று": "ru", "றூ": "roo","றெ": "re", "றே": "re",
        "றை": "rai","றொ": "ro", "றோ": "ro",
        "ற்": "tr",
        "ன": "na",  "னா": "naa","னி": "ni", "னீ": "nee",
        "னு": "nu", "னூ": "noo","னெ": "ne", "னே": "ne",
        "னை": "nai","னொ": "no", "னோ": "no",
        "ன்": "n",
        "ஜ": "ja",  "ஜா": "jaa","ஜி": "ji", "ஜீ": "jee",
        "ஜு": "ju", "ஜூ": "joo","ஜெ": "je", "ஜே": "je",
        "ஜை": "jai","ஜொ": "jo", "ஜோ": "jo",
        "ஜ்": "j",
        "ஷ": "sha","ஷா": "shaa","ஷி": "shi","ஷீ": "shee",
        "ஷு": "shu","ஷூ": "shoo","ஷெ": "she","ஷே": "she",
        "ஷை": "shai","ஷொ": "sho","ஷோ": "sho",
        "ஷ்": "sh",
        "ஸ": "sa",  "ஸா": "saa","ஸி": "si", "ஸீ": "see",
        "ஸு": "su", "ஸூ": "soo","ஸெ": "se", "ஸே": "se",
        "ஸ்": "s",
        "ஹ": "ha",  "ஹா": "haa","ஹி": "hi", "ஹீ": "hee",
        "ஹு": "hu", "ஹூ": "hoo","ஹெ": "he", "ஹே": "he",
        "ஹை": "hai","ஹொ": "ho", "ஹோ": "ho",
        "ஹ்": "h",
        "ஃ": "ah",
        "ா": "aa", "ி": "i",  "ீ": "ee",
        "ு": "u",  "ூ": "oo", "ெ": "e",
        "ே": "e",  "ை": "ai", "ொ": "o",
        "ோ": "o",  "ௌ": "ow", "்": "",
    }

    KEEP_AS_IS = {
        "bus", "stand", "stop", "college", "school", "hospital",
        "office", "market", "park", "bridge", "mill", "station",
        "airport", "library", "court", "bank", "hotel", "lodge",
        "theatre", "theater", "nagar", "salai", "street", "road",
    }

    def convert_word(self, word: str) -> str:
        result = ""
        i = 0
        while i < len(word):
            two = word[i:i+2]
            if two in self.CHAR_MAP:
                result += self.CHAR_MAP[two]
                i += 2
            elif word[i] in self.CHAR_MAP:
                result += self.CHAR_MAP[word[i]]
                i += 1
            else:
                result += word[i]
                i += 1
        return re.sub(r'(.)\1{2,}', r'\1\1', result)

    def _is_tamil(self, text: str) -> bool:
        return any('\u0B80' <= c <= '\u0BFF' for c in text)

    def _is_ascii(self, text: str) -> bool:
        return all(ord(c) < 128 for c in text)

    def convert_text(self, text: str) -> str:
        tokens = text.split(" ")
        out = []
        for token in tokens:
            if not token:
                out.append(token)
            elif token.lower() in self.KEEP_AS_IS:
                out.append(token.capitalize())
            elif self._is_ascii(token):
                out.append(token)
            elif self._is_tamil(token):
                converted = self.convert_word(token)
                out.append(converted[0].upper() + converted[1:] if converted else converted)
            else:
                out.append(token)
        return " ".join(out)


class PhraseTranslator:
    PHRASE_MAP = {
        "பேருந்து நிலையம்": "Bus Stand",
        "பஸ் ஸ்டாண்ட்":    "Bus Stand",
        "பஸ் ஸ்டாப்":      "Bus Stop",
        "பஸ்":             "Bus",
        "ஸ்டாண்ட்":        "Stand",
        "ஸ்டாப்":          "Stop",
        "ஸ்கூல்":          "School",
        "காலேஜ்":          "College",
        "ஆஸ்பத்திரி":      "Hospital",
        "மருத்துவமனை":     "Hospital",
        "மார்க்கெட்":      "Market",
        "ஆபீஸ்":           "Office",
        "டவுன்":            "Town",
        "நகர்":             "Nagar",
        "தெரு":             "Street",
        "சாலை":             "Salai",
        "ரோடு":             "Road",
        "ரோட்":             "Road",
        "தியேட்டர்":        "Theatre",
        "விளக்கு":          "Vilakku",
        "திடல்":            "Thidal",
        "கடை":              "Kadai",
        "சத்திரம்":         "Chatram",
        "விடுதி":           "Viduthi",
        "மில்":             "Mill",
        "கோயில்":           "Kovil",
        "புதுக்கோட்டை பேருந்து நிலையம்": "Pudukottai Bus Stand",
        "புதுக்கோட்டை":    "Pudukottai",
        "அண்டக்குளம்":     "Andakulam",
        "முல்லூர்":         "Mullur",
        "முள்ளூர்":         "Mullur",
        "கண்டக்காரன்பட்டி":"Kandakkaranpatti",
        "மாந்தங்குடி":      "Maanthangudi",
        "பெருங்களூர்":      "Perungalur",
        "பிருந்தாவனம்":     "Brindavanam",
        "ஜீவா நகர்":        "Jeeva Nagar",
        "சரவணா தியேட்டர்": "Saravana Theatre",
        "மெடிக்கல் காலேஜ்":"Medical College",
        "கலைஞர் காலேஜ்":   "Kalaignar College",
        "கலெக்டர் ஆபீஸ்":  "Collector Office",
        "சரவணா":           "Saravana",
        "திலகர்":           "Thilaghar",
        "பழனியப்பா":        "Palaniyappa",
        "சின்னையா":         "Chinnaiya",
        "குலையான்விடுதி":   "Kulaiyanviduthi",
        "கலைஞர்":           "Kalaignar",
        "கலெக்டர்":         "Collector",
        "பால் பண்ணை":       "Paal Pannai",
        "இச்சடி":           "Ichadi",
        "ஆலமரம்":           "Aalamaram",
        "வாராபூர்":         "Varaapoor",
        "மட்டயன் பட்டி":   "Mattayan Patti",
        "நெம்மாளிபட்டி":   "Nemmalipatti",
        "வெல்லவேட்டான்":   "Vellavetaan",
        "வெள்ளவாட்டான்":   "Vellavataan",
        "சிவன்":            "Sivan",
    }

    SUFFIX_MAP = {
        "ஸ்டாப்":     "Stop",
        "ஸ்டாண்ட்":   "Stand",
        "காலேஜ்":     "College",
        "ஸ்கூல்":     "School",
        "மார்க்கெட்": "Market",
        "ஆபீஸ்":      "Office",
        "டவுன்":       "Town",
        "நகர்":        "Nagar",
        "தெரு":        "Street",
        "சாலை":        "Salai",
        "ரோடு":        "Road",
        "ரோட்":        "Road",
    }

    def __init__(self):
        self._engine = TransliterationEngine()
        self._sorted_phrases = sorted(
            self.PHRASE_MAP.items(), key=lambda x: len(x[0]), reverse=True
        )

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        text = text.strip()
        for tamil, english in self._sorted_phrases:
            if text.lower() == tamil.lower():
                return english
        result = text
        for tamil, english in self._sorted_phrases:
            if tamil.lower() in result.lower():
                result = re.compile(re.escape(tamil), re.IGNORECASE).sub(english, result)
        for tamil_suffix, english in self.SUFFIX_MAP.items():
            result = re.sub(re.escape(tamil_suffix), english, result)
        return self._engine.convert_text(result)


class KMLParser:
    NAMESPACE = {"kml": "http://www.opengis.net/kml/2.2"}
    ROUTE_PREFIX_PATTERN = re.compile(
        r"^\s*[A-Za-z]{0,2}\d+[A-Za-z]{0,2}(?=\s|[^\x00-\x7F])\s*"
    )

    def parse_bytes(self, data: bytes) -> list:
        root = ET.fromstring(data)
        waypoints = []
        for pm in root.findall(".//kml:Placemark", self.NAMESPACE):
            name_el  = pm.find("kml:name", self.NAMESPACE)
            coord_el = pm.find(".//kml:coordinates", self.NAMESPACE)
            name = name_el.text.strip() if (name_el is not None and name_el.text) else ""
            lon = lat = ""
            if coord_el is not None and coord_el.text:
                parts = coord_el.text.strip().split(",")
                if len(parts) >= 2:
                    lon = parts[0].strip()
                    lat = parts[1].strip()
            waypoints.append({"name": name, "latitude": lat, "longitude": lon})
        return waypoints

    def strip_route_prefix(self, name: str) -> str:
        return self.ROUTE_PREFIX_PATTERN.sub("", name.strip()).strip()


def convert_to_csv(waypoints: list, source_filename: str, translator, parser) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["S.No", "Name ", "Name ", "Latitude", "Longitude"])
    for i, wp in enumerate(waypoints, 1):
        clean_name    = parser.strip_route_prefix(wp["name"])
        tanglish_name = translator.translate(clean_name)
        writer.writerow([i, clean_name, tanglish_name, wp["latitude"], wp["longitude"]])
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  Streamlit UI
# ═══════════════════════════════════════════════════════════════════════════════

# Title
st.markdown('<div class="app-title">🗺️ KML → CSV Converter</div>', unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("", type=["kml"], label_visibility="collapsed")

if uploaded_file is not None:
    kml_bytes = uploaded_file.read()
    filename  = uploaded_file.name

    parser     = KMLParser()
    translator = PhraseTranslator()

    try:
        waypoints = parser.parse_bytes(kml_bytes)
    except ET.ParseError as e:
        st.error(f"KML parse error: {e}")
        st.stop()

    if not waypoints:
        st.stop()

    csv_text = convert_to_csv(waypoints, filename, translator, parser)
    csv_filename = Path(filename).stem + ".csv"

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_text.encode("utf-8-sig"),
        file_name=csv_filename,
        mime="text/csv",
    )
