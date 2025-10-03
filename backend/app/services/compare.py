from typing import Dict, Iterable, List, Tuple
from .spec_parser import EDI_810_FIELDS


class FieldLengthError:
    def __init__(self, field_id: str, actual_length: int, expected_min: int, expected_max: int, actual_value: str = ""):
        self.field_id = field_id
        self.actual_length = actual_length
        self.expected_min = expected_min
        self.expected_max = expected_max
        self.actual_value = actual_value
        
    def __str__(self):
        return f"{self.field_id}: Length {self.actual_length}, Expected {self.expected_min}-{self.expected_max}"


class FieldComparisonResult:
    def __init__(self):
        self.mandatory_present: List[str] = []      # Green - Mandatory fields present
        self.mandatory_missing: List[str] = []      # Red - Mandatory fields missing
        self.optional_present: List[str] = []       # Yellow - Optional fields present
        self.optional_missing: List[str] = []       # White - Optional fields missing
        self.additional_fields: List[str] = []      # Fields in EDI but not in spec
        self.length_errors: List[FieldLengthError] = []  # Field length validation errors
        
    def get_all_fields_with_status(self) -> List[Dict[str, str]]:
        """Return all fields with their status and color coding."""
        fields = []
        
        # Green: Mandatory fields present in EDI
        for field in sorted(self.mandatory_present):
            field_info = EDI_810_FIELDS.get(field, {
                "name": "Unknown Field", 
                "usage": "Unknown usage",
                "cardinality": "1/1",
                "type": "AN",
                "length": "1/1"
            })
            
            # Check for length errors
            length_error = next((err for err in self.length_errors if err.field_id == field), None)
            has_length_error = length_error is not None
            
            fields.append({
                "field_name": field,
                "name": field_info["name"],
                "status": "Mandatory",
                "usage": field_info["usage"],
                "cardinality": field_info.get("cardinality", "1/1"),
                "type": field_info.get("type", "AN"),
                "length": field_info.get("length", "1/1"),
                "color": "red" if has_length_error else "green",  # Red if length error, green otherwise
                "present_in_edi": True,
                "length_error": str(length_error) if length_error else ""
            })
        
        # Red: Mandatory fields missing from EDI
        for field in sorted(self.mandatory_missing):
            field_info = EDI_810_FIELDS.get(field, {
                "name": "Unknown Field", 
                "usage": "Unknown usage",
                "cardinality": "1/1",
                "type": "AN",
                "length": "1/1"
            })
            fields.append({
                "field_name": field,
                "name": field_info["name"],
                "status": "Mandatory",
                "usage": field_info["usage"],
                "cardinality": field_info.get("cardinality", "1/1"),
                "type": field_info.get("type", "AN"),
                "length": field_info.get("length", "1/1"),
                "color": "red",
                "present_in_edi": False,
                "length_error": ""
            })
        
        # Yellow: Optional fields present in EDI
        for field in sorted(self.optional_present):
            field_info = EDI_810_FIELDS.get(field, {
                "name": "Unknown Field", 
                "usage": "Unknown usage",
                "cardinality": "0/1",
                "type": "AN",
                "length": "1/1"
            })
            
            # Check for length errors
            length_error = next((err for err in self.length_errors if err.field_id == field), None)
            has_length_error = length_error is not None
            
            fields.append({
                "field_name": field,
                "name": field_info["name"],
                "status": "Optional",
                "usage": field_info["usage"],
                "cardinality": field_info.get("cardinality", "0/1"),
                "type": field_info.get("type", "AN"),
                "length": field_info.get("length", "1/1"),
                "color": "red" if has_length_error else "yellow",  # Red if length error, yellow otherwise
                "present_in_edi": True,
                "length_error": str(length_error) if length_error else ""
            })
        
        # White: Optional fields missing from EDI
        for field in sorted(self.optional_missing):
            field_info = EDI_810_FIELDS.get(field, {
                "name": "Unknown Field", 
                "usage": "Unknown usage",
                "cardinality": "0/1",
                "type": "AN",
                "length": "1/1"
            })
            fields.append({
                "field_name": field,
                "name": field_info["name"],
                "status": "Optional",
                "usage": field_info["usage"],
                "cardinality": field_info.get("cardinality", "0/1"),
                "type": field_info.get("type", "AN"),
                "length": field_info.get("length", "1/1"),
                "color": "white",
                "present_in_edi": False,
                "length_error": ""
            })
            
        return fields


