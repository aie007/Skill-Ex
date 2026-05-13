from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

class JobBase(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary: Optional[str] = None
    skills_required: List[str] = []

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: str = Field(default_factory=lambda: str(uuid4()))

    class Config:
        from_attributes = True

class ResumeBase(BaseModel):
    filename: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    s3_key: str
    extracted_skills: List[str] = []
    status: str = "pending"  # pending, processing, completed, failed

    class Config:
        from_attributes = True

class SkillExtractionResponse(BaseModel):
    resume_id: str
    filename: str
    skills: List[str]
    status: str
