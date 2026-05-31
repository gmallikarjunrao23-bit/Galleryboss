#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║          K4RTHIK PORT SCANNER — ULTRA PRO MAX           ║
# ║          Professional Recon & Vulnerability Tool        ║
# ║                     v2.0  |  2025                       ║
# ╚══════════════════════════════════════════════════════════╝

import socket
import subprocess
import struct
import threading
import time
import sys
import os
import json
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError

# ══════════════════════════════════════
#              COLORS
# ══════════════════════════════════════
class C:
    RED      = '\033[91m'
    GREEN    = '\033[92m'
    YELLOW   = '\033[93m'
    BLUE     = '\033[94m'
    MAGENTA  = '\033[95m'
    CYAN     = '\033[96m'
    WHITE    = '\033[97m'
    ORANGE   = '\033[38;5;208m'
    PINK     = '\033[38;5;213m'
    LGREEN   = '\033[38;5;118m'
    GOLD     = '\033[38;5;220m'
    BOLD     = '\033[1m'
    DIM      = '\033[2m'
    ITALIC   = '\033[3m'
    UNDER    = '\033[4m'
    BLINK    = '\033[5m'
    RESET    = '\033[0m'
    BG_BLACK = '\033[40m'
    BG_RED   = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_DARK  = '\033[48;5;232m'

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

# ══════════════════════════════════════
#     VULNERABILITY DATABASE
# ══════════════════════════════════════
VULN_DB = {
    21:   {"risk": "HIGH",   "cve": "CVE-2011-2523", "desc": "FTP Anonymous login / ProFTPD backdoor"},
    22:   {"risk": "MEDIUM", "cve": "CVE-2023-38408", "desc": "SSH - Check version, possible brute-force"},
    23:   {"risk": "CRITICAL","cve": "CVE-2020-10188","desc": "Telnet - Plaintext credentials, STOP USING"},
    25:   {"risk": "MEDIUM", "cve": "CVE-2020-7247",  "desc": "SMTP - Open relay / mail spoofing risk"},
    53:   {"risk": "MEDIUM", "cve": "CVE-2020-1350",  "desc": "DNS - Zone transfer / amplification attack"},
    80:   {"risk": "LOW",    "cve": "CVE-2021-41773", "desc": "HTTP - Path traversal, check for CVEs"},
    110:  {"risk": "MEDIUM", "cve": "CVE-2019-19844",  "desc": "POP3 - Cleartext auth possible"},
    135:  {"risk": "HIGH",   "cve": "CVE-2003-0352",  "desc": "RPC - MS Blaster worm vector"},
    139:  {"risk": "HIGH",   "cve": "CVE-2017-0143",  "desc": "NetBIOS - EternalBlue (SMB)"},
    143:  {"risk": "LOW",    "cve": "CVE-2021-38371",  "desc": "IMAP - Check TLS enforcement"},
    443:  {"risk": "LOW",    "cve": "CVE-2022-0778",  "desc": "HTTPS - Check TLS version & cert"},
    445:  {"risk": "CRITICAL","cve": "CVE-2017-0144",  "desc": "SMB - EternalBlue / WannaCry vector!"},
    1433: {"risk": "HIGH",   "cve": "CVE-2020-0618",  "desc": "MSSQL - RCE via stored procedures"},
    1521: {"risk": "HIGH",   "cve": "CVE-2012-1675",  "desc": "Oracle DB - TNS Poison attack"},
    2375: {"risk": "CRITICAL","cve": "CVE-2019-5736",  "desc": "Docker API EXPOSED! Full RCE risk"},
    3306: {"risk": "HIGH",   "cve": "CVE-2016-6662",  "desc": "MySQL - Config file overwrite RCE"},
    3389: {"risk": "CRITICAL","cve": "CVE-2019-0708",  "desc": "RDP - BlueKeep! Patch immediately"},
    4444: {"risk": "CRITICAL","cve": "N/A",            "desc": "Metasploit default listener port!"},
    5432: {"risk": "MEDIUM", "cve": "CVE-2019-10164", "desc": "PostgreSQL - Stack overflow vuln"},
    5900: {"risk": "HIGH",   "cve": "CVE-2015-5239",  "desc": "VNC - Brute-forceable, often no auth"},
    6379: {"risk": "CRITICAL","cve": "CVE-2022-0543",  "desc": "Redis EXPOSED! No auth by default"},
    8080: {"risk": "LOW",    "cve": "CVE-2021-44228",  "desc": "HTTP-Alt - Check Log4Shell if Java"},
    8443: {"risk": "LOW",    "cve": "CVE-2021-40438",  "desc": "HTTPS-Alt - mod_proxy SSRF risk"},
    9200: {"risk": "HIGH",   "cve": "CVE-2021-22145",  "desc": "Elasticsearch EXPOSED! No auth"},
    27017:{"risk": "CRITICAL","cve": "CVE-2019-2389",  "desc": "MongoDB EXPOSED! No auth by default"},
}

