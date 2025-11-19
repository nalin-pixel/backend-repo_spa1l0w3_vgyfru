import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Company, AppUser

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers to handle ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# ------------------------
# Auth (simple demo only)
# ------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    name: str

@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # Demo login: accept any non-empty password, return a fake token
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    return LoginResponse(token="demo-token", name=payload.email.split("@")[0])

# ------------------------
# Companies CRUD
# ------------------------

class CompanyOut(BaseModel):
    id: str
    company_name: str
    orgnr: str
    status: str

class CompanyDetailOut(CompanyOut):
    contacts: list
    sales: list

@app.post("/api/companies", response_model=CompanyOut)
def create_company(company: Company):
    inserted_id = create_document("company", company)
    return CompanyOut(
        id=str(inserted_id),
        company_name=company.company_name,
        orgnr=company.orgnr,
        status=company.status,
    )

@app.get("/api/companies", response_model=List[CompanyOut])
def list_companies():
    items = get_documents("company")
    result = []
    for it in items:
        result.append(
            CompanyOut(
                id=str(it.get("_id")),
                company_name=it.get("company_name", ""),
                orgnr=it.get("orgnr", ""),
                status=it.get("status", ""),
            )
        )
    return result

@app.get("/api/companies/{company_id}", response_model=CompanyDetailOut)
def get_company(company_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    doc = db["company"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyDetailOut(
        id=str(doc.get("_id")),
        company_name=doc.get("company_name", ""),
        orgnr=doc.get("orgnr", ""),
        status=doc.get("status", ""),
        contacts=doc.get("contacts", []),
        sales=doc.get("sales", []),
    )

@app.put("/api/companies/{company_id}", response_model=CompanyDetailOut)
def update_company(company_id: str, company: Company):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    data = company.model_dump()
    data["updated_at"] = datetime.utcnow()
    result = db["company"].find_one_and_update(
        {"_id": oid}, {"$set": data}, return_document=True
    )
    doc = db["company"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyDetailOut(
        id=str(doc.get("_id")),
        company_name=doc.get("company_name", ""),
        orgnr=doc.get("orgnr", ""),
        status=doc.get("status", ""),
        contacts=doc.get("contacts", []),
        sales=doc.get("sales", []),
    )

@app.delete("/api/companies/{company_id}")
def delete_company(company_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    res = db["company"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Backend up"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db as _db
        if _db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = _db.name
            response["connection_status"] = "Connected"
            response["collections"] = _db.list_collection_names()[:10]
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
