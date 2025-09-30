from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
from .services.edi_parser import parse_edi_to_xml
from .services.spec_parser import parse_pdf_spec_to_xml
from .services.compare import compare_fields


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


class CompareResult(BaseModel):
    is_810: bool
    message: str
    missing_mandatory: list[str]
    additional_fields: list[str]
    present_fields: list[str]
    mandatory_fields: list[str]
    optional_fields: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


@app.post("/api/parse/edi")
async def parse_edi(file: UploadFile = File(...)):
    content = (await file.read()).decode(errors="ignore")
    xml, fields, is_810 = parse_edi_to_xml(content)
    if not is_810:
        raise HTTPException(status_code=400, detail="Please upload an EDI 810 sample invoice.")
    return {"xml": xml, "fields": sorted(list(fields)), "is_810": is_810}


@app.post("/api/parse/spec")
async def parse_spec(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF")
    xml, requirements, all_fields = parse_pdf_spec_to_xml(pdf_bytes)
    return {"xml": xml, "requirements": requirements, "fields": sorted(list(all_fields))}


class CompareRequest(BaseModel):
    edi_xml: str
    spec_xml: str
    edi_fields: list[str]
    spec_requirements: dict[str, bool]


@app.post("/api/compare", response_model=CompareResult)
async def compare(req: CompareRequest):
    missing, additional = compare_fields(req.edi_fields, req.spec_requirements)
    # Heuristic: if required BIG01 present, assume 810 remains True; client enforces before this
    is_810 = True
    mandatory_fields = sorted([k for k, v in req.spec_requirements.items() if v])
    optional_fields = sorted([k for k, v in req.spec_requirements.items() if not v])
    return CompareResult(
        is_810=is_810,
        message="Comparison complete",
        missing_mandatory=missing,
        additional_fields=additional,
        present_fields=sorted(req.edi_fields),
        mandatory_fields=mandatory_fields,
        optional_fields=optional_fields,
    )


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


