# Chart Facts

L0 astrological **facts-only** API for classical Western astrology.

Computes planetary positions and house cusps using [Swiss Ephemeris](https://www.astro.com/swisseph/) via [pyswisseph](https://github.com/astrorigin/pyswisseph). No dignities, scoring, or interpretations — only verifiable astronomical/chart geometry data for upstream services (L1/L2).

Designed to sit behind a private network; L1 consumes JSON and adds classical derivations + your proprietary scoring.

## Architecture

```text
chart-facts (L0, this repo, AGPL)  →  chart-classical (L1, private)
                                    →  chart-engine (L2, private)
                                    →  mayakin UI
```

## Quick start (Docker)

```bash
git clone https://github.com/YOUR_USER/chart-facts.git
cd chart-facts
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

## API

### `GET /health`

Liveness check.

### `GET /meta`

Lists supported house systems and body ids.

### `POST /facts`

Request:

```json
{
  "datetime": "2026-06-23T04:18:00",
  "timezone": "Asia/Taipei",
  "latitude": 25.416667,
  "longitude": 121.5,
  "house_system": "alcabitius"
}
```

Response (abbreviated):

```json
{
  "engine": {
    "name": "swiss-ephemeris",
    "version": "2.10.x",
    "ephe_path": "/app/ephe",
    "zodiac": "tropical"
  },
  "input": { "...": "..." },
  "julian_day_ut": 2460849.345833,
  "angles": { "asc": 285.42, "mc": 210.18, "...": "..." },
  "houses": [{ "number": 1, "cusp": 285.42 }],
  "bodies": [{ "id": "sun", "longitude": 91.5, "speed": 0.95, "retrograde": false }]
}
```

### House systems

| Key | Swiss Ephemeris |
|-----|-----------------|
| `placidus` | P |
| `koch` | K |
| `alcabitius` | A |
| `whole_sign` | W |
| `equal` | E |
| `campanus` | C |
| `regiomontanus` | R |
| `porphyry` | O |
| `morinus` | M |
| `topocentric` | T |
| `krusinski` | U |
| `apc` | Y |

Default: **`alcabitius`** (matches [almuten.net](https://almuten.net/) default).

## Local development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
./scripts/download-ephe.sh   # or scripts/download-ephe.ps1
export EPHE_PATH=./ephe
uvicorn chart_facts.main:app --reload --port 8000
pytest
```

Integration tests (server running):

```bash
pytest -m integration tests/test_api.py
```

## Ephemeris files

See [ephe/README.md](ephe/README.md). Production should always use Swiss Ephemeris `.se1` files for alignment with almuten.net / Astro.com.

## Deploy on your server (with mayakin)

1. Start L0:

   ```bash
   cd chart-facts && docker compose up -d --build
   ```

2. L1 calls L0 at `http://chart-l0:8000` when on the same Docker network `chart-net`, or `http://127.0.0.1:8000` from the host.

3. Connect mayakin to `chart-net` (see mayakin `docker-compose.yml` comment) and set `CHART_L0_URL=http://chart-l0:8000`.

**Do not expose port 8000 to the public internet** unless you accept open ephemeris API abuse.

## License

Copyright (C) 2026 Chart Facts contributors

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU Affero General Public License v3.0 or later**.

See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Planetary positions are calculated using **Swiss Ephemeris** (Astrodienst AG). Swiss Ephemeris is dual-licensed under AGPL-3.0 or a [Professional License](https://www.astro.com/swisseph/swephinfo_e.htm). This project uses the AGPL option; downstream proprietary services must not link pyswisseph directly — consume this API over HTTP instead.
