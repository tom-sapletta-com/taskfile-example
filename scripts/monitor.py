#!/usr/bin/env python3
"""Monitoring script — checks health of all services and reports status.

Called via: @fn monitor
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error


def main():
    domain_web = os.environ.get("DOMAIN_WEB", "localhost:8000")
    domain_landing = os.environ.get("DOMAIN_LANDING", "localhost:3000")

    endpoints = [
        {"name": "Web App (health)", "url": f"http://{domain_web}/health"},
        {"name": "Web App (API)", "url": f"http://{domain_web}/api/v1/status"},
        {"name": "Landing Page", "url": f"http://{domain_landing}"},
    ]

    print("=" * 60)
    print(f"  📊 Monitoring Report — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_ok = True
    results = []

    for ep in endpoints:
        status, latency, detail = check_endpoint(ep["url"])
        icon = "✅" if status else "❌"
        lat_str = f"{latency:.0f}ms" if latency else "N/A"
        print(f"  {icon} {ep['name']:30s} {lat_str:>8s}  {detail}")
        results.append({
            "name": ep["name"],
            "url": ep["url"],
            "ok": status,
            "latency_ms": latency,
            "detail": detail,
        })
        if not status:
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("  🟢 All services healthy")
    else:
        print("  🔴 Some services are DOWN")

    # Send alert if something is down
    if not all_ok:
        webhook = os.environ.get("SLACK_WEBHOOK", "")
        if webhook:
            failed = [r for r in results if not r["ok"]]
            msg = f"🔴 Monitor alert: {len(failed)} service(s) down\n"
            for f in failed:
                msg += f"  • {f['name']}: {f['detail']}\n"
            try:
                data = json.dumps({"text": msg}).encode()
                req = urllib.request.Request(
                    webhook, data=data,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req)
            except Exception as e:
                print(f"  ⚠️  Failed to send alert: {e}")

    sys.exit(0 if all_ok else 1)


def check_endpoint(url: str, timeout: int = 10) -> tuple[bool, float | None, str]:
    """Check a single endpoint. Returns (ok, latency_ms, detail)."""
    try:
        start = time.time()
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        latency = (time.time() - start) * 1000
        code = resp.getcode()
        if code == 200:
            return True, latency, f"HTTP {code}"
        else:
            return False, latency, f"HTTP {code}"
    except urllib.error.HTTPError as e:
        return False, None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, None, f"Connection failed: {e.reason}"
    except Exception as e:
        return False, None, str(e)


if __name__ == "__main__":
    main()
