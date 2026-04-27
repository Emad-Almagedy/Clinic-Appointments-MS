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

## 📡 API Architecture Versions

*   **`v1` (Role-Based)**: Endpoints are logically grouped by user roles (`/admin`, `/doctor`, `/reception`). Tailored for specific dashboard interfaces where each role has distinct endpoints.
*   **`v2` (Resource-Based REST)**: Unified, standard RESTful architecture where endpoints are grouped by system resources (`/appointments`, `/users`, `/patients`). Uses role-based permissions internally and accepts query parameters for advanced filtering.

---

## 🟢 API v2 Endpoints (Resource-Based REST)

### 🔐 Authentication
| Method | Endpoint             | Description           |
| :----- | :------------------- | :-------------------- |
| `POST` | `/api/v2/auth/token` | Login and receive JWT |
| `GET`  | `/api/v2/auth/me`    | Get current user      |

### 👥 Users
| Method   | Endpoint                   | Description         |
| :------- | :------------------------- | :------------------ |
| `GET`    | `/api/v2/users`            | List all users      |
| `POST`   | `/api/v2/users`            | Create a new user   |
| `GET`    | `/api/v2/users/doctors`    | List doctors        |
| `GET`    | `/api/v2/users/{id}`       | Get user details    |
| `PATCH`  | `/api/v2/users/{id}`       | Update user details |
| `DELETE` | `/api/v2/users/{id}`       | Deactivate user     |

### 🤒 Patients
| Method  | Endpoint                  | Description            |
| :------ | :------------------------ | :--------------------- |
| `GET`   | `/api/v2/patients`        | List all patients      |
| `POST`  | `/api/v2/patients`        | Register a new patient |
| `GET`   | `/api/v2/patients/{id}`   | Get patient details    |
| `PATCH` | `/api/v2/patients/{id}`   | Update patient details |

### 📅 Appointments
| Method  | Endpoint                      | Description                                    |
| :------ | :---------------------------- | :--------------------------------------------- |
| `GET`   | `/api/v2/appointments`        | List appointments (supports role-based filters)|
| `POST`  | `/api/v2/appointments`        | Book a new appointment                         |
| `GET`   | `/api/v2/appointments/{id}`   | Get appointment details                        |
| `PATCH` | `/api/v2/appointments/{id}`   | Update appointment (status, visit notes, etc.) |

### ⚙️ Settings
| Method   | Endpoint                      | Description                 |
| :------- | :---------------------------- | :-------------------------- |
| `GET`    | `/api/v2/settings`            | Get all system settings     |
| `POST`   | `/api/v2/settings`            | Create a new setting        |
| `PATCH`  | `/api/v2/settings/{id}`       | Update a setting            |
| `DELETE` | `/api/v2/settings/{id}`       | Delete a setting            |

### 📊 Dashboard Stats
| Method | Endpoint        | Description                         |
| :----- | :-------------- | :---------------------------------- |
| `GET`  | `/api/v2/stats` | Get statistics (filtered by role)   |

---

## 🔵 API v1 Endpoints (Role-Based)

### 🔐 Authentication

| Method | Endpoint             | Description           |
| :----- | :------------------- | :-------------------- |
| `POST` | `/api/v1/auth/token` | Login and receive JWT |
| `GET`  | `/api/v1/auth/me`    | Get current user      |

---

### 🛠️ Admin Dashboard

| Method   | Endpoint                       | Description                  |
| :------- | :----------------------------- | :--------------------------- |
| `GET`    | `/api/v1/admin/stats`          | System statistics            |
| `GET`    | `/api/v1/admin/status_summary` | Appointment status breakdown |
| `GET`    | `/api/v1/admin/appointments`   | All appointments             |
| `POST`   | `/api/v1/admin/users`          | Create user                  |
| `GET`    | `/api/v1/admin/users`          | List users                   |
| `PATCH`  | `/api/v1/admin/users/{id}`     | Update user                  |
| `DELETE` | `/api/v1/admin/users/{id}`     | Deactivate user              |
| `GET`    | `/api/v1/admin/settings`       | Get system settings          |
| `POST`   | `/api/v1/admin/settings`       | Create setting               |
| `PATCH`  | `/api/v1/admin/settings/{id}`  | Update setting               |
| `DELETE` | `/api/v1/admin/settings/{id}`  | Delete setting               |

---

### 👨‍⚕️ Doctor Dashboard

| Method  | Endpoint                                  | Description               |
| :------ | :---------------------------------------- | :------------------------ |
| `GET`   | `/api/v1/doctor/status`                   | Doctor workload summary   |
| `GET`   | `/api/v1/doctor/appointments_today`       | Today's appointments      |
| `GET`   | `/api/v1/doctor/appointments_upcoming`    | Upcoming appointments     |
| `GET`   | `/api/v1/doctor/appointments/{id}`        | Appointment details       |
| `POST`  | `/api/v1/doctor/appointments/{id}/notes`  | Add visit note            |
| `PATCH` | `/api/v1/doctor/appointments/{id}/status` | Update appointment status |
| `GET`   | `/api/v1/doctor/appointments`             | Appointment history       |

---

### 📋 Reception Dashboard

| Method  | Endpoint                              | Description               |
| :------ | :------------------------------------ | :------------------------ |
| `GET`   | `/api/v1/reception/stats`             | Reception dashboard stats |
| `GET`   | `/api/v1/reception/status_overview`   | Real-time clinic overview |
| `GET`   | `/api/v1/reception/appointments`      | Today's schedule          |
| `POST`  | `/api/v1/reception/appointments`      | Book appointment          |
| `PATCH` | `/api/v1/reception/appointments/{id}` | Reschedule/reassign       |
| `POST`  | `/api/v1/reception/patients`          | Register patient          |
| `GET`   | `/api/v1/reception/doctors`           | List doctors              |

---

##  Example Request

```bash
curl -X POST http://localhost:8000/api/v1/reception/appointments \
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

pip install -r requirements.txt

uvicorn app.main:app --reload
or
uv run fastapi dev main.py
```

---
