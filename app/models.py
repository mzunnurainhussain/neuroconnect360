from pydantic import BaseModel, Field
from typing import Literal, Optional

Role = Literal['parent','professional','teacher','researcher','admin']

class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: Role = 'parent'
    preferred_language: Literal['en','ur','roman_ur'] = 'en'

class LoginIn(BaseModel):
    email: str
    password: str

class ChildIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    birth_year: Optional[int] = Field(default=None, ge=1990, le=2100)
    communication_level: Optional[str] = None
    school_status: Optional[str] = None
    primary_concerns: Optional[str] = None

class MilestoneIn(BaseModel):
    child_id: int
    domain: str
    title: str
    status: Literal['achieved','emerging','not_observed','unsure']
    note: Optional[str] = None

class ScreeningIn(BaseModel):
    child_id: Optional[int] = None
    consented: bool
    responses: list[int] = Field(min_length=6, max_length=6)

class AppointmentIn(BaseModel):
    professional_id: int
    requested_date: str
    mode: Literal['online','in_person']
    note: Optional[str] = Field(default=None, max_length=1000)

class ChatIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    language: Literal['en','ur','roman_ur'] = 'en'
