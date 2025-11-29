from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import EmployeeCreate, EmployeeUpdate
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel

# ---------------------------
# JWT / Auth config (demo)
# ---------------------------
SECRET_KEY = "your-very-secret-key-change-this"  # change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simple demo user DB (in-memory). Replace with real user storage in production.
fake_users_db = {
    "admin": {
        "username": "admin",
        # password = "secret123" hashed via passlib bcrypt
        "hashed_password": pwd_context.hash("secret123"),
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str) -> Optional[UserInDB]:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # Could add extra checks here
    return current_user

# ---------------------------
# App & MongoDB config
# ---------------------------
app = FastAPI(title="Employee API with MongoDB (with JWT)")

MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client["assessment_db"]
employees = db["employees"]

# Helper to format employee doc for responses
def employee_helper(employee) -> dict:
    return {
        "id": str(employee["_id"]),
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "department": employee["department"],
        "salary": employee["salary"],
        "joining_date": str(employee["joining_date"]),
        "skills": employee["skills"],
    }

# ---------------------------
# Auth endpoints
# ---------------------------

@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtain a JWT access token. Use form fields:
    - username
    - password

    Example (curl):
    curl -X POST -F "username=admin" -F "password=secret123" http://127.0.0.1:8000/token
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------
# CRUD Endpoints (protected where appropriate)
# ---------------------------

# Create Employee (protected)
@app.post("/employees", tags=["employees"])
async def create_employee(employee: EmployeeCreate, current_user: User = Depends(get_current_active_user)):
    existing = await employees.find_one({"employee_id": employee.employee_id})
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    new_employee = employee.dict()
    new_employee["joining_date"] = str(new_employee["joining_date"])
    await employees.insert_one(new_employee)
    return {"message": "Employee created successfully"}

# Get Employee by ID (public)
@app.get("/employees/{employee_id}", tags=["employees"])
async def get_employee(employee_id: str):
    employee = await employees.find_one({"employee_id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_helper(employee)

# Update Employee (protected)
@app.put("/employees/{employee_id}", tags=["employees"])
async def update_employee(employee_id: str, update_data: EmployeeUpdate, current_user: User = Depends(get_current_active_user)):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if "joining_date" in update_dict:
        update_dict["joining_date"] = str(update_dict["joining_date"])
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await employees.update_one({"employee_id": employee_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully"}

# Delete Employee (protected)
@app.delete("/employees/{employee_id}", tags=["employees"])
async def delete_employee(employee_id: str, current_user: User = Depends(get_current_active_user)):
    result = await employees.delete_one({"employee_id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# List Employees (public) with optional department + pagination
@app.get("/employees", tags=["employees"])
async def list_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, description="Page size"),
):
    query = {}
    if department:
        query["department"] = department

    skip = (page - 1) * size
    cursor = employees.find(query).sort("joining_date", -1).skip(skip).limit(size)
    result = []
    async for emp in cursor:
        result.append(employee_helper(emp))
    return result

# Average Salary (public) with optional department filter
@app.get("/employees/avg-salary", tags=["employees"])
async def average_salary(department: Optional[str] = Query(None, description="Filter by department")):
    pipeline = []
    if department:
        pipeline.append({"$match": {"department": department}})
    pipeline.append({"$group": {"_id": "$department", "avg_salary": {"$avg": "$salary"}}})
    
    cursor = employees.aggregate(pipeline)
    result = []
    async for doc in cursor:
        result.append({"department": doc["_id"], "avg_salary": doc["avg_salary"]})
    return result

# Search Employees by one or multiple skills (public)
@app.get("/employees/search", tags=["employees"])
async def search_employees(skills: str = Query(..., description="Comma-separated list of skills")):
    skills_list = [skill.strip() for skill in skills.split(",")]
    cursor = employees.find({"skills": {"$all": skills_list}})
    result = []
    async for emp in cursor:
        result.append(employee_helper(emp))
    return result

# Root
@app.get("/", tags=["root"])
async def root():
    return {"message": "Employee API is running. Go to /docs for Swagger UI"}
