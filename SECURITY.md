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

## Automated scanning (GitHub)

- **CI** (`.github/workflows/ci.yml`) — backend unit/integration tests, frontend
  tests, `pip-audit`, `npm audit` on every push/PR to `main`.
- **CodeQL** — enabled as **Default setup** under **Settings → Code security and
  analysis** (not a custom workflow). Do not add `.github/workflows/codeql.yml`
  while Default setup is on; GitHub rejects duplicate “advanced” SARIF uploads.

To switch to a custom CodeQL workflow instead: disable Default setup in that
settings page, then restore a `codeql.yml` workflow.

Results: [Actions](https://github.com/imrekaposi-elastic/wkpoule/actions) and
[Security](https://github.com/imrekaposi-elastic/wkpoule/security) on GitHub.
