# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Report security issues privately to the repository maintainers (do not open a
public issue for exploitable findings). Include steps to reproduce, impact,
and affected components (API, frontend, OpenShift manifests).

## Automated scanning (GitLab CI)

Every push and merge request runs:

- **SAST** — static analysis of application source code
- **Dependency scanning** — known vulnerabilities in `backend/requirements.txt` and `frontend/package.json`
- **Secret detection** — committed credentials and tokens

Findings appear under **Security & Compliance** in GitLab. Triage and remediate
high/critical items before production releases.
