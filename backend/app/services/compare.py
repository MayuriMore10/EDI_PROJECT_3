from typing import Dict, Iterable, List


def compare_fields(present_fields: Iterable[str], requirements: Dict[str, bool]):
    present = set(present_fields)
    required = {k for k, v in requirements.items() if v}
    allowed = set(requirements.keys())

    missing_mandatory: List[str] = sorted(list(required - present))
    additional_fields: List[str] = sorted(list(present - allowed))
    return missing_mandatory, additional_fields


