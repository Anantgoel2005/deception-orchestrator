# Deception Orchestrator

Deception Orchestrator is a self-hostable SOC analyst console for demonstrating the detection value of decoys and URL canaries. It turns safe, simulated attack activity into explainable MITRE-tagged events, alerts, and investigations—without requiring an external AI service.

> This is a defensive training and portfolio project. Run decoys only in systems and networks you control. The default hosted deployment exposes only the authenticated dashboard and public URL-canary callback endpoint.

## What works

- Protected, single-admin dashboard with HttpOnly sessions and CSRF protection
- Deterministic offline event scoring, MITRE mapping, alert generation, and alert deduplication
- One-click Demo Lab: a repeatable credential-to-exfiltration chain using TEST-NET addresses
- Analyst event feed, alert triage, and session investigation timeline
- Real one-time URL canaries at `https://your-domain/c/<token>`
- Optional DeepSeek enrichment; the product remains functional without it
- Local-only Docker decoy controls; the production control plane never mounts the Docker socket

## Architecture

```text
Browser ──HTTPS──> Caddy / Next.js ──> FastAPI ──> PostgreSQL
                                      └──> Redis
Public URL canary ───────────────────> FastAPI /c/<token>

Local lab only: FastAPI + worker ──Docker socket──> private decoy containers
```

## Local demo

1. Copy `.env.example` to `.env`, set a unique `SECRET_KEY`, and choose `ADMIN_PASSWORD`.
2. Start the safe control plane:

   ```bash
   docker compose up --build
   ```

3. Open `http://localhost:3000`, sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`, then open **Demo Lab** and run the scenario.
4. The scenario creates events and alerts, then opens the linked investigation automatically.

To enable Docker-managed decoys on a machine you control, explicitly opt in:

```bash
docker compose -f docker-compose.yml -f docker-compose.lab.yml up --build
```

The lab override is the only configuration that mounts the Docker socket. Do not use it on a public control-plane host.

## Hosted control plane

Use a Linux VPS with Docker and a domain whose A/AAAA record points to it.

1. Set `DOMAIN`, `APP_BASE_URL=https://$DOMAIN`, `CANARY_BASE_URL=https://$DOMAIN`, a 32+ character `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD_HASH` in `.env`.
2. Generate the bcrypt hash with `python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your-password'))"` in the backend image or an equivalent trusted environment.
3. Run `docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build`.
4. Verify `https://$DOMAIN/health`, sign in, generate a URL canary, and fetch its copied callback URL once. The pixel request should create a critical alert.

See [deployment notes](docs/deployment.md), [demo script](docs/demo-script.md), and [security notes](docs/security.md).

## API

The protected OpenAPI UI is available at `http://localhost:8000/docs` in local development. Key routes are `POST /api/v1/auth/login`, `POST /api/v1/demo/run`, `GET /api/v1/investigations/{session_id}`, and public `GET /c/{token}`.

## Showcase talking points

- A safe demonstration does not need a live attacker: the scenario runs through the same processing path as telemetry.
- The platform clearly separates local decoy infrastructure from its hosted control plane.
- Every alert contains an explainable score, MITRE context, and a recommended analyst response.
- DeepSeek is the cost-efficient optional enrichment path; offline analysis remains deterministic and testable.
