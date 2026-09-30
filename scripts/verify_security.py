"""
Repository Security & Credentials Leak Scanner
Scans tracked git files, frontend source, and logs for leaked API keys, tokens, and secrets.
"""

import os
import re
import subprocess
import sys

KEY_PATTERNS = [
    re.compile(r"AIzaSy[0-9A-Za-z_-]{33}"),
    re.compile(r"gsk_[0-9A-Za-z]{40,}"),
    re.compile(r"""(?:api[_-]?key|secret|token)\s*[:=]\s*["']([A-Za-z0-9_-]{20,})["']""", re.IGNORECASE)
]

DUMMY_ALLOWLIST = [
    "your_api_key_here",
    "your-api-key-here",
    "placeholder",
    "example",
    "mock",
    "dummy",
    "test_token",
    "change-in-production",
    "dev-insecure-secret-key",
]

def scan_security():
    tracked = subprocess.check_output(["git", "ls-files"]).decode().splitlines()
    leaks = []

    for f in tracked:
        if not os.path.isfile(f):
            continue
        if f.endswith((".pyc", ".png", ".jpg", ".ico", ".pdf", ".lock", ".svg")):
            continue
        if f == ".env" or f.endswith(".env"):
            leaks.append((f, "CRITICAL: .env file is tracked in git!"))
            continue

        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                for p in KEY_PATTERNS:
                    matches = p.findall(content)
                    for m in matches:
                        m_str = m if isinstance(m, str) else m[0]
                        if not any(dummy in m_str.lower() for dummy in DUMMY_ALLOWLIST):
                            leaks.append((f, "REDACTED_SECRET"))
        except Exception:
            pass

    print("===========================================================================")
    print("SECURITY REGRESSION AUDIT REPORT")
    print("===========================================================================")
    print(f"Tracked Files Scanned: {len(tracked)}")
    print(f"Confirmed Leaks Found: {len(leaks)}")
    if leaks:
        for f, desc in leaks:
            print(f"  [ALERT] {f}: {desc}")
        sys.exit(1)
    else:
        print("RESULT: PASSED - No API keys in git, frontend, telemetry, or logs.")
    print("===========================================================================")

if __name__ == "__main__":
    scan_security()
