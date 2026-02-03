This is a solid foundation for a **QR-based Restaurant Management System**. The choice of FastAPI for the backend is excellent for high-performance asynchronous operations, and the directory structure follows industry best practices (separation of concerns between models, schemas, and CRUD).

Based on your request for a **Backend-only README**, I have refined and expanded your documentation. This version focuses strictly on the API, database architecture, and technical implementation details.

---

# 🍽️ QR Menu – Backend API

The core engine of the Restaurant Management System. This is a high-performance REST API built with **FastAPI**, featuring Role-Based Access Control (RBAC), multi-tenancy for restaurants, and dynamic pricing management.

## 🛠️ Tech Stack & Architecture

* **Framework:** FastAPI (Python 3.10+)
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy 2.0 (with async support if required)
* **Migrations:** Alembic
* **Security:** JWT (JSON Web Tokens), OAuth2, Passlib (bcrypt)
* **Validation:** Pydantic v2

---

## 🏗️ Project Structure

```text
fastapi_restaurant/
├── app/
│   ├── api/               # API Router endpoints (v1)
│   ├── core/              # Security, JWT, config, and constants
│   ├── crud/              # Reusable DB logic (Create, Read, Update, Delete)
│   ├── db/                # Session management and base classes
│   ├── models/            # SQLAlchemy database definitions
│   ├── schemas/           # Pydantic models for request/response validation
│   └── main.py            # Application initialization and middleware
├── migrations/            # Database version control files (Alembic)
├── uploads/               # Local storage for product/logo images
├── alembic.ini            # Migration configuration
└── requirements.txt       # Python dependencies

```

---

## 🔐 Database Schema & Relationships

The system utilizes a relational structure to ensure data integrity across multiple restaurants.

* **Users:** Stores Admin and Restaurant staff credentials.
* **Restaurants:** Linked to a User (Owner) and contains branding info.
* **Categories:** Global menu categories defined by Admin.
* **Products:** Linked to specific Restaurants and Categories.
* **Product Prices:** Supports multiple sizes (e.g., Small, Medium, Large) for a single product.

---

## ⚙️ Installation & Setup

### 1. Environment Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/qr_menu_db
SECRET_KEY=generate_a_secure_long_random_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
IMAGE_UPLOAD_DIR=./uploads

```

### 2. Install Requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

### 3. Initialize Database

```bash
alembic upgrade head

```

### 4. Run the Server

```bash
uvicorn app.main:app --reload

```

The interactive API documentation (Swagger UI) will be available at: `http://127.0.0.1:8000/docs`

---

## 🛡️ Role-Based Access Control (RBAC)

The API enforces strict permission layers using FastAPI Dependencies.

| Endpoint | Method | Admin | Restaurant | Public |
| --- | --- | --- | --- | --- |
| `/api/v1/restaurants/` | POST | ✅ | ❌ | ❌ |
| `/api/v1/categories/` | POST | ✅ | ❌ | ❌ |
| `/api/v1/products/` | POST | ❌ | ✅ | ❌ |
| `/api/v1/products/{id}` | GET | ✅ | ✅ | ✅ |

---

## 🧾 Key API Endpoints

### Authentication

* `POST /auth/login` - Returns JWT token.

### Admin Operations

* `POST /api/v1/restaurants/` - Onboard a new restaurant.
* `GET /api/v1/admin/stats` - Platform-wide analytics.

### Restaurant Operations

* `POST /api/v1/products/` - Add new item with price variants.
* `PATCH /api/v1/products/{id}/availability` - Toggle "Out of Stock" status.
* `PUT /api/v1/restaurants/profile` - Update branding and logo.

### Public Access

* `GET /api/v1/restaurants/{restaurant_id}/menu` - Fetches the full menu for the QR view.

---

## 🔒 Security Implementation

1. **Password Hashing:** Uses `bcrypt` for secure storage.
2. **Dependency Injection:** Current user and role are verified before every protected route.
3. **Ownership Logic:** CRUD operations for products check if `product.restaurant_id == current_user.restaurant_id`.
4. **CORS:** Configured to allow requests only from trusted frontend domains.
