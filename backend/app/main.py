from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
from .services.edi_parser import parse_edi_to_xml
from .services.spec_parser import parse_pdf_spec_to_xml, parse_document_spec_to_xml
from .services.compare import compare_fields, compare_fields_detailed, get_mandatory_fields, get_optional_fields, get_segment_summary
from .services.ai_summary import ComplianceAnalyzer, generate_executive_summary


app = FastAPI(title="EDI 810 Validator API")

# Resolve project and frontend directories regardless of CWD
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mounts will be added after API routes (see bottom)


class FieldInfo(BaseModel):
    field_name: str
    name: str
    status: str
    usage: str
    cardinality: str
    type: str
    length: str
    color: str
    present_in_edi: bool
    length_error: str

class SegmentInfo(BaseModel):
    segment_tag: str
    x12_requirement: str
    company_usage: str
    min_usage: str
    max_usage: str
    present_in_edi: str
    status: str

class CompareResult(BaseModel):
    is_810: bool
    message: str
    missing_mandatory: list[str]
    additional_fields: list[str]
    present_fields: list[str]
    mandatory_fields: list[str]
    optional_fields: list[str]
    detailed_fields: list[FieldInfo]
    segment_summary: list[SegmentInfo]
    executive_summary: str | None = None
    analysis: Dict[str, Any] | None = None
    key_fields: Dict[str, Dict[str, str]] | None = None
    edi_present_status: list[Dict[str, str]] | None = None



@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