RISK_COLOR = {
    "CRITICAL": C.RED + C.BOLD,
    "HIGH":     C.ORANGE,
    "MEDIUM":   C.YELLOW,
    "LOW":      C.GREEN,
    "INFO":     C.CYAN,
}

RISK_ICON = {
    "CRITICAL": "💀",
    "HIGH":     "🔴",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
    "INFO":     "ℹ️ ",
}

# ══════════════════════════════════════
#     COMMON PORTS (Choice 4)
# ══════════════════════════════════════
COMMON_PORTS = [
    20,21,22,23,25,53,67,68,69,80,110,119,123,135,137,
    138,139,143,161,194,389,443,445,465,514,515,587,631,
    993,995,1080,1194,1433,1521,1723,2375,2376,3306,3389,
    4444,5432,5900,5985,6379,8080,8443,8888,9200,9300,
    10000,27017,27018,50000
]

# ══════════════════════════════════════
#        TTL-BASED OS DETECTION
# ══════════════════════════════════════
def detect_os_ttl(ip):
    """Detect OS based on TTL from ping response"""
    try:
        if os.name == 'nt':
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip],
                                    capture_output=True, text=True, timeout=3)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, text=True, timeout=3)
        
        output = result.stdout
        ttl_match = re.search(r'ttl[=\s](\d+)', output, re.IGNORECASE)
        if ttl_match:
            ttl = int(ttl_match.group(1))
            if ttl <= 64:
                return f"Linux/Unix (TTL={ttl})", "🐧"
            elif ttl <= 128:
                return f"Windows (TTL={ttl})", "🪟"
            else:
                return f"Network Device (TTL={ttl})", "🌐"
    except:
        pass
    return "Unknown", "❓"

# ══════════════════════════════════════
#        HOST ALIVE CHECK
# ══════════════════════════════════════
def is_host_alive(ip):
    """Ping check — returns True if host responds"""
    try:
        if os.name == 'nt':
            result = subprocess.run(['ping', '-n', '1', '-w', '1500', ip],
                                    capture_output=True, timeout=4)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '2', ip],
                                    capture_output=True, timeout=4)
        return result.returncode == 0
    except:
        return False

# ══════════════════════════════════════
#        GEOLOCATION LOOKUP
# ══════════════════════════════════════
def geolocate(ip):
    """Fetch geolocation from ip-api.com"""
    try:
        # Skip private IPs
        if ipaddress.ip_address(ip).is_private:
            return {"city":"Local Network","country":"LAN","isp":"Private","org":"Private","lat":0,"lon":0}
        url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,lat,lon,as"
        with urlopen(url, timeout=4) as r:
            data = json.loads(r.read().decode())
            if data.get("status") == "success":
                return data
    except:
        pass
    return {}

# ══════════════════════════════════════
#        BANNER GRABBING (Enhanced)
# ══════════════════════════════════════
HTTP_PROBES = {
    80:   b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n",
    8080: b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n",
    8443: b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n",
    443:  b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n",
    21:   None,  # FTP sends banner on connect
    22:   None,  # SSH sends banner on connect
    25:   None,  # SMTP sends banner on connect
    23:   None,  # Telnet
}

def grab_banner(sock, port):
    try:
        probe = HTTP_PROBES.get(port, b"\r\n")
        if probe:
            sock.send(probe)
        data = sock.recv(1024).decode('utf-8', errors='ignore').strip()
        lines = [l.strip() for l in data.split('\n') if l.strip()]
        return ' | '.join(lines[:2])[:80] if lines else ""
    except:
        return ""

