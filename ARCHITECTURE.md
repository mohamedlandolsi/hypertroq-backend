# HyperToQ Backend - Architecture Documentation

## Overview

This project implements **Clean Architecture** principles to create a maintainable, testable, and scalable FastAPI backend.

## Layer Structure

### 1. Domain Layer (`app/domain/`)
**Purpose**: Core business logic and rules (framework-independent)

- **Entities** (`entities/`): Business objects with identity
  - `base.py`: Base entity class with ID and timestamps
  - `user.py`: User entity with business logic

- **Value Objects** (`value_objects/`): Immutable objects without identity
  - `base.py`: Base value object class
  - `email.py`: Email value object with validation

- **Interfaces** (`interfaces/`): Repository contracts
  - `repository.py`: Base repository interface
  - `user_repository.py`: User repository interface

### 2. Application Layer (`app/application/`)
**Purpose**: Application-specific business rules and orchestration

- **DTOs** (`dtos/`): Data Transfer Objects for API communication
  - `user_dto.py`: User-related DTOs
  - `auth_dto.py`: Authentication DTOs

- **Services** (`services/`): Business logic orchestration
  - `user_service.py`: User management logic
  - `auth_service.py`: Authentication logic

### 3. Infrastructure Layer (`app/infrastructure/`)
**Purpose**: External dependencies and implementations

- **Database** (`database/`): Database configuration
  - `session.py`: SQLAlchemy session and engine setup

- **Repositories** (`repositories/`): Data access implementations
  - `user_repository.py`: User repository implementation

- **External** (`external/`): Third-party integrations
  - `gemini.py`: Google Gemini AI service
  - `lemonsqueezy.py`: LemonSqueezy payment service

- **Cache** (`cache/`): Caching implementations
  - `redis_client.py`: Redis client wrapper

- **Tasks** (`tasks.py`): Celery background tasks

### 4. Presentation Layer (`app/presentation/`)
**Purpose**: API interface and HTTP concerns

- **API** (`api/v1/`): RESTful endpoints
  - `auth.py`: Authentication routes
  - `users.py`: User management routes
  - `health.py`: Health check endpoint

- **Middleware** (`middleware/`): HTTP middleware
  - `logging.py`: Request/response logging
  - `cors.py`: CORS configuration

### 5. Core (`app/core/`)
**Purpose**: Shared configurations and utilities

- `config.py`: Application settings
- `security.py`: Security utilities (JWT, password hashing)
- `dependencies.py`: FastAPI dependency injection
- `celery_app.py`: Celery configuration

### 6. Models (`app/models/`)
**Purpose**: Database models (SQLAlchemy)

- `user.py`: User database model

## Data Flow

```
HTTP Request
    ↓
Presentation Layer (API Routes)
    ↓
Application Layer (Services/Use Cases)
    ↓
Domain Layer (Entities/Business Logic)
    ↓
Infrastructure Layer (Repositories)
    ↓
Database
```

## Dependency Rules

1. **Domain Layer**: No dependencies on other layers
2. **Application Layer**: Depends only on Domain Layer
3. **Infrastructure Layer**: Depends on Domain and Application Layers
4. **Presentation Layer**: Depends on Application and Infrastructure Layers

## Key Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Single Responsibility**: Each class has one reason to change
4. **Open/Closed**: Open for extension, closed for modification
5. **Interface Segregation**: Many specific interfaces over one general interface

## Testing Strategy

- **Unit Tests**: Test domain entities and services in isolation
- **Integration Tests**: Test repository implementations with database
- **API Tests**: Test HTTP endpoints end-to-end

## Adding New Features

1. **Define Entity** in `domain/entities/`
2. **Create Repository Interface** in `domain/interfaces/`
3. **Implement Repository** in `infrastructure/repositories/`
4. **Create DTOs** in `application/dtos/`
5. **Implement Service** in `application/services/`
6. **Create API Routes** in `presentation/api/v1/`
7. **Add Tests** in `tests/`

## Benefits

- ✅ **Testability**: Easy to test business logic in isolation
- ✅ **Maintainability**: Clear structure and responsibilities
- ✅ **Flexibility**: Easy to swap implementations
- ✅ **Scalability**: Well-organized for team collaboration
- ✅ **Framework Independence**: Core logic not tied to FastAPI
