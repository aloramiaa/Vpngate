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

def generate_markdown(clean_ips, summary):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"IPs_No_Proxy_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w', encoding="utf-8") as file:
        file.write(f"# Clean VPNGate IPs\n")
        file.write(f"Generated on: {timestamp}\n\n")
        file.write(f"**Summary:** {summary}\n\n")
        file.write("| # | IP Address | Hostname | Type | Country | Provider |\n")
        file.write("|---|------------|----------|------|---------|----------|\n")

        for i, ip_info in enumerate(clean_ips, start=1):
            file.write(f"| {i} | {ip_info['ip']} | {ip_info['hostname']} | {ip_info['type']} | {ip_info['country']} | {ip_info['provider']} |\n")
    print(f"📄 Saved clean IPs to {filename}")
    return filename

def update_readme(latest_md_file):
    with open("README.md", "r+", encoding="utf-8") as readme_file:
        content = readme_file.readlines()
        content.insert(0, f"## Latest VPNGate IP Report: {latest_md_file}\n\n")
        content.insert(1, f"[Link to Report](./{latest_md_file})\n\n")
        readme_file.seek(0)
        readme_file.writelines(content)
    print("📄 Updated README.md with the latest report link.")

def main():
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
                    "country": result.get("isocode", "Unknown"),
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

    # Generate Markdown file
    latest_md_file = generate_markdown(clean_ips, summary)
    
    # Update README with the link to the latest report
    update_readme(latest_md_file)

if __name__ == "__main__":
    main()
