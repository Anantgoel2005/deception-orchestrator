# Security policy

## Supported version

Security fixes are applied to the latest commit on `main`. This project is a defensive lab and portfolio system; it is not offered as a managed production service.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** button under the repository Security tab. If private reporting is unavailable, open a minimal issue requesting a private contact channel without including vulnerability details. Do not publish exploit details, credentials, canary tokens, or deployment addresses.

Include the affected component, reproduction steps, impact, and any suggested mitigation. You should receive an acknowledgement within seven days. Please allow reasonable time for validation and remediation before public disclosure.

## Security boundary

The hosted control plane and the optional local decoy lab have deliberately different trust boundaries. Review [docs/security.md](docs/security.md) and [docs/architecture.md](docs/architecture.md) before deployment.

Only run decoys on systems and networks you own or are explicitly authorized to test. Never expose the bundled decoy templates directly to the public internet.
