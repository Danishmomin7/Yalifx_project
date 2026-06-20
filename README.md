# YaliFX

YaliFX is a Python-backed marketplace MVP for production-ready 3D FX assets. It is built around the product brief in `YaliFX_Pixl_Prod.pdf`: VDB assets, Unreal Niagara systems, Unity VFX Graph assets, curated quality content, community uploads, studio purchasing, creator monetization, subscriptions, and enterprise licensing.

## Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: Server-rendered HTML plus vanilla CSS/JavaScript
- Tests: Pytest with FastAPI TestClient

## Features

- Searchable FX marketplace with category, format, engine, curated, and price filters
- Seeded assets for smoke, fire, explosions, clouds, realtime magic, dust, energy, and fog
- Creator upload API and UI form
- Checkout simulation with commission calculation and generated download links
- Creator dashboard API for sales, revenue, and asset metrics
- Studio subscription plans and enterprise inquiry capture
- Local procedural thumbnail assets for the marketplace cards

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## API

- `GET /api/health`
- `GET /api/assets`
- `GET /api/assets/{slug}`
- `POST /api/assets`
- `POST /api/orders`
- `GET /api/creators`
- `GET /api/creators/{creator_id}/dashboard`
- `GET /api/plans`
- `POST /api/enterprise/inquiries`

## Business Mapping

- Commission model: checkout calculates a marketplace commission on every order.
- Featured creators: seeded assets include featured and curated flags.
- Studio subscriptions: `/api/plans` exposes studio plan options and the UI displays them.
- Enterprise licensing: inquiry endpoint captures games, film, and studio licensing leads.

