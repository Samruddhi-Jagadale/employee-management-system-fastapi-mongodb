from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# Common fields shared by all employees
class EmployeeBase(BaseModel):
    name: str = Field(..., example="John Doe")
    department: str = Field(..., example="Engineering")
    salary: float = Field(..., example=75000)
    joining_date: date = Field(..., example="2023-01-15")
    skills: List[str] = Field(..., example=["Python", "MongoDB", "APIs"])

# For creating new employees
class EmployeeCreate(EmployeeBase):
    employee_id: str = Field(..., description="Unique Employee ID", example="E123")

# For updating employees (all fields optional)
class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    joining_date: Optional[date] = None
    skills: Optional[List[str]] = None
