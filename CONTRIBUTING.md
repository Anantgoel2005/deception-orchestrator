# Contributing

Contributions should preserve the separation between the hosted control plane and the explicitly enabled local decoy lab.

## Local validation

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip check
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
npm audit --omit=dev --audit-level=high
```

Production configuration:

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
```

Never commit `.env` files, real credentials, live canary tokens, attacker data, or identifiable production telemetry. Tests and documentation must use RFC 5737 TEST-NET addresses and reserved example domains.
