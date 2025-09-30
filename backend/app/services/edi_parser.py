from typing import Tuple, Set


def _detect_separators(edi_text: str) -> Tuple[str, str]:
    # Default X12: element '*', segment '~'
    element = '*'
    segment = '~'
    # Try to infer from ISA if present
    if edi_text.startswith('ISA') and len(edi_text) > 105:
        element = edi_text[3]
        segment = edi_text[105]
    return element, segment


def parse_edi_to_xml(edi_text: str) -> Tuple[str, Set[str], bool]:
    """Parse a simple X12 EDI text into a minimal XML and collect field tags.

    Returns:
        xml: Minimal XML string representation
        present_fields: Set of tags like 'BIG01', 'BIG02', 'REF01', etc.
        is_810: Heuristic check whether it's likely an 810 invoice
    """
    element_sep, segment_sep = _detect_separators(edi_text)
    raw_segments = [s for s in edi_text.strip().split(segment_sep) if s]
    is_810 = False
    present_fields: Set[str] = set()

    xml_parts = ["<EDI>"]
    for seg in raw_segments:
        parts = seg.split(element_sep)
        if not parts:
            continue
        seg_id = parts[0].strip()
        if seg_id == 'ST' and any(p.startswith('810') for p in parts[1:3] if p):
            is_810 = True
        # Build field tags seg_id + 2-digit index
        for idx, value in enumerate(parts[1:], start=1):
            if value:
                tag = f"{seg_id}{idx:02d}"
                present_fields.add(tag)
        # Minimal XML representation
        xml_parts.append(f"  <{seg_id}>")
        for idx, value in enumerate(parts[1:], start=1):
            safe_val = (value or '').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append(f"    <E{idx:02d}>{safe_val}</E{idx:02d}>")
        xml_parts.append(f"  </{seg_id}>")
    xml_parts.append("</EDI>")

    return "\n".join(xml_parts), present_fields, is_810


