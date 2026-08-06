# Roadmap

The current release is a hardened single-admin portfolio lab. The roadmap below separates credible next steps from features that would only be necessary for organizational deployment.

## Portfolio release

- [x] Fail-closed production configuration and explicit trust boundaries
- [x] Authenticated console with CSRF protection and bounded login throttling
- [x] Non-root application containers and private production data services
- [x] Backend tests, frontend type-check/build, npm audit, CodeQL, and Dependabot
- [ ] Add real dashboard screenshots and a short recorded demo
- [ ] Publish a tagged release with checksums and a reproducible release checklist

## Operational maturity

- [ ] Move distributed rate-limit state to Redis
- [ ] Add append-only analyst audit events for authentication and state changes
- [ ] Add OpenTelemetry traces, structured JSON logs, and service-level metrics
- [ ] Add authenticated collector enrollment and key rotation
- [ ] Add retention jobs and documented restore testing
- [ ] Add Playwright coverage for login, demo execution, alert triage, and canary generation

## Organizational deployment

- [ ] Replace single-admin authentication with OIDC and role-based access control
- [ ] Separate collectors from the control plane with mutually authenticated transport
- [ ] Add SIEM export, webhook signing, and delivery retry semantics
- [ ] Add tenant isolation and per-project retention policies
- [ ] Complete an external threat model and deployment security review

The bundled decoy containers will remain an explicit local-lab feature. Turning them into an internet-facing managed honeypot fleet is outside the intended scope of this repository.
