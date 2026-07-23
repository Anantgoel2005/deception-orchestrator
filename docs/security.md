# Security and responsible use

Deception Orchestrator is designed for owned lab networks and defensive demonstrations. It does not execute captured commands, block traffic, or expose decoy services from the production control plane.

- Production startup rejects missing admin password hashes, weak secrets, and non-HTTPS public URLs.
- Dashboard mutations require an authenticated HttpOnly session plus a matching CSRF token.
- URL canary callbacks record only the source address, bounded user agent, and request path. The token is one-time.
- The Docker socket is absent from the base and production Compose files. It is available only through `docker-compose.lab.yml`.
- Use TEST-NET source addresses in the bundled scenario. Do not identify or target real third parties.

For a public deployment, place the server behind the supplied Caddy configuration, keep the OS patched, restrict SSH administration, retain database backups, and rotate the admin password and application secret if access is suspected.
