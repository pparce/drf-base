# asp-base

An **ASP.NET Core 9 (Minimal APIs)** port of the `drf-base` Django REST Framework project.
It reproduces every feature of the original — JWT authentication, a custom email-based user,
Google Sign-In, image uploads, background email, rate limiting and OpenAPI docs — using modern
ASP.NET best practices.

## Highlights (ASP.NET best practices used)

- **Minimal APIs** organised by feature with `MapGroup` and endpoint extension methods.
- **Typed results** (`Results<Ok<T>, NotFound, ...>`) for accurate OpenAPI generation.
- **EF Core + PostgreSQL** (Npgsql) with a hand-checked initial migration applied on startup.
- **JWT bearer auth** with access/refresh tokens (replaces `simplejwt`).
- **PBKDF2 password hashing** via `PasswordHasher<User>` (replaces Django's hasher).
- **Options pattern** with start-up validation for JWT/Email/Google/Media config.
- **Built-in rate limiter** with `anon` (100/day), `user` (1000/day) and `auth` (10/min) policies.
- **FluentValidation** wired through a reusable endpoint filter.
- **Background email** via `Channel<T>` + `BackgroundService` with retries (replaces Celery).
- **Serilog** structured logging, **CORS**, security headers and **Swagger UI** with JWT support.

## Requirements

- [.NET SDK 9.0](https://dotnet.microsoft.com/download)
- PostgreSQL (or run everything with Docker Compose)

## Getting started

```sh
cd src/AspBase.Api

# 1. Set a real JWT signing key (>= 32 chars) and DB connection string,
#    either in appsettings.Development.json or as environment variables.
export Jwt__SigningKey="$(openssl rand -base64 48)"
export ConnectionStrings__Default="Host=localhost;Port=5432;Database=aspbase;Username=postgres;Password=postgres"

# 2. Run — migrations are applied automatically on startup.
dotnet run
```

Open <http://localhost:5080/swagger> for interactive API docs.

### With Docker

```sh
docker compose up --build
# API on http://localhost:8080/swagger
```

### Managing the database schema

An initial migration ships in `src/AspBase.Api/Migrations` and is applied on startup.
To evolve the schema after changing entities:

```sh
dotnet tool install --global dotnet-ef      # once
cd src/AspBase.Api
dotnet ef migrations add <Name>
dotnet ef database update
```

## API surface

| Area   | Method & route                          | Auth        | Notes |
|--------|-----------------------------------------|-------------|-------|
| Health | `GET /api/health`                       | anonymous   | DB connectivity probe |
| Auth   | `POST /api/auth/login`                  | anonymous   | returns access + refresh tokens |
| Auth   | `POST /api/auth/register`               | anonymous   | creates user, queues welcome email |
| Auth   | `POST /api/auth/sending_restore_code`   | anonymous   | emails a reset code |
| Auth   | `POST /api/auth/restore_password`       | anonymous   | resets password with code |
| Auth   | `POST /api/auth/google`                 | anonymous   | Google ID-token exchange |
| Auth   | `POST /api/auth/token/refresh`          | anonymous   | new access token from refresh |
| Users  | `GET /api/users`                        | staff       | paginated |
| Users  | `GET /api/users/{id}`                    | self/staff  | |
| Users  | `GET /api/users/me`                      | user        | current user |
| Users  | `POST /api/users`                        | staff       | create user |
| Users  | `PUT /api/users/{id}`                     | self/staff  | update email/name |
| Users  | `DELETE /api/users/{id}`                  | staff       | |
| Users  | `POST /api/users/admin_create`           | staff       | create/promote staff user |
| Users  | `POST /api/users/change_password`        | user        | |
| Core   | `GET/POST /api/core/image`              | user        | list / multipart upload |
| Core   | `GET/DELETE /api/core/image/{id}`        | user        | |

## How it maps to the DRF project

| DRF (Django)                          | ASP.NET Core (this repo)                                  |
|---------------------------------------|----------------------------------------------------------|
| `AuthViewSet`                         | `Features/Auth/AuthEndpoints`                             |
| `UserViewSet`                         | `Features/Users/UserEndpoints`                            |
| `ImageViewSet`                        | `Features/Core/ImageEndpoints`                            |
| `health_check`                        | `Features/Health/HealthEndpoints`                         |
| custom `User` model                   | `Domain/Entities/User` + `AppDbContext`                  |
| `BaseModel` / `BaseDate`              | `Domain/Entities/BaseEntity` + `SaveChanges` timestamps  |
| `simplejwt`                           | `Infrastructure/Auth/JwtTokenService`                    |
| `set_password` / `check_password`     | `Infrastructure/Auth/PasswordHashingService`             |
| Google OAuth verify                   | `Infrastructure/Auth/GoogleTokenValidator`               |
| `EmailService` + Celery tasks         | `Infrastructure/Email/*` (service + queue + hosted svc)  |
| DRF throttling                        | built-in rate limiter policies in `Program.cs`           |
| `drf-spectacular`                     | Swashbuckle / Swagger UI                                 |
| `django-cors-headers`                 | `AddCors` policy                                          |
| settings.py                           | `appsettings.json` + Options classes                     |
