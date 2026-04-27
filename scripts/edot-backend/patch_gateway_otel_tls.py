#!/usr/bin/env python3
"""Run on the EDOT gateway host. Adds tls.insecure_skip_verify to elasticsearch/otel exporter.

Prefer fixing ECE so the deployment URL is in the certificate SAN. This is a workaround when
the cert is only valid for *.ece.kaposi.net (one label) and the hostname is e.g. o11y.es.ece.kaposi.net.
"""
from pathlib import Path

p = Path("/etc/edot/otel.yml")
t = p.read_text(encoding="utf-8")
if "insecure_skip_verify" in t:
    print("otel.yml already contains insecure_skip_verify; no change")
    raise SystemExit(0)

needle = "    mapping:\n      mode: otel\n"
repl = (
    needle
    + "\n"
    + "    # Workaround: ES HTTPS cert SAN does not match ELASTIC_ENDPOINT hostname.\n"
    + "    # Replace with proper cert / URL in ECE when possible.\n"
    + "    tls:\n"
    + "      insecure_skip_verify: true\n"
)
if needle not in t:
    raise SystemExit(f"expected snippet not found in {p}")
p.write_text(t.replace(needle, repl, 1), encoding="utf-8")
print(f"updated {p}")
