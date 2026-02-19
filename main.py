
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(title="PharmaGuard API")
 from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------
# VCF PARSER
# ------------------------
def parse_vcf(file_content):
    variants = []
    for line in file_content.split("\n"):
        if line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) < 8:
            continue
        info = columns[7]
        info_dict = {}
        for item in info.split(";"):
            if "=" in item:
                key, value = item.split("=")
                info_dict[key] = value
        if "GENE" in info_dict:
            variants.append({
                "gene": info_dict.get("GENE"),
                "star": info_dict.get("STAR"),
                "rsid": info_dict.get("RS")
            })
    return variants


# ------------------------
# PHENOTYPE MAPPING
# ------------------------
def get_phenotype(star):
    if star == "*4":
        return "PM"
    if star == "*1":
        return "NM"
    if star == "*2xN":
        return "URM"
    return "Unknown"


# ------------------------
# RISK ENGINE
# ------------------------
def get_risk(gene, phenotype, drug):

    if drug == "CODEINE" and gene == "CYP2D6":
        if phenotype == "PM":
            return "Ineffective", "high"
        if phenotype == "URM":
            return "Toxic", "critical"
        return "Safe", "low"

    if drug == "WARFARIN" and gene == "CYP2C9":
        if phenotype == "PM":
            return "Adjust Dosage", "moderate"
        return "Safe", "low"

    if drug == "CLOPIDOGREL" and gene == "CYP2C19":
        if phenotype == "PM":
            return "Ineffective", "high"
        return "Safe", "low"

    return "Unknown", "none"


# ------------------------
# MAIN ENDPOINT
# ------------------------
@app.post("/analyze/")
async def analyze(file: UploadFile, drug: str = Form(...)):

    content = await file.read()
    file_text = content.decode()

    variants = parse_vcf(file_text)

    if not variants:
        return JSONResponse(content={"error": "No valid variants found"})

    variant = variants[0]
    gene = variant["gene"]
    star = variant["star"]
    rsid = variant["rsid"]

    phenotype = get_phenotype(star)
    risk_label, severity = get_risk(gene, phenotype, drug.upper())

    response = {
        "patient_id": "PATIENT_001",
        "drug": drug.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "risk_assessment": {
            "risk_label": risk_label,
            "confidence_score": 0.9,
            "severity": severity
        },
        "pharmacogenomic_profile": {
            "primary_gene": gene,
            "diplotype": star,
            "phenotype": phenotype,
            "detected_variants": [
                {
                    "rsid": rsid,
                    "gene": gene
                }
            ]
        },
        "clinical_recommendation": {
            "action": "Follow CPIC guideline recommendation"
        },
        "llm_generated_explanation": {
            "summary": f"{gene} phenotype {phenotype} affects {drug} response."
        },
        "quality_metrics": {
            "vcf_parsing_success": True
        }
    }

    return response
