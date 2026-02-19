from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn

app = FastAPI(title="PharmaGuard API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_DRUGS = [
    "CODEINE",
    "WARFARIN",
    "CLOPIDOGREL",
    "SIMVASTATIN",
    "AZATHIOPRINE",
    "FLUOROURACIL",
]

CRITICAL_GENES = [
    "CYP2D6",
    "CYP2C19",
    "CYP2C9",
    "SLCO1B1",
    "TPMT",
    "DPYD",
]


@app.post("/analyze")
async def analyze_vcf(
    file: UploadFile = File(...),
    drug: str = Form(...)
):

    if not file.filename.endswith(".vcf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file format. Only .vcf allowed."}
        )

    if drug.upper() not in SUPPORTED_DRUGS:
        return JSONResponse(
            status_code=400,
            content={"error": "Unsupported drug."}
        )

    content = await file.read()
    lines = content.decode("utf-8").split("\n")

    detected_variants = []
    primary_gene = "Unknown"
    rsid = "rs000000"
    total_variants = 0

    for line in lines:
        if line.startswith("#"):
            continue

        total_variants += 1
        parts = line.split("\t")

        if len(parts) > 2:
            rsid = parts[2]

        # Simple demo gene detection from INFO
        if "CYP2D6" in line:
            primary_gene = "CYP2D6"
        elif "CYP2C19" in line:
            primary_gene = "CYP2C19"
        elif "CYP2C9" in line:
            primary_gene = "CYP2C9"
        elif "SLCO1B1" in line:
            primary_gene = "SLCO1B1"
        elif "TPMT" in line:
            primary_gene = "TPMT"
        elif "DPYD" in line:
            primary_gene = "DPYD"

    detected_variants.append({
        "rsid": rsid,
        "gene": primary_gene
    })

    # Risk Logic (Prototype)
    if primary_gene == "CYP2D6" and drug.upper() == "CODEINE":
        risk_label = "Toxic"
        severity = "high"
        phenotype = "PM"
    elif primary_gene == "CYP2C19" and drug.upper() == "CLOPIDOGREL":
        risk_label = "Ineffective"
        severity = "high"
        phenotype = "PM"
    elif primary_gene == "TPMT" and drug.upper() == "AZATHIOPRINE":
        risk_label = "Adjust Dosage"
        severity = "moderate"
        phenotype = "IM"
    else:
        risk_label = "Safe"
        severity = "none"
        phenotype = "NM"

    response = {
        "patient_id": "PATIENT_001",
        "drug": drug.upper(),
        "timestamp": datetime.utcnow().isoformat(),

        "risk_assessment": {
            "risk_label": risk_label,
            "confidence_score": 0.90,
            "severity": severity
        },

        "pharmacogenomic_profile": {
            "primary_gene": primary_gene,
            "diplotype": "*1/*2",
            "phenotype": phenotype,
            "detected_variants": detected_variants
        },

        "clinical_recommendation": {
            "cpic_guideline_reference": "CPIC Level A",
            "recommendation": "Follow CPIC guideline recommendation.",
            "dose_adjustment": "Adjust dose according to CPIC recommendations."
        },

        "llm_generated_explanation": {
            "summary": f"{primary_gene} phenotype {phenotype} affects {drug.upper()} response.",
            "biological_mechanism": "Variant alters enzyme activity affecting drug metabolism.",
            "variant_citations": [rsid]
        },

        "quality_metrics": {
            "vcf_parsing_success": True,
            "total_variants_scanned": total_variants,
            "relevant_variants_found": len(detected_variants),
            "analysis_confidence": 0.92
        }
    }

    return response


@app.get("/")
def root():
    return {"message": "PharmaGuard API is running."}
