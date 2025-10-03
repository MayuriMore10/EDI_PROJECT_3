from typing import Tuple, Set, Dict


def _detect_separators(edi_text: str) -> Tuple[str, str]:
    # Default X12: element '*', segment '~'
    element = '*'
    segment = '~'
    # Try to infer from ISA if present
    if edi_text.startswith('ISA') and len(edi_text) > 105:
        element = edi_text[3]
        segment = edi_text[105]
    return element, segment


def validate_edi_810(edi_text: str) -> Tuple[bool, str]:
    """Validate that the EDI file is a valid 810 invoice.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    element_sep, segment_sep = _detect_separators(edi_text)
    raw_segments = [s for s in edi_text.strip().split(segment_sep) if s]
    
    # Check for required segments
    has_isa = False
    has_gs = False
    has_st_810 = False
    
    for seg in raw_segments:
        parts = seg.split(element_sep)
        if not parts:
            continue
        seg_id = parts[0].strip()
        
        if seg_id == 'ISA':
            has_isa = True
        elif seg_id == 'GS':
            has_gs = True
        elif seg_id == 'ST':
            # Check if it's specifically an 810 transaction
            if len(parts) > 1 and parts[1].strip() == '810':
                has_st_810 = True
            elif len(parts) > 1 and parts[1].strip() != '810':
                return False, f"Only EDI 810 (Invoice) files are allowed. Found transaction type: {parts[1].strip()}"
    
    if not has_isa:
        return False, "Invalid EDI file: Missing ISA (Interchange Control Header) segment"
    if not has_gs:
        return False, "Invalid EDI file: Missing GS (Functional Group Header) segment"
    if not has_st_810:
        return False, "Only EDI 810 (Invoice) files are allowed. Please upload a valid EDI 810 file."
    
    return True, ""


def parse_edi_to_xml(edi_text: str) -> Tuple[str, Set[str], bool, Dict[str, str]]:
    """Parse a simple X12 EDI text into a minimal XML and collect field tags.

    Returns:
        xml: Minimal XML string representation
        present_fields: Set of tags like 'BIG01', 'BIG02', 'REF01', etc.
        is_810: Strict check whether it's a valid 810 invoice
        field_values: Dictionary mapping field IDs to their actual values
    """
    # First validate that it's a proper EDI 810 file
    is_valid_810, error_msg = validate_edi_810(edi_text)
    if not is_valid_810:
        # Return empty results with error indication
        return f"<Error>{error_msg}</Error>", set(), False, {}
    
    element_sep, segment_sep = _detect_separators(edi_text)
    raw_segments = [s for s in edi_text.strip().split(segment_sep) if s]
    present_fields: Set[str] = set()
    field_values: Dict[str, str] = {}

    xml_parts = ["<EDI_810>"]
    xml_parts.append("  <TransactionType>810 - Invoice</TransactionType>")
    
    for seg in raw_segments:
        parts = seg.split(element_sep)
        if not parts:
            continue
        seg_id = parts[0].strip()
        
        # Build field tags seg_id + 2-digit index and store values
        for idx, value in enumerate(parts[1:], start=1):
            if value.strip():  # Only count non-empty values
                tag = f"{seg_id}{idx:02d}"
                present_fields.add(tag)
                field_values[tag] = value.strip()  # Store actual field value for validation
        
        # Enhanced XML representation with segment names
        segment_names = {
            'ISA': 'Interchange_Control_Header',
            'GS': 'Functional_Group_Header', 
            'ST': 'Transaction_Set_Header',
            'BIG': 'Invoice_Information',
            'REF': 'Reference_Identification',
            'N1': 'Name',
            'N2': 'Additional_Name_Information',
            'N3': 'Address_Information',
            'N4': 'Geographic_Location',
            'PER': 'Administrative_Contact',
            'ITD': 'Terms_of_Sale',
            'DTM': 'Date_Time_Reference',
            'FOB': 'FOB_Information',
            'CUR': 'Currency_Code',
            'IT1': 'Line_Item',
            'PID': 'Product_Description',
            'SAC': 'Service_Allowance_Charge',
            'TXI': 'Tax_Information',
            'SLN': 'Sub_Line_Item',
            'TDS': 'Total_Invoice_Amount',
            'ISS': 'Invoice_Shipment_Summary',
            'CTT': 'Transaction_Totals',
            'SE': 'Transaction_Set_Trailer',
            'GE': 'Functional_Group_Trailer',
            'IEA': 'Interchange_Control_Trailer'
        }
        
        segment_name = segment_names.get(seg_id, seg_id)
        xml_parts.append(f"  <{segment_name} segment_id=\"{seg_id}\">")
        
        for idx, value in enumerate(parts[1:], start=1):
            safe_val = (value or '').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            xml_parts.append(f"    <Element_{idx:02d}>{safe_val}</Element_{idx:02d}>")
        xml_parts.append(f"  </{segment_name}>")
    
    xml_parts.append("</EDI_810>")

    return "\n".join(xml_parts), present_fields, True, field_values


