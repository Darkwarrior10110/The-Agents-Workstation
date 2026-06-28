# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email the maintainer or use GitHub's private vulnerability reporting.
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

You should receive an initial response within 48 hours.

## Security Considerations

### API Keys & Secrets

- Never commit `.env` files or hardcode API keys.
- Use `.env.example` as a template; it contains placeholder values only.
- Rotate keys immediately if exposed.
- The LLM Gateway supports multiple provider keys with automatic failover — rotate compromised keys without downtime.

### Generated Code Execution

This workstation generates and executes code via AI agents. Key risks:

- **Generated code runs with the permissions of the host process.** Run in a sandboxed environment (Docker, VM) for untrusted goals.
- The pre-save validator checks syntax and basic safety, but cannot guarantee generated code is safe.
- The `terminal_agent` executes shell commands — restrict its use in production.

### Network Exposure

- The FastAPI server binds to `0.0.0.0:8000` by default.
- In production, use a reverse proxy (nginx, Caddy) with TLS.
- The WebSocket dashboard (`/api/dashboard/stream`) has no authentication — add auth middleware before exposing publicly.

### Docker

- Mount `.env` as read-only (`:ro`) — already configured in `docker-compose.yml`.
- Do not mount sensitive host directories into the container.
- Use non-root containers in production.

### Dependency Security

- Run `pip audit` regularly to check for known vulnerabilities.
- Pin dependencies in production (`pip freeze > requirements.lock`).
- Bandit scans are included in CI — review reports on every PR.

## Best Practices

- Use environment variables for all secrets.
- Enable HTTPS in production.
- Add authentication to the API and WebSocket endpoints.
- Run agents in isolated containers for untrusted workloads.
- Monitor logs in `storage/logs/` for anomalies.