def validate_field_lengths(edi_field_values: Dict[str, str]) -> List[FieldLengthError]:
    """
    Validate field lengths against EDI 810 specifications - optimized.
    
    Args:
        edi_field_values: Dictionary mapping field IDs to their actual values
        
    Returns:
        List of FieldLengthError objects for fields that don't meet length requirements
    """
    length_errors = []
    
    # Limit validation to prevent performance issues
    if len(edi_field_values) > 100:
        # Only validate mandatory fields for large datasets
        mandatory_fields = {k: v for k, v in edi_field_values.items() 
                          if k in EDI_810_FIELDS and EDI_810_FIELDS[k]["status"] == "M"}
        field_values_to_check = mandatory_fields
    else:
        field_values_to_check = edi_field_values
    
    for field_id, value in field_values_to_check.items():
        if field_id not in EDI_810_FIELDS:
            continue
            
        field_spec = EDI_810_FIELDS[field_id]
        length_spec = field_spec.get("length", "1/1")
        
        # Parse length specification (e.g., "1/22" means min 1, max 22)
        try:
            min_length, max_length = map(int, length_spec.split('/'))
            actual_length = len(value) if value else 0
            
            if actual_length < min_length or actual_length > max_length:
                length_errors.append(FieldLengthError(
                    field_id=field_id,
                    actual_length=actual_length,
                    expected_min=min_length,
                    expected_max=max_length,
                    actual_value=value[:50] if len(value) > 50 else value  # Truncate long values
                ))
        except (ValueError, AttributeError):
            continue
    
    return length_errors


def compare_fields_detailed(present_fields: Iterable[str], requirements: Dict[str, bool], edi_field_values: Dict[str, str] = None) -> FieldComparisonResult:
    """
    Perform detailed comparison between EDI fields and specification requirements.
    
    Args:
        present_fields: List of field IDs present in the EDI file
        requirements: Dictionary mapping field IDs to whether they're required
        edi_field_values: Dictionary mapping field IDs to their actual values (for length validation)
    
    Returns:
        FieldComparisonResult with categorized fields and color coding
    """
    present = set(present_fields)
    result = FieldComparisonResult()
    
    # Validate field lengths if values are provided
    if edi_field_values:
        result.length_errors = validate_field_lengths(edi_field_values)
    
    # Categorize fields based on requirements and presence
    for field, is_required in requirements.items():
        if is_required:  # Mandatory field
            if field in present:
                result.mandatory_present.append(field)
            else:
                result.mandatory_missing.append(field)
        else:  # Optional field
            if field in present:
                result.optional_present.append(field)
            else:
                result.optional_missing.append(field)
    
    # Find additional fields in EDI that are not in requirements
    allowed_fields = set(requirements.keys())
    result.additional_fields = sorted(list(present - allowed_fields))
    
    return result


def compare_fields(present_fields: Iterable[str], requirements: Dict[str, bool]) -> Tuple[List[str], List[str]]:
    """
    Legacy function for backward compatibility.
    
    Returns:
        Tuple of (missing_mandatory, additional_fields)
    """
    present = set(present_fields)
    required = {k for k, v in requirements.items() if v}
    allowed = set(requirements.keys())

    missing_mandatory: List[str] = sorted(list(required - present))
    additional_fields: List[str] = sorted(list(present - allowed))
    return missing_mandatory, additional_fields


def get_mandatory_fields() -> List[str]:
    """Get list of all mandatory EDI 810 fields."""
    return [field for field, info in EDI_810_FIELDS.items() if info["status"] == "M"]


def get_optional_fields() -> List[str]:
    """Get list of all optional EDI 810 fields."""
    return [field for field, info in EDI_810_FIELDS.items() if info["status"] == "O"]


def get_segment_summary(present_fields: Iterable[str], requirements: Dict[str, bool]) -> List[Dict[str, str]]:
    """
    Generate segment-based summary in the format shown in EDI 855 validator.
    
    Returns:
        List of segment dictionaries with columns: segment_tag, x12_requirement, 
        company_usage, min_usage, max_usage, present_in_edi, status
    """
    present = set(present_fields)
    
    # Define EDI 810 segments with their usage patterns
    segments = {
        "ISA": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "GS": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"}, 
        "ST": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "BIG": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "REF": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "12"},
        "N1": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "1", "max_usage": "200"},
        "N2": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "2"},
        "N3": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "2"},
        "N4": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1"},
        "PER": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "3"},
        "ITD": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "10"},
        "DTM": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "10"},
        "FOB": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1"},
        "CUR": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1"},
        "IT1": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "999999"},
        "PID": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "200"},
        "SAC": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "25"},
        "TXI": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "10"},
        "SLN": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1000"},
        "TDS": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "ISS": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1"},
        "CTT": {"x12_requirement": "optional", "company_usage": "used", "min_usage": "0", "max_usage": "1"},
        "SE": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "GE": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"},
        "IEA": {"x12_requirement": "mandatory", "company_usage": "must_use", "min_usage": "1", "max_usage": "1"}
    }
    
    segment_summary = []
    
    for segment_tag, segment_info in segments.items():
        # Check if any fields from this segment are present
        segment_fields = [field for field in present if field.startswith(segment_tag)]
        is_present = len(segment_fields) > 0
        
        # Determine status
        if segment_info["x12_requirement"] == "mandatory":
            status = "✓ Present" if is_present else "✗ Missing" 
        else:
            status = "✓ Present" if is_present else "✗ Missing"
            
        segment_summary.append({
            "segment_tag": segment_tag,
            "x12_requirement": segment_info["x12_requirement"],
            "company_usage": segment_info["company_usage"], 
            "min_usage": segment_info["min_usage"],
            "max_usage": segment_info["max_usage"],
            "present_in_edi": "Yes" if is_present else "No",
            "status": status
        })
    
    return segment_summary


