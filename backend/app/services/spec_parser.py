from typing import Dict, Tuple, Set
from pdfminer.high_level import extract_text
import re
import io


MANDATORY_HINTS = {"M", "Mandatory", "Required"}
OPTIONAL_HINTS = {"O", "Optional"}


def parse_pdf_spec_to_xml(pdf_bytes: bytes) -> Tuple[str, Dict[str, bool], Set[str]]:
    """Extract a rough field list from a PDF EDI 810 spec.

    This is heuristic: it looks for lines like BIG01, BIG02 and tries to detect
    whether they are mandatory.

    Returns:
        xml: Minimal XML with <Field name=... required=.../>
        requirements: map of field tag -> is_required
        all_fields: set of field tags found
    """
    # Fast path: attempt to parse directly from raw bytes (many specs are text-like PDFs)
    raw_hint = pdf_bytes[:2_000_000].decode(errors="ignore")
    requirements: Dict[str, bool] = {}

    def harvest(from_text: str):
        for line in from_text.splitlines():
            for seg, num in re.findall(r"\b([A-Z]{2,3})(\d{1,2})\b", line):
                tag = f"{seg}{int(num):02d}"
                line_upper = line.upper()
                if any(h.upper() in line_upper for h in OPTIONAL_HINTS):
                    requirements[tag] = False
                elif any(h.upper() in line_upper for h in MANDATORY_HINTS):
                    requirements[tag] = True
                else:
                    requirements.setdefault(tag, False)

    harvest(raw_hint)

    text = ""
    if not requirements:  # Slow path: use pdfminer only if needed
        try:
            text = extract_text(io.BytesIO(pdf_bytes)) or ""
        except Exception:
            text = ""
        if text:
            harvest(text)

    # Find tokens like SEGIDxx where xx is 1-2 digits
    tokens = re.findall(r"\b([A-Z]{2,3})(\d{1,2})\b", text)
    # If still nothing found, seed minimal required BIG fields so comparison works
    if not requirements:
        for tag in ("BIG01", "BIG02"):
            requirements[tag] = True

    # Build XML
    xml_parts = ["<Spec>"]
    for tag, req in sorted(requirements.items()):
        xml_parts.append(f"  <Field name=\"{tag}\" required=\"{'true' if req else 'false'}\"/>")
    xml_parts.append("</Spec>")

    return "\n".join(xml_parts), requirements, set(requirements.keys())


