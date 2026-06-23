Swiss Ephemeris ephemeris files are **not** committed to this repository.

## Quick setup

From the repository root:

```bash
# Linux / macOS
./scripts/download-ephe.sh

# Windows PowerShell
./scripts/download-ephe.ps1
```

This downloads `sepl_18.se1` and `semo_18.se1` (planets + Moon, 1800–2399 AD)
from the official Astrodienst FTP mirror into `./ephe/`.

## Docker

The Docker image downloads ephemeris files at build time. For production you can
also mount a host directory:

```yaml
volumes:
  - ./ephe:/app/ephe:ro
```

## Without ephemeris files

Swiss Ephemeris falls back to the built-in **Moshier** analytical ephemeris.
Positions are close but **not** identical to file-based Swiss Ephemeris.
For production alignment with almuten.net / Astro.com, always use `.se1` files.

## License

Ephemeris data files are part of the [Swiss Ephemeris](https://www.astro.com/swisseph/)
distribution. See the Swiss Ephemeris license (AGPL or Professional License).
