from typing import Dict, Tuple, Set, List
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
import re
import io


MANDATORY_HINTS = {"M", "Mandatory", "Required"}
OPTIONAL_HINTS = {"O", "Optional"}

# Define comprehensive EDI 810 field structure with cardinality, type, and field length
EDI_810_FIELDS = {
    # Interchange Control Header
    "ISA01": {"name": "Authorization Information Qualifier", "status": "M", "usage": "Code to identify the type of information in the Authorization Information", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "ISA02": {"name": "Authorization Information", "status": "M", "usage": "Information used for additional identification or authorization of the interchange sender or the data in the interchange", "cardinality": "1/1", "type": "AN", "length": "10/10"},
    "ISA03": {"name": "Security Information Qualifier", "status": "M", "usage": "Code to identify the type of information in the Security Information", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "ISA04": {"name": "Security Information", "status": "M", "usage": "Information used for identifying the security information about the interchange sender or the data in the interchange", "cardinality": "1/1", "type": "AN", "length": "10/10"},
    "ISA05": {"name": "Interchange ID Qualifier", "status": "M", "usage": "Qualifier to designate the system/method of code structure used to designate the sender or receiver ID element being qualified", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "ISA06": {"name": "Interchange Sender ID", "status": "M", "usage": "Identification code published by the sender for other parties to use as the receiver ID to route data to them", "cardinality": "1/1", "type": "AN", "length": "15/15"},
    "ISA07": {"name": "Interchange ID Qualifier", "status": "M", "usage": "Qualifier to designate the system/method of code structure used to designate the sender or receiver ID element being qualified", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "ISA08": {"name": "Interchange Receiver ID", "status": "M", "usage": "Identification code published by the receiver of the data", "cardinality": "1/1", "type": "AN", "length": "15/15"},
    "ISA09": {"name": "Interchange Date", "status": "M", "usage": "Date of the interchange", "cardinality": "1/1", "type": "DT", "length": "6/6"},
    "ISA10": {"name": "Interchange Time", "status": "M", "usage": "Time of the interchange", "cardinality": "1/1", "type": "TM", "length": "4/4"},
    "ISA11": {"name": "Interchange Control Standards Identifier", "status": "M", "usage": "Code to identify the agency responsible for the control standard used by the message that is enclosed by the interchange header and trailer", "cardinality": "1/1", "type": "ID", "length": "1/1"},
    "ISA12": {"name": "Interchange Control Version Number", "status": "M", "usage": "This version number covers the interchange control segments", "cardinality": "1/1", "type": "ID", "length": "5/5"},
    "ISA13": {"name": "Interchange Control Number", "status": "M", "usage": "A control number assigned by the interchange sender", "cardinality": "1/1", "type": "N0", "length": "9/9"},
    "ISA14": {"name": "Acknowledgment Requested", "status": "M", "usage": "Code sent by the sender to request an interchange acknowledgment (TA1)", "cardinality": "1/1", "type": "ID", "length": "1/1"},
    "ISA15": {"name": "Usage Indicator", "status": "M", "usage": "Code to indicate whether data enclosed by this interchange envelope is test, production or information", "cardinality": "1/1", "type": "ID", "length": "1/1"},
    "ISA16": {"name": "Component Element Separator", "status": "M", "usage": "Type is not applicable; the component element separator is a delimiter and not a data element", "cardinality": "1/1", "type": "AN", "length": "1/1"},
    
    # Functional Group Header
    "GS01": {"name": "Functional Identifier Code", "status": "M", "usage": "Code identifying a group of application related transaction sets", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "GS02": {"name": "Application Sender's Code", "status": "M", "usage": "Code identifying party sending transmission; codes agreed to by trading partners", "cardinality": "1/1", "type": "AN", "length": "2/15"},
    "GS03": {"name": "Application Receiver's Code", "status": "M", "usage": "Code identifying party receiving transmission; codes agreed to by trading partners", "cardinality": "1/1", "type": "AN", "length": "2/15"},
    "GS04": {"name": "Date", "status": "M", "usage": "Date expressed as CCYYMMDD", "cardinality": "1/1", "type": "DT", "length": "8/8"},
    "GS05": {"name": "Time", "status": "M", "usage": "Time expressed in 24-hour clock time as follows: HHMM, or HHMMSS, or HHMMSSD, or HHMMSSDD", "cardinality": "1/1", "type": "TM", "length": "4/8"},
    "GS06": {"name": "Group Control Number", "status": "M", "usage": "Assigned number originated and maintained by the sender", "cardinality": "1/1", "type": "N0", "length": "1/9"},
    "GS07": {"name": "Responsible Agency Code", "status": "M", "usage": "Code used in conjunction with Data Element 480 to identify the issuer of the standard", "cardinality": "1/1", "type": "ID", "length": "1/2"},
    "GS08": {"name": "Version / Release / Industry Identifier Code", "status": "M", "usage": "Code indicating the version, release, subrelease, and industry identifier of the EDI standard being used", "cardinality": "1/1", "type": "AN", "length": "1/12"},
    
    # Transaction Set Header
    "ST01": {"name": "Transaction Set Identifier Code", "status": "M", "usage": "Code uniquely identifying a Transaction Set (must be 810 for Invoice)", "cardinality": "1/1", "type": "ID", "length": "3/3"},
    "ST02": {"name": "Transaction Set Control Number", "status": "M", "usage": "Identifying control number that must be unique within the transaction set functional group assigned by the originator for a transaction set", "cardinality": "1/1", "type": "AN", "length": "4/9"},
    
    # Invoice Date, Invoice Number, PO Date, PO Number
    "BIG01": {"name": "Invoice Date", "status": "M", "usage": "Date expressed as CCYYMMDD", "cardinality": "1/1", "type": "DT", "length": "8/8"},
    "BIG02": {"name": "Invoice Number", "status": "M", "usage": "Identifying number assigned by issuer", "cardinality": "1/1", "type": "AN", "length": "1/22"},
    "BIG03": {"name": "Purchase Order Date", "status": "O", "usage": "Date expressed as CCYYMMDD", "cardinality": "0/1", "type": "DT", "length": "8/8"},
    "BIG04": {"name": "Purchase Order Number", "status": "O", "usage": "Identifying number for Purchase Order assigned by the orderer/purchaser", "cardinality": "0/1", "type": "AN", "length": "1/22"},
    "BIG05": {"name": "Release Number", "status": "O", "usage": "Number identifying a release against a Purchase Order previously placed by the parties involved in the transaction", "cardinality": "0/1", "type": "AN", "length": "1/30"},
    "BIG06": {"name": "Change Order Sequence Number", "status": "O", "usage": "Number assigned by the orderer identifying a specific change or revision to a previously transmitted transaction set", "cardinality": "0/1", "type": "AN", "length": "1/8"},
    "BIG07": {"name": "Transaction Type Code", "status": "O", "usage": "Code specifying the type of transaction", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    
    # Reference Identification
    "REF01": {"name": "Reference Identification Qualifier", "status": "O", "usage": "Code qualifying the Reference Identification", "cardinality": "0/1", "type": "ID", "length": "2/3"},
    "REF02": {"name": "Reference Identification", "status": "O", "usage": "Reference information as defined for a particular Transaction Set or as specified by the Reference Identification Qualifier", "cardinality": "0/1", "type": "AN", "length": "1/50"},
    "REF03": {"name": "Description", "status": "O", "usage": "A free-form description to clarify the related data elements and their content", "cardinality": "0/1", "type": "AN", "length": "1/80"},
    
    # Name segments
    "N101": {"name": "Entity Identifier Code", "status": "M", "usage": "Code identifying an organizational entity, a physical location, property or an individual", "cardinality": "1/1", "type": "ID", "length": "2/3"},
    "N102": {"name": "Name", "status": "O", "usage": "Free-form name", "cardinality": "0/1", "type": "AN", "length": "1/60"},
    "N103": {"name": "Identification Code Qualifier", "status": "O", "usage": "Code designating the system/method of code structure used for Identification Code (67)", "cardinality": "0/1", "type": "ID", "length": "1/2"},
    "N104": {"name": "Identification Code", "status": "O", "usage": "Code identifying a party or other code", "cardinality": "0/1", "type": "AN", "length": "2/80"},
    
    # Additional Name Information
    "N201": {"name": "Name", "status": "M", "usage": "Free-form name", "cardinality": "1/1", "type": "AN", "length": "1/60"},
    "N202": {"name": "Name", "status": "O", "usage": "Free-form name", "cardinality": "0/1", "type": "AN", "length": "1/60"},
    
    # Address Information
    "N301": {"name": "Address Information", "status": "M", "usage": "Address information", "cardinality": "1/1", "type": "AN", "length": "1/55"},
    "N302": {"name": "Address Information", "status": "O", "usage": "Address information", "cardinality": "0/1", "type": "AN", "length": "1/55"},
    
    # Geographic Location
    "N401": {"name": "City Name", "status": "O", "usage": "Free-form text for city name", "cardinality": "0/1", "type": "AN", "length": "2/30"},
    "N402": {"name": "State or Province Code", "status": "O", "usage": "Code (Standard State/Province) as defined by appropriate government agency", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    "N403": {"name": "Postal Code", "status": "O", "usage": "Code defining international postal zone code excluding punctuation and blanks", "cardinality": "0/1", "type": "ID", "length": "3/15"},
    "N404": {"name": "Country Code", "status": "O", "usage": "Code identifying the country", "cardinality": "0/1", "type": "ID", "length": "2/3"},
    
    # Administrative Contact Information
    "PER01": {"name": "Contact Function Code", "status": "M", "usage": "Administrative contact - Contact function"},
    "PER02": {"name": "Name", "status": "O", "usage": "Administrative contact - Contact name"},
    "PER03": {"name": "Communication Number Qualifier", "status": "O", "usage": "Administrative contact - Communication qualifier"},
    "PER04": {"name": "Communication Number", "status": "O", "usage": "Administrative contact - Communication number"},
    
    # Terms of Sale/Deferred Terms of Sale
    "ITD01": {"name": "Terms Type Code", "status": "O", "usage": "Terms of sale - Terms type"},
    "ITD02": {"name": "Terms Basis Date Code", "status": "O", "usage": "Terms of sale - Terms basis date"},
    "ITD03": {"name": "Terms Discount Percent", "status": "O", "usage": "Terms of sale - Discount percent"},
    "ITD04": {"name": "Terms Discount Due Date", "status": "O", "usage": "Terms of sale - Discount due date"},
    "ITD05": {"name": "Terms Discount Days Due", "status": "O", "usage": "Terms of sale - Discount days"},
    "ITD06": {"name": "Terms Net Due Date", "status": "O", "usage": "Terms of sale - Net due date"},
    "ITD07": {"name": "Terms Net Days", "status": "O", "usage": "Terms of sale - Net days"},
    
    # Date/Time Reference
    "DTM01": {"name": "Date/Time Qualifier", "status": "M", "usage": "Date/Time reference - Date qualifier"},
    "DTM02": {"name": "Date", "status": "O", "usage": "Date/Time reference - Date"},
    "DTM03": {"name": "Time", "status": "O", "usage": "Date/Time reference - Time"},
    
    # Freight On Board Information
    "FOB01": {"name": "Shipment Method of Payment", "status": "M", "usage": "FOB information - Payment method"},
    "FOB02": {"name": "Location Qualifier", "status": "O", "usage": "FOB information - Location qualifier"},
    "FOB03": {"name": "Description", "status": "O", "usage": "FOB information - Description"},
    
    # Currency Code
    "CUR01": {"name": "Entity Identifier Code", "status": "M", "usage": "Currency - Entity identifier"},
    "CUR02": {"name": "Currency Code", "status": "M", "usage": "Currency - Currency code"},
    
    # Line Item
    "IT101": {"name": "Assigned Identification", "status": "O", "usage": "Alphanumeric characters assigned for differentiation within a transaction set", "cardinality": "0/1", "type": "AN", "length": "1/20"},
    "IT102": {"name": "Quantity Invoiced", "status": "M", "usage": "Number of units invoiced (supplier units)", "cardinality": "1/1", "type": "R", "length": "1/15"},
    "IT103": {"name": "Unit or Basis for Measurement Code", "status": "M", "usage": "Code specifying the units in which a value is being expressed, or manner in which a measurement has been taken", "cardinality": "1/1", "type": "ID", "length": "2/2"},
    "IT104": {"name": "Unit Price", "status": "M", "usage": "Price per unit of product, service, commodity, etc.", "cardinality": "1/1", "type": "R", "length": "1/17"},
    "IT105": {"name": "Basis of Unit Price Code", "status": "O", "usage": "Code identifying the type of unit price for an item", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    "IT106": {"name": "Product/Service ID Qualifier", "status": "O", "usage": "Code identifying the type/source of the descriptive number used in Product/Service ID (234)", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    "IT107": {"name": "Product/Service ID", "status": "O", "usage": "Identifying number for a product or service", "cardinality": "0/1", "type": "AN", "length": "1/48"},
    
    # Product/Item Description
    "PID01": {"name": "Item Description Type", "status": "M", "usage": "Product description - Description type"},
    "PID02": {"name": "Product/Process Characteristic Code", "status": "O", "usage": "Product description - Characteristic code"},
    "PID03": {"name": "Agency Qualifier Code", "status": "O", "usage": "Product description - Agency qualifier"},
    "PID04": {"name": "Product Description Code", "status": "O", "usage": "Product description - Description code"},
    "PID05": {"name": "Description", "status": "O", "usage": "Product description - Description text"},
    
    # Service, Promotion, Allowance, or Charge Information
    "SAC01": {"name": "Allowance or Charge Indicator", "status": "M", "usage": "Service/Allowance/Charge - Allowance/Charge indicator"},
    "SAC02": {"name": "Service, Promotion, Allowance, or Charge Code", "status": "O", "usage": "Service/Allowance/Charge - Service code"},
    "SAC03": {"name": "Agency Qualifier Code", "status": "O", "usage": "Service/Allowance/Charge - Agency qualifier"},
    "SAC04": {"name": "Agency Service, Promotion, Allowance, or Charge Code", "status": "O", "usage": "Service/Allowance/Charge - Agency code"},
    "SAC05": {"name": "Amount", "status": "O", "usage": "Service/Allowance/Charge - Amount"},
    
    # Tax Information
    "TXI01": {"name": "Tax Type Code", "status": "M", "usage": "Tax information - Tax type"},
    "TXI02": {"name": "Monetary Amount", "status": "O", "usage": "Tax information - Tax amount"},
    "TXI03": {"name": "Percent", "status": "O", "usage": "Tax information - Tax percent"},
    "TXI04": {"name": "Tax Jurisdiction Code Qualifier", "status": "O", "usage": "Tax information - Jurisdiction qualifier"},
    "TXI05": {"name": "Tax Jurisdiction Code", "status": "O", "usage": "Tax information - Jurisdiction code"},
    
    # Sub-line Item
    "SLN01": {"name": "Assigned Identification", "status": "M", "usage": "Sub-line item - Sub-line number"},
    "SLN02": {"name": "Assigned Identification", "status": "O", "usage": "Sub-line item - Parent line number"},
    "SLN03": {"name": "Relationship Code", "status": "M", "usage": "Sub-line item - Relationship code"},
    "SLN04": {"name": "Quantity", "status": "O", "usage": "Sub-line item - Quantity"},
    "SLN05": {"name": "Unit or Basis for Measurement Code", "status": "O", "usage": "Sub-line item - Unit of measure"},
    
    # Total Invoice Amount
    "TDS01": {"name": "Amount", "status": "M", "usage": "Monetary amount", "cardinality": "1/1", "type": "N2", "length": "1/18"},
    
    # Invoice Shipment Summary
    "ISS01": {"name": "Number of Units Shipped", "status": "O", "usage": "Numeric value of units shipped in manufacturer's shipping units for a line item or transaction set", "cardinality": "0/1", "type": "R", "length": "1/10"},
    "ISS02": {"name": "Unit or Basis for Measurement Code", "status": "O", "usage": "Code specifying the units in which a value is being expressed, or manner in which a measurement has been taken", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    "ISS03": {"name": "Weight", "status": "O", "usage": "Numeric value of weight", "cardinality": "0/1", "type": "R", "length": "1/10"},
    "ISS04": {"name": "Unit or Basis for Measurement Code", "status": "O", "usage": "Code specifying the units in which a value is being expressed, or manner in which a measurement has been taken", "cardinality": "0/1", "type": "ID", "length": "2/2"},
    
    # Transaction Totals
    "CTT01": {"name": "Number of Line Items", "status": "M", "usage": "Total number of line items in the transaction set", "cardinality": "1/1", "type": "N0", "length": "1/6"},
    "CTT02": {"name": "Hash Total", "status": "O", "usage": "Sum of values of the specified data element. All values in the data element will be summed without regard to decimal points", "cardinality": "0/1", "type": "R", "length": "1/10"},
    
    # Transaction Set Trailer
    "SE01": {"name": "Number of Included Segments", "status": "M", "usage": "Total number of segments included in a transaction set including ST and SE segments", "cardinality": "1/1", "type": "N0", "length": "1/10"},
    "SE02": {"name": "Transaction Set Control Number", "status": "M", "usage": "Identifying control number that must be unique within the transaction set functional group assigned by the originator for a transaction set", "cardinality": "1/1", "type": "AN", "length": "4/9"},
    
    # Functional Group Trailer
    "GE01": {"name": "Number of Transaction Sets Included", "status": "M", "usage": "A count of the number of transaction sets included in the functional group", "cardinality": "1/1", "type": "N0", "length": "1/6"},
    "GE02": {"name": "Group Control Number", "status": "M", "usage": "Assigned number originated and maintained by the sender", "cardinality": "1/1", "type": "N0", "length": "1/9"},
    
    # Interchange Control Trailer
    "IEA01": {"name": "Number of Included Functional Groups", "status": "M", "usage": "A count of the number of functional groups included in an interchange", "cardinality": "1/1", "type": "N0", "length": "1/5"},
    "IEA02": {"name": "Interchange Control Number", "status": "M", "usage": "A control number assigned by the interchange sender", "cardinality": "1/1", "type": "N0", "length": "9/9"}
}


def detect_file_type(file_bytes: bytes, filename: str = "") -> str:
    """Detect the file type based on content and filename."""
    # Check file signature (magic numbers)
    if file_bytes.startswith(b'%PDF'):
        return 'pdf'
    elif file_bytes.startswith(b'\xd0\xcf\x11\xe0'):  # MS Office compound document
        if filename.lower().endswith('.doc'):
            return 'doc'
        elif filename.lower().endswith('.docx'):
            return 'docx'
    elif file_bytes.startswith(b'PK\x03\x04'):  # ZIP-based format
        if filename.lower().endswith('.docx'):
            return 'docx'
    
    # Check filename extension as fallback
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ['pdf', 'doc', 'docx', 'txt']:
            return ext
    
    # Default to text if we can decode it
    try:
        file_bytes.decode('utf-8')
        return 'txt'
    except UnicodeDecodeError:
        try:
            file_bytes.decode('latin-1')
            return 'txt'
        except UnicodeDecodeError:
            return 'unknown'


def extract_text_from_document(file_bytes: bytes, filename: str = "") -> List[str]:
    """Extract text from various document types line by line - optimized version."""
    lines = []
    file_type = detect_file_type(file_bytes, filename)
    
    # Limit file size for performance (max 5MB)
    if len(file_bytes) > 5 * 1024 * 1024:
        file_bytes = file_bytes[:5 * 1024 * 1024]
    
    try:
        if file_type == 'pdf':
            # Fast path: try raw text extraction first
            try:
                raw_text = file_bytes.decode(errors="ignore")
                if "BIG01" in raw_text or "ISA01" in raw_text:  # Quick check for EDI content
                    lines = raw_text.splitlines()
                else:
                    # Use pdfminer only if needed
                    text = extract_text(io.BytesIO(file_bytes))
                    if text:
                        lines = text.splitlines()
            except Exception:
                # Fallback to pdfminer
                text = extract_text(io.BytesIO(file_bytes))
                if text:
                    lines = text.splitlines()
        
        elif file_type == 'txt':
            # Handle plain text files (fastest)
            try:
                text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = file_bytes.decode('latin-1', errors="ignore")
            lines = text.splitlines()
        
        elif file_type == 'docx':
            # Simplified DOCX handling
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
                    doc_xml = docx_zip.read('word/document.xml')
                    # Simple text extraction without full parsing
                    text_content = doc_xml.decode(errors="ignore")
                    # Extract text between tags
                    import re
                    text_matches = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', text_content)
                    lines = [match.strip() for match in text_matches if match.strip()]
            except Exception:
                # Fallback to raw text
                text = file_bytes.decode(errors="ignore")
                lines = text.splitlines()
        
        else:
            # Default: raw text extraction
            text = file_bytes.decode(errors="ignore")
            lines = text.splitlines()
            
    except Exception:
        # Final fallback
        try:
            text = file_bytes.decode(errors="ignore")
            lines = text.splitlines()
        except Exception:
            lines = []
    
    # Limit number of lines for performance
    return [line.strip() for line in lines[:1000] if line.strip()]


def parse_document_spec_to_xml(file_bytes: bytes, filename: str = "") -> Tuple[str, Dict[str, bool], Set[str], Dict[str, str]]:
    """Extract field list from any document type using high-level line-by-line parsing.

    This function parses documents (PDF, DOC, DOCX, TXT) line by line to identify 
    EDI 810 fields and their mandatory/optional status.

    Returns:
        xml: XML representation of the parsed fields
        requirements: map of field tag -> is_required
        all_fields: set of field tags found
    """
    requirements: Dict[str, bool] = {}
    status_map: Dict[str, str] = {}
    found_fields: Set[str] = set()
    
    # Extract text line by line from any document type
    lines = extract_text_from_document(file_bytes, filename)
    
    def _infer_status_from_line(line_upper: str) -> str:
        """Infer status letter (M/O/X) from a line of spec text (case-insensitive)."""
        # Try common patterns like ' M ', '(M)', 'Status: M', '|M|', etc.
        # Priority: M > O > X when multiple are present (rare)
        if any(p in line_upper for p in ["(M)", " M ", " STATUS M", "\tM\t", "|M|", " M,", " M:"]):
            return "M"
        if any(p in line_upper for p in ["(O)", " O ", " STATUS O", "\tO\t", "|O|", " O,", " O:"]):
            return "O"
        if any(p in line_upper for p in ["(X)", " X ", " STATUS X", "\tX\t", "|X|", " X,", " X:"]):
            return "X"
        # Fallback: single-letter at end of tokenized columns
        tokens = [t.strip("|,;:- ") for t in line_upper.split()]
        for t in tokens[-3:]:
            if t in {"M", "O", "X"}:
                return t
        return ""

    def analyze_line(line: str):
        """Analyze a single line for EDI field patterns - optimized."""
        # Skip very long lines to avoid performance issues
        if len(line) > 500:
            return
            
        line_upper = line.upper()
        
        # Quick check if line contains EDI patterns (expanded)
        if not any(seg in line_upper for seg in [
            'ISA','GS','ST','BIG','REF','N1','N2','N3','N4','PER','ITD','DTM','FOB','CUR',
            'IT1','PID','SAC','TXI','SLN','TDS','ISS','CTT','SE','GE','IEA']):
            return
        
        # Look for EDI field patterns (optimized regex)
        field_matches = re.findall(r"\b([A-Z]{2,4})(\d{1,2})\b", line)
        
        for seg, num in field_matches:
            tag = f"{seg}{int(num):02d}"
            
            # Only process known EDI fields to avoid unnecessary processing
            if tag not in EDI_810_FIELDS:
                continue
                
            found_fields.add(tag)
            # Determine requirement using spec line if available, else fallback to predefined
            status_letter = _infer_status_from_line(line_upper)
            if status_letter:
                # Treat X (not used) as optional for comparison purposes
                requirements[tag] = (status_letter == 'M')
                status_map[tag] = status_letter
            else:
                # Use predefined field status for better performance
                requirements[tag] = EDI_810_FIELDS[tag]["status"] == "M"
                # Map to M/O from predefined spec
                predefined = EDI_810_FIELDS[tag]["status"]
                status_map[tag] = 'M' if predefined.upper() == 'M' else 'O'

    # Process each line
    for line in lines:
        if line:
            analyze_line(line)
    
    # If no fields found, use a minimal predefined header structure for resilience
    if not found_fields:
        header_fields = [
            "ISA01","ISA02","ISA03","ISA04","ISA05","ISA06","ISA07","ISA08",
            "ISA09","ISA10","ISA11","ISA12","ISA13","ISA14","ISA15","ISA16",
            "GS01","GS02","GS03","GS04","GS05","GS06","GS07","GS08",
            "ST01","ST02","BIG01","BIG02","CTT01","SE01","SE02"
        ]
        
        for field in header_fields:
            if field in EDI_810_FIELDS:
                found_fields.add(field)
                requirements[field] = EDI_810_FIELDS[field]["status"] == "M"
                status_map[field] = 'M' if EDI_810_FIELDS[field]["status"].upper() == 'M' else 'O'
    
    # Detect document type for XML metadata
    doc_type = detect_file_type(file_bytes, filename)
    
    # Build XML representation
    xml_parts = [f"<Document type=\"{doc_type}\">"]
    xml_parts.append(f"  <SourceFile>{filename or 'Unknown'}</SourceFile>")
    xml_parts.append("  <ParsedFields>")
    
    for tag in sorted(found_fields):
        field_info = EDI_810_FIELDS.get(tag, {"name": "Unknown Field", "usage": "Unknown usage"})
        status = "Mandatory" if requirements.get(tag, False) else "Optional"
        
        xml_parts.append(f"    <Field>")
        xml_parts.append(f"      <Tag>{tag}</Tag>")
        xml_parts.append(f"      <Name>{field_info['name']}</Name>")
        xml_parts.append(f"      <Status>{status}</Status>")
        xml_parts.append(f"      <Usage>{field_info['usage']}</Usage>")
        xml_parts.append(f"      <Required>{'true' if requirements.get(tag, False) else 'false'}</Required>")
        xml_parts.append(f"    </Field>")
    
    xml_parts.append("  </ParsedFields>")
    xml_parts.append("</Document>")

    return "\n".join(xml_parts), requirements, found_fields, status_map


# Keep the old function for backward compatibility
def parse_pdf_spec_to_xml(pdf_bytes: bytes) -> Tuple[str, Dict[str, bool], Set[str]]:
    """Legacy function for PDF parsing - redirects to new document parser."""
    xml, requirements, found, _status = parse_document_spec_to_xml(pdf_bytes, "document.pdf")
    return xml, requirements, found