# ══════════════════════════════════════
#        GLOBALS
# ══════════════════════════════════════
results = []
lock    = threading.Lock()
scanned = 0
THREADS = 100
total_ports = 0

# ══════════════════════════════════════
#        BANNER / INTRO
# ══════════════════════════════════════
def type_print(text, delay=0.012, color=""):
    """Typewriter effect"""
    for ch in text:
        print(color + ch, end='', flush=True)
        time.sleep(delay)
    print(C.RESET)

def banner():
    clear()
    art = f"""
{C.GREEN}{C.BOLD}
██╗  ██╗ █████╗ ██████╗ ████████╗██╗  ██╗██╗██╗  ██╗
██║ ██╔╝██╔══██╗██╔══██╗╚══██╔══╝██║  ██║██║██║ ██╔╝
█████╔╝ ███████║██████╔╝   ██║   ███████║██║█████╔╝
██╔═██╗ ██╔══██║██╔══██╗   ██║   ██╔══██║██║██╔═██╗
██║  ██╗██║  ██║██║  ██║   ██║   ██║  ██║██║██║  ██╗
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
{C.RESET}"""
    print(art)
    print(f"{C.GREEN}{'═'*65}{C.RESET}")
    print(f"{C.CYAN}  ⚡ ULTRA PRO MAX Port Scanner  {C.DIM}|{C.RESET}{C.CYAN}  v2.0  {C.DIM}|{C.RESET}{C.GOLD}  by Karthik 🔥{C.RESET}")
    print(f"{C.DIM}  OS Detection • Geo Lookup • CVE Hints • HTML Report • CIDR{C.RESET}")
    print(f"{C.GREEN}{'═'*65}{C.RESET}\n")

# ══════════════════════════════════════
#        PROGRESS BAR
# ══════════════════════════════════════
def live_progress():
    """Animated live progress bar thread"""
    global scanned, total_ports
    spinner = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
    i = 0
    start = time.time()
    while True:
        with lock:
            done = scanned
        if done >= total_ports:
            break
        pct = done / total_ports if total_ports else 0
        width = 35
        filled = int(width * pct)
        bar = f"{C.GREEN}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.RESET}"
        elapsed = time.time() - start
        eta = (elapsed / pct - elapsed) if pct > 0 else 0
        eta_str = f"ETA {int(eta)}s" if eta < 9999 else "..."
        spin = spinner[i % len(spinner)]
        print(f"\r  {C.CYAN}{spin}{C.RESET} [{bar}] {C.YELLOW}{int(pct*100)}%{C.RESET}  {C.DIM}{done}/{total_ports} ports  {eta_str}{C.RESET}   ", end='', flush=True)
        i += 1
        time.sleep(0.08)
    # Final 100%
    bar = f"{C.GREEN}{'█' * 35}{C.RESET}"
    print(f"\r  {C.GREEN}✔{C.RESET} [{bar}] {C.GREEN}100%{C.RESET}  {C.DIM}{total_ports}/{total_ports} ports  Done!{C.RESET}   ")

# ══════════════════════════════════════
#        PORT SCANNER CORE
# ══════════════════════════════════════
def scan_port(args):
    global scanned
    target, port = args
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((target, port))
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except:
                service = "unknown"
            banner_txt = grab_banner(sock, port)
            vuln = VULN_DB.get(port, {"risk":"INFO","cve":"N/A","desc":"No known CVEs in DB"})
            risk = vuln["risk"]
            rc   = RISK_COLOR.get(risk, C.WHITE)
            icon = RISK_ICON.get(risk, "•")
            with lock:
                results.append({
                    'port':    port,
                    'service': service,
                    'banner':  banner_txt,
                    'risk':    risk,
                    'cve':     vuln["cve"],
                    'desc':    vuln["desc"],
                })
            # Print result ABOVE progress bar
            print(f"\r  {C.GREEN}[+]{C.RESET} {icon} Port {C.BOLD}{C.WHITE}{port:<6}{C.RESET} "
                  f"{C.GREEN}OPEN{C.RESET}  {C.CYAN}{service:<12}{C.RESET} "
                  f"{rc}[{risk}]{C.RESET}  {C.DIM}{banner_txt[:35]}{C.RESET}",
                  flush=True)
        sock.close()
    except:
        pass
    finally:
        with lock:
            scanned += 1

