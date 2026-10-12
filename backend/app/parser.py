"""Resume text extraction and skill extraction (spaCy PhraseMatcher + rules)."""
import io
import re
from dataclasses import dataclass, field

import spacy
from spacy.matcher import PhraseMatcher

from .skills_data import TAXONOMY

SECTION_HEADINGS = {
    "skills": r"(technical\s+)?skills|core competencies|technologies",
    "experience": r"(professional\s+|work\s+|research\s+)?experience|internships?|employment",
    "projects": r"projects?|personal projects|academic projects",
    "education": r"education|academics|qualifications",
    "achievements": r"achievements?|awards|honou?rs|certifications?",
    "leadership": r"leadership|positions of responsibility|extracurriculars?",
}
_HEADING_RE = {
    k: re.compile(rf"^\s*(?:{v})\s*:?\s*$", re.IGNORECASE) for k, v in SECTION_HEADINGS.items()
}
_DATE_RANGE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4})\s*[-–—to]+\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4}|present|current)",
    re.IGNORECASE,
)
_DEGREE = re.compile(r"\b(b\.?\s?tech|b\.?e\.?|b\.?sc|m\.?\s?tech|m\.?sc|m\.?s\.?|ph\.?d|mba|bca|mca)\b", re.IGNORECASE)
_BULLET = re.compile(r"^\s*[•\-\*▪●◦]\s+")
# "C" is too ambiguous for a phrase matcher; accept it only as a standalone list item.
_C_LANG = re.compile(r"(?:^|[,/|•·;:(])[ \t]*C[ \t]*(?=[,/|•·;)]|$)(?![+#])", re.MULTILINE)

_nlp = None
_matcher = None
_canon = {}


def _load(model_name: str):
    global _nlp, _matcher, _canon
    if _nlp is not None:
        return
    _nlp = spacy.load(model_name, disable=["ner", "lemmatizer"])
    _matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    for canonical, (_, aliases) in TAXONOMY.items():
        terms = set(aliases)
        if canonical not in ("Testing", "C"):  # too generic or handled by a dedicated rule
            terms.add(canonical.lower())
        docs = [_nlp.make_doc(t) for t in terms]
        key = canonical
        _matcher.add(key, docs)
        _canon[key] = canonical


@dataclass
class ParsedResume:
    skills: dict = field(default_factory=dict)      # canonical -> {"evidence": "applied"|"listed", "category": str}
    sections: list = field(default_factory=list)
    degrees: list = field(default_factory=list)
    date_ranges: int = 0
    bullet_count: int = 0
    word_count: int = 0


MAX_PDF_PAGES = 10
MAX_DOCX_UNCOMPRESSED = 20 * 1024 * 1024  # guards against zip bombs


def extract_text(data: bytes, filename: str) -> str:
    """Extract text after checking the file's real type, not just its extension."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise ValueError("That file is not a valid PDF.")
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDF has too many pages (max {MAX_PDF_PAGES}). Upload just your resume.")
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        import zipfile
        if not data.startswith(b"PK\x03\x04"):
            raise ValueError("That file is not a valid DOCX.")
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if sum(i.file_size for i in z.infolist()) > MAX_DOCX_UNCOMPRESSED:
                raise ValueError("DOCX file is too large once unpacked.")
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    if name.endswith(".txt") or not name:
        if b"\x00" in data:
            raise ValueError("That file does not look like plain text.")
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Unsupported file type. Upload a PDF, DOCX or TXT file.")


def split_sections(text: str) -> dict:
    sections, current = {"header": []}, "header"
    for line in text.splitlines():
        stripped = line.strip()
        matched = next((k for k, rx in _HEADING_RE.items() if rx.match(stripped)), None)
        if matched:
            current = matched
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def _find_skills(text: str, model_name: str) -> set:
    _load(model_name)
    doc = _nlp(text)
    found = {_canon[_nlp.vocab.strings[mid]] for mid, _, _ in _matcher(doc)}
    if _C_LANG.search(text):
        found.add("C")
    return found


def parse_resume(text: str, model_name: str = "en_core_web_sm") -> ParsedResume:
    text = re.sub(r"[ \t]+", " ", text or "").strip()
    sections = split_sections(text)
    applied_text = "\n".join(sections.get(k, "") for k in ("experience", "projects", "achievements", "leadership"))
    # Inline headings such as "Skills: Python, SQL" land in the header block, so scan it too.
    listed_text = sections.get("skills", "") + "\n" + sections.get("header", "")

    applied = _find_skills(applied_text, model_name) if applied_text else set()
    listed = _find_skills(listed_text, model_name) if listed_text else set()
    # Resumes without clear headings: scan everything and treat as listed evidence.
    if not applied and not listed:
        listed = _find_skills(text, model_name)

    parsed = ParsedResume()
    for skill in applied | listed:
        parsed.skills[skill] = {
            "evidence": "applied" if skill in applied else "listed",
            "category": TAXONOMY[skill][0],
        }
    parsed.sections = [k for k, v in sections.items() if k != "header" and v.strip()]
    parsed.degrees = sorted({m.group(0).lower().replace(" ", "") for m in _DEGREE.finditer(sections.get("education", text))})
    parsed.date_ranges = len(_DATE_RANGE.findall(text))
    parsed.bullet_count = sum(1 for ln in text.splitlines() if _BULLET.match(ln))
    parsed.word_count = len(text.split())
    return parsed
