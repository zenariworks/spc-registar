# SPC Registar

A digital registry for parishes of the Serbian Orthodox Church — parishioners, households, baptisms, weddings, priests, and a feast-day (slava) calendar. A single installation serves **multiple parishes**, with fully isolated data per parish.

!!! tip "New here?"
    Go straight to [Development setup](setup.md) if you're building locally, or [Standalone Docker](standalone.md) if you just want to run the app.

## How it works (in brief)

- **Multi-parish (django-tenants).** Each parish is a separate Postgres schema in one database; one parish's data is never visible to another. Shared tables (users, parishes) live in the `public` schema. Details: [Architecture](architecture.md).
- **Roles and authorization.** Everyone must sign in. Write access depends on role: **Admin**, **Office** (parishioners, households, baptisms, weddings), **Clergy** (priests), **Read-only**.
- **Registers.** Parishioners and households, with the **baptism** and **wedding** registers; a separate **priests** register.
- **Printing.** The detail form prints straight from the browser (`window.print()`), faithful to the official register form; field positions are calibrated.
- **Slava calendar.** Fixed and movable feasts, with a short daily reminder and fasting info.
- **Tech.** Django 6 + PostgreSQL, server-rendered (no SPA), PDF via WeasyPrint, behind gunicorn and Caddy.

## Quick start

- **Develop on your machine** → [Development setup](setup.md)
- **Run everything in Docker (local / Windows / server)** → [Standalone Docker](standalone.md)
- **Production on a server** → [Deployment](deployment.md)

After it starts, the app is at `http://localhost:8000/`, with sign-in at `/prijava/`.

## All documentation

| Document | About |
|---|---|
| [Development setup](setup.md) | bare-metal (pyenv) and Docker Compose environments |
| [Standalone Docker](standalone.md) | all-in-one bundle + image with an external database |
| [Deployment](deployment.md) | gunicorn + systemd + Caddy, and Docker prod |
| [Architecture](architecture.md) | django-tenants schemas, authorization, models, URL map |
| [Testing](testing.md) | tests, coverage, pre-commit hooks |
| [Data migration](MIGRACIJA.md) | importing from the legacy HramSP app (DBF → Postgres) |

> Detail pages not yet translated fall back to Serbian.
