# Deployment notes

The production Compose overlay starts PostgreSQL, Redis, FastAPI, Next.js, a non-decoy worker, and Caddy. DNS must resolve `DOMAIN` to the server before Caddy can obtain TLS certificates.

Required production values: `DOMAIN`, `APP_BASE_URL`, `CANARY_BASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD_HASH`. `APP_BASE_URL` and `CANARY_BASE_URL` must use the same HTTPS hostname unless a deliberate reverse-proxy configuration is added.

Back up the PostgreSQL volume before upgrades. Apply application upgrades with `docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build`; the API runs Alembic migrations before serving traffic. The production overlay deliberately does not expose database, Redis, backend, or Docker socket ports.
