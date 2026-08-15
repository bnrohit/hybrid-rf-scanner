# Security Policy

## Reporting
Do not open a public issue containing credentials, private sensor data, or a working exploit against a deployed scanner. Report security-sensitive findings privately to the repository owner.

## Deployment defaults
- Keep the API on loopback unless remote access is required.
- Remote bind requires `HYBRID_SCANNER_API_TOKEN`.
- Prefer TLS termination and authentication at a hardened reverse proxy for network deployments.
- Run the scanner as the dedicated non-root `scanner` account.
- Never commit tokens, camera recordings, credentials, or private datasets.
- Treat firmware/profile files and calibration transforms as release-controlled artifacts.

## Dependency hygiene
GitHub CI runs `pip-audit`, and Dependabot is configured for Python dependencies and GitHub Actions.
