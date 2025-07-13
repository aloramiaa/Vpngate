import requests
import csv
import io
import socket
from datetime import datetime

API_KEY = '896357-7r961n-0t9072-j922c6'
VPNGATE_URL = 'http://www.vpngate.net/api/iphone/'
FILTER_COUNTRY = None  # e.g., set to "JP" to only show Japan-based IPs

def fetch_vpngate_csv():
    response = requests.get(VPNGATE_URL)
    response.encoding = 'utf-8'
    csv_data = '\n'.join(response.text.splitlines()[2:])
    return io.StringIO(csv_data)

def check_ip(ip):
    url = f"http://proxycheck.io/v2/{ip}?key={API_KEY}&vpn=1&asn=1&node=1&inf=1"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        return data.get(ip)
    except Exception as e:
        print(f"[!] Error checking IP {ip}: {e}")
        return None

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "N/A"

def generate_markdown(clean_ips, summary, date_str):
    filename = f"IPs_No_Proxy_{date_str}.md"
    with open(filename, 'w', encoding="utf-8") as file:
        file.write(f"# Clean VPNGate IPs\n")
        file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        file.write(f"**Summary:** {summary}\n\n")
        file.write("| # | IP Address | Hostname | Type | Country | Provider |\n")
        file.write("|---|------------|----------|------|---------|----------|\n")

        for i, ip_info in enumerate(clean_ips, start=1):
            file.write(f"| {i} | {ip_info['ip']} | {ip_info['hostname']} | {ip_info['type']} | {ip_info['country']} | {ip_info['provider']} |\n")
    print(f"📄 Saved markdown report to {filename}")

    # also keep a latest.md
    with open("latest.md", "w", encoding="utf-8") as latest:
        latest.write(open(filename, "r", encoding="utf-8").read())
    return filename

def generate_html_index(clean_ips, summary, date_str):
    filename = f"index_{date_str}.html"
    with open(filename, 'w', encoding="utf-8") as file:
        file.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VPNGate Clean IPs - {date_str}</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
</style>
</head>
<body>
<h1>Clean VPNGate IPs</h1>
<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Summary:</strong> {summary}</p>
<table>
<tr><th>#</th><th>IP Address</th><th>Hostname</th><th>Type</th><th>Country</th><th>Provider</th></tr>
""")
        for i, ip_info in enumerate(clean_ips, start=1):
            file.write(f"<tr><td>{i}</td><td>{ip_info['ip']}</td><td>{ip_info['hostname']}</td>"
                       f"<td>{ip_info['type']}</td><td>{ip_info['country']}</td><td>{ip_info['provider']}</td></tr>")
        file.write("""
</table>
</body>
</html>""")
    print(f"🌐 Saved HTML index to {filename}")

    # also keep a latest.html
    with open("latest.html", "w", encoding="utf-8") as latest:
        latest.write(open(filename, "r", encoding="utf-8").read())
    return filename

def update_readme(latest_md_file, latest_html_file):
    lines = [
        f"## Latest VPNGate Reports\n",
        f"- [Markdown Report]({latest_md_file})\n",
        f"- [HTML Index]({latest_html_file})\n\n"
    ]
    # Read existing README if exists
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            old_content = f.readlines()
    except FileNotFoundError:
        old_content = []

    # Write updated content
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(lines + old_content)
    print("✅ Updated README.md with the latest report links.")

def main():
    date_str = datetime.now().strftime('%Y%m%d')
    csv_file = fetch_vpngate_csv()
    reader = csv.reader(csv_file)
    clean_ips = []
    total = proxy = errors = 0

    print("🔍 Starting full scan...\n")

    for row in reader:
        if len(row) < 2:
            continue
        ip = row[1]
        total += 1

        result = check_ip(ip)
        if result:
            if result.get("proxy") == "no":
                country = result.get("isocode", "Unknown")
                if FILTER_COUNTRY and country != FILTER_COUNTRY:
                    continue

                hostname = resolve_hostname(ip)
                ip_info = {
                    "ip": ip,
                    "hostname": hostname,
                    "type": result.get("type", "Unknown"),
                    "country": country,
                    "provider": result.get("provider", "Unknown")
                }
                clean_ips.append(ip_info)
                print(f"[✔] {ip} | {hostname} | {ip_info['type']} | {country}")
            else:
                proxy += 1
                print(f"[✘] {ip} is a proxy")
        else:
            errors += 1
            print(f"[!] {ip} check failed.")

    summary = f"Clean: {len(clean_ips)}, Proxies: {proxy}, Errors: {errors}, Total Checked: {total}"
    print(f"\n✅ Finished. {summary}")

    md_file = generate_markdown(clean_ips, summary, date_str)
    html_file = generate_html_index(clean_ips, summary, date_str)
    update_readme(md_file, html_file)

if __name__ == "__main__":
    main()
