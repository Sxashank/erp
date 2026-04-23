# SMFC ERP Backend

Enterprise NBFC Management System - Backend API

## Technology Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT + OAuth2
- **Python**: 3.11+

## Project Structure

```
backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── auth/            # Authentication endpoints
│   │   └── masters/         # Master data endpoints
│   ├── core/                # Core utilities (security, exceptions)
│   ├── models/              # SQLAlchemy models
│   │   ├── auth/            # User, Role, Permission models
│   │   └── masters/         # Organization, Unit, Dept, Designation
│   ├── repositories/        # Data access layer
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic layer
│   ├── config.py            # Application settings
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Docker setup
└── requirements.txt         # Python dependencies
```

## Quick Start

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python scripts/seed_data.py

# Create superuser
docker-compose exec backend python scripts/create_superuser.py
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_data.py
python scripts/create_superuser.py

# Start server
uvicorn app.main:app --reload
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## Default Credentials

After running seed scripts:
- **Username**: krishna
- **Email**: krishna@supersight.com
- **Password**: ChangeMe123!
- **Role**: SUPER_ADMIN

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Current user profile

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Roles & Permissions
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role
- `GET /api/v1/roles/permissions` - List permissions

### Organizations
- `GET /api/v1/organizations` - List organizations
- `POST /api/v1/organizations` - Create organization

### Units
- `GET /api/v1/units` - List units
- `GET /api/v1/units/tree` - Unit hierarchy
- `POST /api/v1/units` - Create unit

### Departments
- `GET /api/v1/departments` - List departments
- `GET /api/v1/departments/tree` - Department hierarchy
- `POST /api/v1/departments` - Create department

### Designations
- `GET /api/v1/designations` - List designations
- `POST /api/v1/designations` - Create designation

## License

Proprietary - SMFC Ltd
