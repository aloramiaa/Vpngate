import os
import re
import json
import shutil
import requests
from datetime import datetime

API_KEY = '896357-7r961n-0t9072-j922c6'
PCIO_URL = "http://proxycheck.io/v2/{}?key={}&vpn=1&asn=1&risk=1&node=1&inf=1"

CONFIG_DIR = "configs"
FAILED_DIR = os.path.join(CONFIG_DIR, "failed")
os.makedirs(FAILED_DIR, exist_ok=True)

def extract_remote_ip(ovpn_file):
    with open(ovpn_file, 'r') as f:
        for line in f:
            m = re.match(r'^remote\s+([\d\.]+)', line.strip())
            if m:
                return m.group(1)
    return None

def check_ip(ip):
    try:
        url = PCIO_URL.format(ip, API_KEY)
        res = requests.get(url, timeout=5)
        return res.json().get(ip, {})
    except Exception as e:
        print(f"[!] API error for {ip}: {e}")
        return {}

def main():
    summary = {
        "total": 0, "clean": 0, "flagged": 0
    }
    records = []
    files = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.ovpn')]

    for fname in files:
        fpath = os.path.join(CONFIG_DIR, fname)
        ip = extract_remote_ip(fpath)
        summary["total"] += 1

        if not ip:
            print(f"🚫 Could not extract IP from {fname}")
            shutil.move(fpath, os.path.join(FAILED_DIR, fname))
            summary["flagged"] += 1
            continue

        print(f"🔍 Checking {ip} from {fname}")
        data = check_ip(ip)

        record = {
            "file": fname,
            "ip": ip,
            "asn": data.get("asn", "N/A"),
            "provider": data.get("provider", "N/A"),
            "country": data.get("isocode", "N/A"),
            "risk": data.get("risk", "N/A"),
            "type": data.get("type", "N/A"),
            "proxy": data.get("proxy", "N/A")
        }

        try:
            risk_value = int(data.get("risk", 0))
        except ValueError:
            risk_value = 0

        if data.get("proxy") == "yes" or risk_value > 10:
            print(f"🚫 {ip} flagged. Risk {data.get('risk')}")
            shutil.move(fpath, os.path.join(FAILED_DIR, fname))
            summary["flagged"] += 1
        else:
            summary["clean"] += 1

        records.append(record)

    # JSON report (includes all)
    with open("report.json", "w") as f:
        json.dump({"summary": summary, "records": records}, f, indent=2)
    print("📄 Saved report.json")

    # Markdown report (excludes proxy=yes)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🚀 VPNGate Config Report\n")
        f.write(f"_Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        f.write(f"**Summary:** ✅ {summary['clean']} clean | 🚫 {summary['flagged']} flagged | 🔍 {summary['total']} total\n\n")
        f.write(f"## Details (excluding detected proxies)\n")
        f.write(f"| File | IP | ASN | Provider | Country | Type | Risk | Proxy |\n")
        f.write(f"|------|----|-----|----------|---------|------|------|-------|\n")
        for r in records:
            if r["proxy"] == "yes":
                continue  # skip proxies
            f.write(f"| {r['file']} | {r['ip']} | {r['asn']} | {r['provider']} | {r['country']} | {r['type']} | {r['risk']} | {r['proxy']} |\n")
        f.write("\n")
        f.write(f"**Full JSON:** See [report.json](./report.json)\n")

    print("✅ README.md updated without proxy=yes entries.")

if __name__ == "__main__":
    main()
