"""
Database Schemas for the CRM app

Each Pydantic model corresponds to a MongoDB collection (lowercase of class name).
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

class AppUser(BaseModel):
    """
    Users collection schema
    Collection name: "appuser"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Password hash (never store plain password)")
    is_active: bool = Field(True, description="Whether user is active")

class Contact(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr

class SaleItem(BaseModel):
    phone_number: str = Field(..., description="Phone number for the subscription")
    plan: str = Field(..., description="Subscription/plan name")
    price: float = Field(..., ge=0, description="Price (SEK)")
    contract_term_months: int = Field(..., ge=0, description="Binding time in months")
    renegotiation_date: date = Field(..., description="Omförhandlingsdatum")

class Company(BaseModel):
    """
    Companies collection schema
    Collection name: "company"
    """
    company_name: str = Field(..., description="Företagsnamn")
    orgnr: str = Field(..., description="Organisationsnummer")
    status: str = Field(..., description="Status")
    contacts: List[Contact] = Field(default_factory=list)
    sales: List[SaleItem] = Field(default_factory=list)
