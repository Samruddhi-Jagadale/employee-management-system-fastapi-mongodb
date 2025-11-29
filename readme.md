

## Employee API with MongoDB

This project is a **FastAPI application** that connects to **MongoDB** to manage Employee records.  
It implements **CRUD operations, search, filtering, aggregation**, and optional enhancements like **JWT authentication**.

---
 
## Features
- Create Employee – Add new employee records (with unique employee_id).  
-Read Employee – Fetch employee details by ID.  
- Update Employee – Partial updates supported.  
- Delete Employee – Remove employees by ID.  
- List Employees – Filter by department and sort by joining date.  
- Search Employees – Find employees by skills.  
- Average Salary by Department – MongoDB aggregation query.  
- JWT Authentication(optional enhancement) – Protect APIs with token-based auth.  
- Pagination(optional enhancement) – Paginate employee listings.  

---

## Tech Stack
- Backend Framework: FastAPI  
- Database: MongoDB (Motor async driver)  
- Server: Uvicorn (ASGI)  
- Validation: Pydantic  
- Authentication: JWT (JSON Web Token), Passlib for password hashing  

---



### Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

* **Windows (cmd):**

  ```bash
  venv\Scripts\activate
  ```
* **Linux/Mac:**

  ```bash
  source venv/bin/activate
  ```

### Install Dependencies

```bash
pip install -r requirements.txt
```

(If `requirements.txt` is missing, run:)

```bash
pip install fastapi uvicorn motor pydantic passlib[bcrypt] python-jose[cryptography] python-multipart
```

### Start MongoDB

Make sure MongoDB server is running locally (default connection string is):

```
mongodb://localhost:27017
```

### Run the Application

```bash
uvicorn main:app --reload
```

---

## 📖 API Documentation

Once running, you can test APIs at:

* Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📊 Example Employee JSON

```json
{
  "employee_id": "E123",
  "name": "John Doe",
  "department": "Engineering",
  "salary": 75000,
  "joining_date": "2023-01-15",
  "skills": ["Python", "MongoDB", "APIs"]
}
```

---

## 🔑 Authentication (Optional Enhancement)

* Register User → `POST /register`
* Login User → `POST /token` (returns JWT token)
* In Swagger UI → click Authorize and enter:

  ```
  Bearer <your_token>
  ```

---

## ✅ Status

* All core CRUD operations are implemented.
* Querying, aggregation, and search tested in Swagger UI.
* JWT authentication added for secure routes.

---

## 👨‍💻 Author

* Name: Samruddhi Mahesh Jagadale
* Email: samruddhijagadale16@gmail.com
* GitHub Repo: https://github.com/Samruddhi-Jagadale

---

