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

## Automated scanning (GitHub Actions)

Every push and pull request to `main` runs workflows under `.github/workflows/`:

- **CI** — backend unit/integration tests, frontend tests, `pip-audit`, `npm audit`
- **CodeQL** — static analysis for Python and TypeScript/JavaScript

Results: [Actions](https://github.com/imrekaposi-elastic/wkpoule/actions) and
[Security](https://github.com/imrekaposi-elastic/wkpoule/security) tabs on GitHub.

If the repo is mirrored to GitLab, `.gitlab-ci.yml` runs SAST, dependency scanning,
and secret detection there as well.