# ══════════════════════════════════════
#        HTML REPORT GENERATOR
# ══════════════════════════════════════
def generate_html_report(target, ip, geo, os_guess, scan_results, elapsed, ports_scanned):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    risk_colors_html = {
        "CRITICAL": "#ff2244",
        "HIGH":     "#ff6600",
        "MEDIUM":   "#ffcc00",
        "LOW":      "#44ff88",
        "INFO":     "#00ccff",
    }

    rows = ""
    for r in sorted(scan_results, key=lambda x: x['port']):
        rc = risk_colors_html.get(r['risk'], '#fff')
        rows += f"""
        <tr>
          <td><b>{r['port']}</b></td>
          <td>{r['service']}</td>
          <td><span class="badge" style="background:{rc};color:#000">{r['risk']}</span></td>
          <td><code>{r['cve']}</code></td>
          <td>{r['desc']}</td>
          <td class="banner">{r['banner'] or '—'}</td>
        </tr>"""

    geo_html = ""
    if geo:
        geo_html = f"""
        <div class="geo-box">
          🌍 <b>{geo.get('city','?')}, {geo.get('country','?')}</b> &nbsp;|&nbsp;
          ISP: <b>{geo.get('isp','?')}</b> &nbsp;|&nbsp;
          ORG: <b>{geo.get('org','?')}</b>
        </div>"""

    critical_count = sum(1 for r in scan_results if r['risk'] == 'CRITICAL')
    high_count     = sum(1 for r in scan_results if r['risk'] == 'HIGH')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>K4RTHIK Scanner — {target}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@400;600;700&display=swap');
  :root {{
    --bg: #050a0f;
    --card: #0d1117;
    --border: #1a2a1a;
    --green: #00ff88;
    --cyan: #00ccff;
    --red: #ff2244;
    --orange: #ff6600;
    --yellow: #ffcc00;
    --dim: #445544;
    --text: #ccffcc;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh;
    padding: 2rem;
  }}
  body::before {{
    content: '';
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at 20% 0%, rgba(0,255,136,0.04) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 100%, rgba(0,204,255,0.03) 0%, transparent 60%);
    pointer-events: none;
  }}
  header {{
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }}
  header h1 {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    color: var(--green);
    letter-spacing: 4px;
    text-transform: uppercase;
    text-shadow: 0 0 20px rgba(0,255,136,0.4);
  }}
  header p {{ color: var(--dim); font-size: 0.9rem; margin-top: 0.4rem; font-family: 'JetBrains Mono', monospace; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .stat-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    position: relative;
    overflow: hidden;
  }}
  .stat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--green), var(--cyan));
  }}
  .stat-card .label {{ font-size: 0.75rem; color: var(--dim); text-transform: uppercase; letter-spacing: 2px; }}
  .stat-card .value {{ font-size: 2rem; font-weight: 700; color: var(--green); font-family: 'JetBrains Mono', monospace; margin-top: 0.3rem; }}
  .stat-card.red .value {{ color: var(--red); }}
  .stat-card.orange .value {{ color: var(--orange); }}
  .stat-card.cyan .value {{ color: var(--cyan); }}
  .geo-box {{
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
    padding: 0.8rem 1.2rem;
    border-radius: 6px;
    margin-bottom: 2rem;
    font-size: 0.95rem;
    color: #aaccaa;
  }}
  .target-info {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }}
  .target-info .field {{ flex: 1; min-width: 150px; }}
  .target-info .field label {{ font-size: 0.7rem; color: var(--dim); text-transform: uppercase; letter-spacing: 2px; }}
  .target-info .field span {{ display: block; font-family: 'JetBrains Mono', monospace; color: var(--cyan); font-size: 1rem; margin-top: 0.2rem; }}
  .alert {{
    background: rgba(255,34,68,0.08);
    border: 1px solid rgba(255,34,68,0.3);
    border-left: 4px solid var(--red);
    padding: 1rem 1.5rem;
    border-radius: 6px;
    margin-bottom: 2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #ff8899;
  }}
  .alert strong {{ color: var(--red); }}
  h2 {{
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--green);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}
  h2::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    font-size: 0.9rem;
  }}
  th {{
    background: rgba(0,255,136,0.06);
    padding: 0.8rem 1rem;
    text-align: left;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--green);
    border-bottom: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
  }}
  td {{
    padding: 0.8rem 1rem;
    border-bottom: 1px solid rgba(26,42,26,0.5);
    color: #aabbaa;
    vertical-align: middle;
  }}
  tr:hover td {{ background: rgba(0,255,136,0.02); }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 3px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    font-family: 'JetBrains Mono', monospace;
  }}
  code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--yellow);
    background: rgba(255,204,0,0.07);
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
  }}
  .banner {{ color: #667766; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; word-break: break-all; }}
  .no-results {{
    text-align: center;
    padding: 3rem;
    color: var(--dim);
    font-family: 'JetBrains Mono', monospace;
  }}
  footer {{
    text-align: center;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    color: var(--dim);
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
  }}
  footer span {{ color: var(--green); }}
</style>
</head>
<body>
<header>
  <h1>⚡ K4RTHIK PORT SCANNER — ULTRA PRO MAX</h1>
  <p>Professional Recon & Vulnerability Assessment Report</p>
  <p style="margin-top:0.3rem">{ts}</p>
</header>

<div class="target-info">
  <div class="field"><label>Target</label><span>{target}</span></div>
  <div class="field"><label>Resolved IP</label><span>{ip}</span></div>
  <div class="field"><label>OS Guess</label><span>{os_guess}</span></div>
  <div class="field"><label>Ports Scanned</label><span>{ports_scanned}</span></div>
  <div class="field"><label>Time Taken</label><span>{elapsed}s</span></div>
  <div class="field"><label>Open Ports</label><span>{len(scan_results)}</span></div>
</div>

{geo_html}

<div class="grid">
  <div class="stat-card red">
    <div class="label">Critical</div>
    <div class="value">{critical_count}</div>
  </div>
  <div class="stat-card orange">
    <div class="label">High Risk</div>
    <div class="value">{high_count}</div>
  </div>
  <div class="stat-card cyan">
    <div class="label">Open Ports</div>
    <div class="value">{len(scan_results)}</div>
  </div>
  <div class="stat-card">
    <div class="label">Scanned</div>
    <div class="value" style="font-size:1.5rem">{ports_scanned}</div>
  </div>
</div>
"""
    if critical_count > 0:
        html += f"""
<div class="alert">
  <strong>⚠️  CRITICAL VULNERABILITIES DETECTED!</strong><br>
  {critical_count} critical risk port(s) found. Immediate action required.
  Common exploits may be actively targeting these services.
</div>
"""
    html += f"""
<h2>📋 Port Scan Results</h2>
"""
    if scan_results:
        html += f"""
<table>
  <thead>
    <tr>
      <th>Port</th><th>Service</th><th>Risk</th><th>CVE</th><th>Description</th><th>Banner</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""
    else:
        html += '<div class="no-results">🔒 No open ports found — host may be firewalled.</div>'

    html += f"""
<footer>
  Generated by <span>K4RTHIK SCANNER v2.0</span> — For authorized testing only.<br>
  Always get permission before scanning. Use responsibly.
</footer>
</body>
</html>"""
    return html

# ══════════════════════════════════════
#        INPUT / CONFIGURATION
# ══════════════════════════════════════
def get_target():
    print(f"{C.CYAN}  ┌──────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}  │          TARGET CONFIGURATION            │{C.RESET}")
    print(f"{C.CYAN}  └──────────────────────────────────────────┘{C.RESET}\n")

    target = input(f"  {C.GREEN}[?]{C.RESET} Enter target IP / Domain / CIDR: {C.WHITE}").strip()
    print(f"{C.RESET}", end="")

    # CIDR detection
    cidr_mode = False
    cidr_hosts = []
    if '/' in target:
        try:
            net = ipaddress.ip_network(target, strict=False)
            cidr_hosts = [str(h) for h in net.hosts()]
            cidr_mode = True
            print(f"\n  {C.YELLOW}[*]{C.RESET} CIDR detected — {C.WHITE}{len(cidr_hosts)}{C.RESET} hosts to check")
        except:
            print(f"  {C.RED}[!]{C.RESET} Invalid CIDR range, treating as hostname")
            cidr_mode = False

    print(f"\n  {C.GREEN}[?]{C.RESET} Select port range:")
    print(f"  {C.YELLOW}  [1]{C.RESET} Quick scan     (1–1000)")
    print(f"  {C.YELLOW}  [2]{C.RESET} Full scan      (1–10000)")
    print(f"  {C.YELLOW}  [3]{C.RESET} Custom range")
    print(f"  {C.YELLOW}  [4]{C.RESET} Common ports   ({len(COMMON_PORTS)} ports)")
    print(f"  {C.YELLOW}  [5]{C.RESET} Top 100 ports  (curated)")

    choice = input(f"\n  {C.GREEN}[?]{C.RESET} Choice: {C.WHITE}").strip()
    print(f"{C.RESET}", end="")

    TOP_100 = [
        21,22,23,25,53,80,110,111,135,139,143,443,445,
        993,995,1723,3306,3389,5900,8080,8443,8888,27017,
        6379,5432,1433,1521,2375,9200,4444,5985,10000,
        50000,2049,873,512,513,514,548,631,5800,5801,
        6000,6001,6002,7001,7002,8000,8001,8008,8009,
        8080,8081,8082,8443,9000,9001,9090,9091,9443,
        9999,10001,11211,15672,16379,25565,27015,28017,
        32400,49152,50070,51820,55443,60000,
    ]

    if choice == "1":
        ports = list(range(1, 1001))
    elif choice == "2":
        ports = list(range(1, 10001))
    elif choice == "3":
        s = int(input(f"  {C.GREEN}[?]{C.RESET} Start port: "))
        e = int(input(f"  {C.GREEN}[?]{C.RESET} End port:   "))
        ports = list(range(s, e + 1))
    elif choice == "4":
        ports = COMMON_PORTS
    elif choice == "5":
        ports = sorted(set(TOP_100))
    else:
        ports = list(range(1, 1001))

    print(f"\n  {C.GREEN}[?]{C.RESET} Scan speed:")
    print(f"  {C.YELLOW}  [1]{C.RESET} Stealth    (50 threads)   — low noise")
    print(f"  {C.YELLOW}  [2]{C.RESET} Normal     (100 threads)  — balanced")
    print(f"  {C.YELLOW}  [3]{C.RESET} Aggressive (200 threads)  — fast & loud")
    print(f"  {C.YELLOW}  [4]{C.RESET} Turbo      (500 threads)  — maximum speed ⚡")

    speed = input(f"\n  {C.GREEN}[?]{C.RESET} Choice: {C.WHITE}").strip()
    print(f"{C.RESET}", end="")

    global THREADS
    THREADS = {
        "1": 50, "2": 100, "3": 200, "4": 500
    }.get(speed, 100)

    return target, ports, cidr_mode, cidr_hosts

# ══════════════════════════════════════
#        MAIN SCAN RUNNER
# ══════════════════════════════════════
def run_scan(target, ports, show_header=True):
    global scanned, results, total_ports
    scanned      = 0
    results      = []
    total_ports  = len(ports)

    # Resolve hostname
    try:
        ip = socket.gethostbyname(target)
    except:
        print(f"\n  {C.RED}[!]{C.RESET} Could not resolve: {C.WHITE}{target}{C.RESET}")
        return None, None

    if show_header:
        print(f"\n{C.GREEN}{'═'*65}{C.RESET}")
        print(f"  {C.CYAN}[*]{C.RESET} Target  : {C.WHITE}{C.BOLD}{target}{C.RESET}")
        print(f"  {C.CYAN}[*]{C.RESET} IP      : {C.WHITE}{ip}{C.RESET}")

        # Host alive check
        print(f"  {C.CYAN}[*]{C.RESET} Checking host... ", end='', flush=True)
        alive = is_host_alive(ip)
        if alive:
            print(f"{C.GREEN}✔ Online{C.RESET}")
        else:
            print(f"{C.YELLOW}⚠  No ping response (may be firewalled, continuing...){C.RESET}")

        # OS detection
        print(f"  {C.CYAN}[*]{C.RESET} OS Detect... ", end='', flush=True)
        os_guess, os_icon = detect_os_ttl(ip)
        print(f"{C.WHITE}{os_icon} {os_guess}{C.RESET}")

        # Geo lookup
        print(f"  {C.CYAN}[*]{C.RESET} Geolocation... ", end='', flush=True)
        geo = geolocate(ip)
        if geo:
            print(f"{C.WHITE}🌍 {geo.get('city','?')}, {geo.get('country','?')}  —  {geo.get('isp','?')}{C.RESET}")
        else:
            print(f"{C.DIM}unavailable (private IP or offline){C.RESET}")

        print(f"  {C.CYAN}[*]{C.RESET} Ports   : {C.WHITE}{total_ports} ports{C.RESET}")
        print(f"  {C.CYAN}[*]{C.RESET} Threads : {C.WHITE}{THREADS}{C.RESET}")
        print(f"{C.GREEN}{'═'*65}{C.RESET}\n")
    else:
        geo = {}
        os_guess = "?"
        os_icon  = "❓"

    start = time.time()
    print(f"  {C.YELLOW}[~]{C.RESET} Scanning in progress...\n")

    # Launch progress bar thread
    prog_thread = threading.Thread(target=live_progress, daemon=True)
    prog_thread.start()

    args = [(ip, port) for port in ports]
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        executor.map(scan_port, args)

    prog_thread.join(timeout=3)
    elapsed = round(time.time() - start, 2)

    # ── FINAL REPORT ──
    print(f"\n{C.GREEN}{'═'*65}{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}  SCAN COMPLETE — RESULTS{C.RESET}")
    print(f"{C.GREEN}{'═'*65}{C.RESET}\n")

    if results:
        sorted_results = sorted(results, key=lambda x: x['port'])
        print(f"  {'PORT':<8} {'SERVICE':<14} {'RISK':<10} {'CVE':<18} {'DESC'}")
        print(f"  {'─'*8} {'─'*14} {'─'*10} {'─'*18} {'─'*30}")
        for r in sorted_results:
            rc = RISK_COLOR.get(r['risk'], C.WHITE)
            icon = RISK_ICON.get(r['risk'], '•')
            print(f"  {C.WHITE}{r['port']:<8}{C.RESET}"
                  f"{C.CYAN}{r['service']:<14}{C.RESET}"
                  f"{rc}{r['risk']:<10}{C.RESET}"
                  f"{C.YELLOW}{r['cve']:<18}{C.RESET}"
                  f"{C.DIM}{r['desc'][:35]}{C.RESET}")
    else:
        print(f"  {C.YELLOW}[!]{C.RESET} No open ports found — host may be firewalled or down.")

    crit = sum(1 for r in results if r['risk'] == 'CRITICAL')
    high = sum(1 for r in results if r['risk'] == 'HIGH')

    print(f"\n{C.GREEN}{'═'*65}{C.RESET}")
    print(f"  {C.GREEN}[+]{C.RESET} Open ports    : {C.WHITE}{C.BOLD}{len(results)}{C.RESET}")
    print(f"  {C.RED}[!]{C.RESET} Critical      : {C.RED}{C.BOLD}{crit}{C.RESET}")
    print(f"  {C.ORANGE}[!]{C.RESET} High risk     : {C.ORANGE}{high}{C.RESET}")
    print(f"  {C.GREEN}[+]{C.RESET} Total scanned : {C.WHITE}{total_ports}{C.RESET}")
    print(f"  {C.GREEN}[+]{C.RESET} Time taken    : {C.WHITE}{elapsed}s{C.RESET}")
    print(f"{C.GREEN}{'═'*65}{C.RESET}\n")

    if crit > 0:
        print(f"  {C.RED}{C.BOLD}💀 WARNING: {crit} CRITICAL port(s) found! Immediate attention needed!{C.RESET}\n")

    # ── SAVE OPTIONS ──
    print(f"  {C.GREEN}[?]{C.RESET} Export report:")
    print(f"  {C.YELLOW}  [1]{C.RESET} Save as TXT")
    print(f"  {C.YELLOW}  [2]{C.RESET} Save as JSON")
    print(f"  {C.YELLOW}  [3]{C.RESET} Save as HTML {C.CYAN}(premium, browser-ready){C.RESET}")
    print(f"  {C.YELLOW}  [4]{C.RESET} Save ALL (TXT + JSON + HTML)")
    print(f"  {C.YELLOW}  [n]{C.RESET} Skip")

    save = input(f"\n  {C.GREEN}[?]{C.RESET} Choice: ").strip().lower()
    ts_str = int(time.time())
    base   = f"scan_{target.replace('/', '_')}_{ts_str}"

    if save in ('1', '4'):
        fname = f"{base}.txt"
        with open(fname, 'w') as f:
            f.write(f"K4RTHIK PORT SCANNER v2.0 - RESULTS\n")
            f.write(f"Target : {target} ({ip})\n")
            f.write(f"OS     : {os_guess}\n")
            f.write(f"Time   : {elapsed}s\n")
            f.write(f"{'='*60}\n")
            for r in sorted(results, key=lambda x: x['port']):
                f.write(f"[{r['risk']}] Port {r['port']} - {r['service']} | {r['cve']} | {r['desc']} | {r['banner']}\n")
        print(f"  {C.GREEN}[+]{C.RESET} TXT saved  : {C.WHITE}{fname}{C.RESET}")

    if save in ('2', '4'):
        fname = f"{base}.json"
        data  = {
            "target": target, "ip": ip, "os": os_guess,
            "geo": geo, "elapsed": elapsed,
            "open_ports": len(results), "critical": crit, "high": high,
            "results": sorted(results, key=lambda x: x['port'])
        }
        with open(fname, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  {C.GREEN}[+]{C.RESET} JSON saved : {C.WHITE}{fname}{C.RESET}")

    if save in ('3', '4'):
        fname  = f"{base}.html"
        html   = generate_html_report(target, ip, geo, f"{os_icon} {os_guess}",
                                       results, elapsed, total_ports)
        with open(fname, 'w') as f:
            f.write(html)
        print(f"  {C.GREEN}[+]{C.RESET} HTML saved : {C.WHITE}{fname}{C.RESET}")
        print(f"  {C.CYAN}[*]{C.RESET} Open in browser: {C.UNDERLINE if hasattr(C,'UNDERLINE') else ''}{fname}{C.RESET}")

    print()
    return ip, geo

# ══════════════════════════════════════
#        CIDR SCAN MODE
# ══════════════════════════════════════
def run_cidr_scan(hosts, ports):
    alive_hosts = []
    print(f"\n  {C.YELLOW}[~]{C.RESET} Checking which hosts are alive...\n")
    for h in hosts:
        a = is_host_alive(h)
        icon = f"{C.GREEN}✔ ALIVE{C.RESET}" if a else f"{C.DIM}✗ down{C.RESET}"
        print(f"  {h:<20} {icon}")
        if a:
            alive_hosts.append(h)
        time.sleep(0.05)

    print(f"\n  {C.GREEN}[+]{C.RESET} {len(alive_hosts)}/{len(hosts)} hosts alive\n")

    for h in alive_hosts:
        print(f"\n{C.CYAN}{'─'*65}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}Scanning: {h}{C.RESET}")
        print(f"{C.CYAN}{'─'*65}{C.RESET}")
        run_scan(h, ports, show_header=True)
        time.sleep(0.3)

# ══════════════════════════════════════
#        MAIN
# ══════════════════════════════════════
def main():
    banner()
    try:
        target, ports, cidr_mode, cidr_hosts = get_target()

        if cidr_mode:
            run_cidr_scan(cidr_hosts, ports)
        else:
            run_scan(target, ports)

        again = input(f"  {C.GREEN}[?]{C.RESET} Scan again? (y/n): ").strip().lower()
        if again == 'y':
            main()
        else:
            print(f"\n{C.GREEN}{'═'*65}{C.RESET}")
            print(f"  {C.GOLD}{C.BOLD}  Goodbye buddy ————— Karthik! 💥{C.RESET}")
            print(f"{C.GREEN}{'═'*65}{C.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}[!]{C.RESET} Interrupted by user.\n")
    except Exception as e:
        print(f"\n  {C.RED}[!]{C.RESET} Error: {e}\n")

if __name__ == "__main__":
    main()