@app.post("/api/parse/edi")
async def parse_edi(file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode(errors="ignore")
        xml, fields, is_810, field_values = parse_edi_to_xml(content)
        if not is_810:
            raise HTTPException(status_code=400, detail="Please upload an EDI 810 sample invoice.")
        return {
            "xml": xml, 
            "fields": sorted(list(fields)), 
            "is_810": is_810,
            "field_values": field_values
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing EDI file: {str(e)}")


@app.post("/api/parse/spec")
async def parse_spec(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Use the new dynamic document parser
        xml, requirements, all_fields, status_map = parse_document_spec_to_xml(file_bytes, file.filename or "")
        
        return {
            "xml": xml, 
            "requirements": requirements, 
            "fields": sorted(list(all_fields)),
            "status_map": status_map,
            "filename": file.filename,
            "file_type": file.content_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing specification file: {str(e)}")


class CompareRequest(BaseModel):
    edi_xml: str
    spec_xml: str
    edi_fields: list[str]
    spec_requirements: dict[str, bool]
    edi_field_values: dict[str, str] = {}
    spec_status_map: dict[str, str] | None = None


@app.post("/api/compare", response_model=CompareResult)
async def compare(req: CompareRequest):
    try:
        # Merge spec requirements with all fields present in EDI so they are shown in summary
        merged_requirements: Dict[str, bool] = dict(req.spec_requirements or {})
        for f in req.edi_fields:
            if f not in merged_requirements:
                merged_requirements[f] = False  # treat as optional if not defined in spec

        # Perform detailed comparison with field length validation
        detailed_result = compare_fields_detailed(
            req.edi_fields, 
            merged_requirements, 
            req.edi_field_values
        )
        
        # Legacy comparison for backward compatibility
        missing, additional = compare_fields(req.edi_fields, merged_requirements)
        
        # Check if it's a valid 810 (ST01 should be present and contain 810)
        is_810 = "ST01" in req.edi_fields
        
        mandatory_fields = sorted([k for k, v in merged_requirements.items() if v])
        optional_fields = sorted([k for k, v in merged_requirements.items() if not v])
        
        # Convert detailed result to FieldInfo objects and decorate usage with status (M/O/X)
        status_map = req.spec_status_map or {}
        def decorate_usage(field_code: str, base_usage: str, present: bool) -> str:
            letter = (status_map.get(field_code) or '').upper()
            if letter == 'M':
                prefix = 'Must Use'
            elif letter == 'X':
                prefix = 'Conditional' + (' (present)' if present else '')
            elif letter == 'O':
                prefix = 'Optional'
            else:
                prefix = ''
            return f"{prefix} — {base_usage}" if prefix else base_usage

        detailed_fields_list = []
        for field_data in detailed_result.get_all_fields_with_status():
            code = field_data.get("field_name")
            new_data = dict(field_data)
            new_data["usage"] = decorate_usage(code, field_data.get("usage", ""), bool(field_data.get("present_in_edi")))
            detailed_fields_list.append(FieldInfo(**new_data))
        
        # Generate segment summary
        segment_data = get_segment_summary(req.edi_fields, merged_requirements)
        segment_summary = [SegmentInfo(**seg_data) for seg_data in segment_data]
        
        # AI compliance analysis and executive summary
        analyzer = ComplianceAnalyzer()
        analysis = analyzer.generate_comprehensive_summary(
            comparison_result=detailed_result,
            edi_fields=req.edi_fields,
            spec_requirements=merged_requirements,
            edi_field_values=req.edi_field_values or {}
        )
        exec_summary = generate_executive_summary(analysis)

        # Extract key fields grouped by segment for summary panel
        def extract_key_fields(values: Dict[str, str]) -> Dict[str, Dict[str, str]]:
            keys_by_segment: Dict[str, list[str]] = {
                "GS": ["GS01", "GS02", "GS03", "GS04", "GS05", "GS06", "GS07", "GS08"],
                "ST": ["ST01", "ST02"],
                "BIG": ["BIG01", "BIG02", "BIG03", "BIG04"],
                "REF": ["REF01", "REF02", "REF03"],
                "N1": ["N101", "N102", "N103", "N104"],
                "N2": ["N201", "N202"],
                "N3": ["N301", "N302"],
                "N4": ["N401", "N402", "N403", "N404"],
                "PER": ["PER01", "PER02", "PER03", "PER04"],
                "ITD": ["ITD01", "ITD02", "ITD03", "ITD04", "ITD05", "ITD06", "ITD07"],
                "DTM": ["DTM01", "DTM02", "DTM03"],
                "FOB": ["FOB01", "FOB02", "FOB03"],
                "CUR": ["CUR01", "CUR02"],
                "IT1": ["IT101", "IT102", "IT103", "IT104", "IT105", "IT106", "IT107"],
                "PID": ["PID01", "PID02", "PID03", "PID04", "PID05"],
                "CTT": ["CTT01", "CTT02"],
                "SAC": ["SAC01", "SAC02", "SAC03", "SAC04", "SAC05"],
                "SE": ["SE01", "SE02"]
            }
            grouped: Dict[str, Dict[str, str]] = {}
            for seg, seg_keys in keys_by_segment.items():
                seg_map: Dict[str, str] = {}
                for k in seg_keys:
                    v = values.get(k)
                    if v is not None and str(v).strip() != "":
                        seg_map[k] = str(v)
                if seg_map:
                    grouped[seg] = seg_map
            return grouped

        key_fields = extract_key_fields(req.edi_field_values or {})

        # Build list of EDI-present fields and their spec status (M/O/X)
        edi_present_status: list[Dict[str, str]] = []
        for code in sorted(set(req.edi_fields)):
            letter = (status_map.get(code) or ("M" if merged_requirements.get(code) else "O")).upper()
            if letter == 'M':
                label = 'Must Use'
            elif letter == 'X':
                label = 'Conditional'
            else:
                label = 'Optional'
            edi_present_status.append({
                "field": code,
                "status_letter": letter,
                "status_label": label
            })

        return CompareResult(
            is_810=is_810,
            message="Comparison complete",
            missing_mandatory=missing,
            additional_fields=additional,
            present_fields=sorted(req.edi_fields),
            mandatory_fields=mandatory_fields,
            optional_fields=optional_fields,
            detailed_fields=detailed_fields_list,
            segment_summary=segment_summary,
            executive_summary=exec_summary,
            analysis=analysis,
            key_fields=key_fields,
            edi_present_status=edi_present_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during comparison: {str(e)}")


@app.get("/")
def root_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# Serve static resources
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
# Mount assets only if the directory exists to avoid startup errors
ASSETS_DIR = FRONTEND_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


