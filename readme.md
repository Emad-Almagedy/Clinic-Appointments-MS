#  HealthCare Clinic Management System API

A production-ready backend system for managing clinic operations, built with **FastAPI**, **SQLModel**, and **Async SQLAlchemy**.
Designed with scalability, data integrity, and real-world healthcare workflows in mind.

---

##  Overview

This API powers a role-based clinic system supporting:

* Doctors managing appointments and visit notes
* Receptionists handling bookings and patient registration
* Admins controlling users, settings, and system-wide insights


---

## 📡 API Endpoints

A unified, standard RESTful architecture grouped by system resources. Uses role-based permissions internally and accepts query parameters for advanced filtering.

### 🔐 Authentication
| Method | Endpoint             | Description           |
| :----- | :------------------- | :-------------------- |
| `POST` | `/api/v1/auth/token` | Login and receive JWT |
| `GET`  | `/api/v1/auth/me`    | Get current user      |

### 👥 Users
| Method   | Endpoint                   | Description         |
| :------- | :------------------------- | :------------------ |
| `GET`    | `/api/v1/users`            | List all users      |
| `POST`   | `/api/v1/users`            | Create a new user   |
| `GET`    | `/api/v1/users/doctors`    | List doctors        |
| `GET`    | `/api/v1/users/{id}`       | Get user details    |
| `PATCH`  | `/api/v1/users/{id}`       | Update user details |
| `DELETE` | `/api/v1/users/{id}`       | Deactivate user     |

### 🤒 Patients
| Method  | Endpoint                  | Description            |
| :------ | :------------------------ | :--------------------- |
| `GET`   | `/api/v1/patients`        | List all patients      |
| `POST`  | `/api/v1/patients`        | Register a new patient |
| `GET`   | `/api/v1/patients/{id}`   | Get patient details    |
| `PATCH` | `/api/v1/patients/{id}`   | Update patient details |

### 📅 Appointments
| Method  | Endpoint                      | Description                                    |
| :------ | :---------------------------- | :--------------------------------------------- |
| `GET`   | `/api/v1/appointments`        | List appointments (supports role-based filters)|
| `POST`  | `/api/v1/appointments`        | Book a new appointment                         |
| `GET`   | `/api/v1/appointments/{id}`   | Get appointment details                        |
| `PATCH` | `/api/v1/appointments/{id}`   | Update appointment (status, visit notes, etc.) |

### ⚙️ Settings
| Method   | Endpoint                      | Description                 |
| :------- | :---------------------------- | :-------------------------- |
| `GET`    | `/api/v1/settings`            | Get all system settings     |
| `POST`   | `/api/v1/settings`            | Create a new setting        |
| `PATCH`  | `/api/v1/settings/{id}`       | Update a setting            |
| `DELETE` | `/api/v1/settings/{id}`       | Delete a setting            |

### 📊 Dashboard Stats
| Method | Endpoint        | Description                         |
| :----- | :-------------- | :---------------------------------- |
| `GET`  | `/api/v1/stats` | Get statistics (filtered by role)   |

---

##  Example Request

```bash
curl -X POST http://localhost:8000/api/v1/appointments \
-H "Authorization: Bearer <token>" \
-H "Content-Type: application/json" \
-d '{
  "doctor_id": "uuid",
  "patient_id": "uuid",
  "appointment_date": "2026-04-21",
  "appointment_time": "10:00:00"
}'
```

---

## 🛠️ Setup & Installation

```bash
git clone <your-repo>
cd project

# Install dependencies (using uv)
uv sync
# or pip install -r requirements.txt

# Set up the database tables using Alembic
uv run alembic upgrade head

# Seed the database with initial settings and admin user
uv run python -m app.scripts.seed_settings
uv run python -m app.scripts.seed_admin

# Run the server
uv run fastapi dev main.py
```

---

## 🗄️ Database Migrations (Alembic)

This project uses Alembic to manage database schema changes.

**To create a new migration** (after changing a SQLModel class):
```bash
uv run alembic revision --autogenerate -m "description of changes"
```

**To apply migrations to the database**:
```bash
uv run alembic upgrade head
```

---
