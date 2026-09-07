#!/usr/bin/env python3
import os
import sys
import time
import json
import base64
import socket
import subprocess
import tempfile
import signal
import statistics
import threading
import re
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from threading import Lock
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ipaddress

TIMEOUT_PER_URL = 7
MAX_TCP_PING_MS = 700
TCP_PING_TIMEOUT = MAX_TCP_PING_MS / 1100
SPEEDTEST_TIMEOUT = 9

LTE_TIMEOUT_PER_URL = 25
LTE_MAX_TCP_PING_MS = 12000
LTE_TCP_PING_TIMEOUT = LTE_MAX_TCP_PING_MS / 9000
LTE_SPEEDTEST_TIMEOUT = 40

OPERATOR_FILES = {
    "MTS": os.environ.get("MTS_CIDR_FILE", "mts_cidr.txt"),
    "Beeline": os.environ.get("BEELINE_CIDR_FILE", "beeline_cidr.txt"),
    "MegafonYota": os.environ.get("MEGAFON_CIDR_FILE", "megafon_cidr.txt"),
    "Tele2": os.environ.get("TELE2_CIDR_FILE", "tele2_cidr.txt")
}

MIN_SPEED_NORMAL = 100.0      
MIN_SPEED_OPERATOR = 0.0    

SOURCES_LIST_URL = "https://raw.githubusercontent.com/bobrinaw/vlessforu/main/lol"
FETCH_PROXY = os.environ.get("FETCH_PROXY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = "bobrinaw"
REPO_NAME = "vlessforu"
OUTPUT_FILE = "working_configs.txt"
BRANCH = "main"
NOJEKYLL_FILE = ".nojekyll"
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", 7200))
SPEEDTEST_INTERVAL = int(os.environ.get("SPEEDTEST_INTERVAL", 3600))
TEST_URLS = [
    "https://www.gstatic.com/generate_204",
    "https://telegram.org",
    "https://www.instagram.com",
    "https://tiktok.com"
]
SPEEDTEST_URLS = [
    "https://raw.githubusercontent.com/BitDoctor/speed-test-file/refs/heads/master/5mb.txt",
]
BLOCKED_COUNTRIES = {"JP", "VN", "AF", "IR", "TM", "CN", "KR"}
FASTEST_SKIP_COUNTRIES = {"RU", "CA", "UK", "HK", "TW", "ES", "US"}
MIN_SUCCESS = 2
PING_WORKERS = int(os.environ.get("PING_WORKERS", 30))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 7))
FETCH_WORKERS = int(os.environ.get("FETCH_WORKERS", 6))
SPEEDTEST_WORKERS = 2
XRAY_STARTUP_TIMEOUT = 2.5
BLACKLIST_AGE_LIMIT = 5 * 3600
PANEL_TITLE = "Tg: Vlessforu ❤️ FREE"
TG_BOT_LINK = "https://t.me/Vlessforu/95"
WEBPAGE_LINK = "https://t.me/Vlessforu"
EXPIRE_TIMESTAMP = int(datetime(6767, 9, 11).timestamp())
TOTAL_BYTES = 67 * 1024**4
BLACKLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist_local.txt")
CIDR_WHITELIST_FILE = os.environ.get("CIDR_WHITELIST_FILE", "cidr_whitelist.txt")
IP_WHITELIST_FILE = os.environ.get("IP_WHITELIST_FILE", "ips_whitelist.txt")
IP_BLACKLIST_FILE = os.environ.get("IP_BLACKLIST_FILE", "ip_blacklist.txt")
DOMAIN_WHITELIST_FILE = os.environ.get("DOMAIN_WHITELIST_FILE", "white_domens.txt")
DOMAIN_BLACKLIST_FILE = os.environ.get("DOMAIN_BLACKLIST_FILE", "blacklist_domains.txt")
WS_PATCH_BLOCKLIST_FILE = os.environ.get("WS_PATCH_BLOCKLIST_FILE", "ws_patch_blocklist.txt")
YT_CIDR_FILE = os.environ.get("YT_CIDR_FILE", "yt_cidr.txt")
STATIC_HWID = "9dcd98947a040627"

_happ_routing_config = {
    "Name": "Tg: VlessForu  ",
    "GlobalProxy": "true",
    "UseChunkFiles": "true",
    "RemoteDns": "94.140.14.14",
    "DomesticDns": "77.88.8.8",
    "RemoteDNSType": "DoH",
    "RemoteDNSDomain": "https://dns.adguard-dns.com/dns-query",
    "RemoteDNSIP": "8.8.8.8",
    "DomesticDNSType": "DoH",
    "DomesticDNSDomain": "https://77.88.8.8/dns-query",
    "DomesticDNSIP": "77.88.8.8",
    "Geoipurl": "https://sub.vlessfo.ru/vlessforu/geoip.dat",
    "Geositeurl": "https://sub.vlessfo.ru/vlessforu/geosite.dat",
    "LastUpdated": "1786492800",
    "DnsHosts": {
        "lkfl2.nalog.ru": "213.24.64.175",
        "lknpd.nalog.ru": "213.24.64.181"
    },
    "RouteOrder": "block-proxy-direct",
    "DirectSites": [
        "geosite:private",
        "geosite:category-ru",
        "protocol:bittorrent",
        "domain:2gis.ru", "domain:ads.x5.ru", "domain:2gis.com", "domain:aif.ru",
        "domain:aeroflot.ru", "domain:alfabank.ru", "domain:avito.ru", "domain:beeline.ru",
        "domain:burgerkingrus.ru", "domain:dellin.ru", "domain:drive2.ru", "domain:dzen.ru",
        "domain:flypobeda.ru", "domain:forbes.ru", "domain:gazeta.ru", "domain:gazprombank.ru",
        "domain:gismeteo.ru", "domain:gosuslugi.ru", "domain:hh.ru", "domain:kontur.ru",
        "domain:kontur.host", "domain:kp.ru", "domain:kuper.ru", "domain:lenta.ru",
        "domain:mail.ru", "domain:max.ru", "domain:megamarket.ru", "domain:megamarket.tech",
        "domain:megafon.ru", "domain:moex.com", "domain:motivtelecom.ru", "domain:ozon.ru",
        "domain:pervye.ru", "domain:psbank.ru", "domain:rambler.ru", "domain:rambler-co.ru",
        "domain:rbc.ru", "domain:reg.ru", "domain:reviews.2gis.com", "domain:rg.ru",
        "domain:ria.ru", "domain:ruwiki.ru", "domain:rustore.ru", "domain:rutube.ru",
        "domain:rzd.ru", "domain:sirena-travel.ru", "domain:sravni.ru", "domain:t-j.ru",
        "domain:t2.ru", "domain:tank-online.com", "domain:taximaxim.ru", "domain:tbank-online.com", "domain:imgsmail.ru", "domain:ok.ru", "domain:yadro.ru",
        "domain:tildaapi.com", "domain:tns-counter.ru", "domain:trvl.yandex.net", "domain:tutu.ru",
        "domain:vk.com", "domain:vk.ru", "domain:vkvideo.ru", "domain:vtb.ru", "domain:x5.ru",
        "domain:ya.ru", "domain:yandex.ru", "domain:yandex.net", "domain:yandex.com",
    "domain:yastatic.net", "domain:yandexcloud.net", "domain:wildberries.ru", "domain:wbbasket.ru",
        "full:go.yandex", "full:ru.ruwiki.ru", "domain:avito.st", "domain:geobasket.ru", "domain:wb.ru",
        "domain:xn--90acagbhgpca7c8c7f.xn--p1ai", "domain:xn--80ajghhoc2aj1c8b.xn--p1ai",
        "domain:xn--90aivcdt6dxbc.xn--p1ai", "domain:xn--b1aew.xn--p1ai", "domain:oneme.app", "domain:oneme.ru", "domain:mycdn.me", "domain:vkuser.net",
    "domain:yastatic.ru", "domain:yandex.net", "domain:voskhod.ru", "domain:apptracer.ru"
    ],
    "DirectIp": [
        "geoip:private",
        "89.208.85.188"
    ],
    "ProxySites": [
        "geosite:telegram",
    "domain:vlessfo.ru"
    ],
    "ProxyIp": [],
    "BlockSites": [
        "",
    ],
    "BlockIp": [],
    "DomainStrategy": "IPIfNonMatch",
    "FakeDNS": "true"
}

HAPP_THEME_BASE64 = "eyJiYWNrZ3JvdW5kR3JhZGllbnRSb3RhdGlvbkFuZ2xlIjo0NS4wLCJzZXJ2ZXJSb3dCYWNrZ3JvdW5kQ29sb3IiOiIjMUQyQTIwRkYiLCJzdWJzSGVhZGVyQ29sb3IiOiIjMjUzQTI3RkYiLCJwcm9maWxlV2ViUGFnZUljb25Db2xvciI6IiMwMEI4OTRGRiIsInNlbGVjdGVkU2VydmVyUm93Q29sb3IiOiIjMkE0QTMwRkYiLCJkaXNjbG9zdXJlU3ViSGVhZGVyVGV4dENvbG9yIjoiI0Q0RENEQ0ZGIiwiYnV0dG9uVGV4dENvbG9yIjoiI0ZGRkZGRkZGIiwiYnV0dG9uVGltZXJDb2xvciI6IiMwMEI4OTRGRiIsInN1YnNjcmlwdGlvbkluZm9CYWNrZ3JvdW5kQ29sb3IiOiIjMjQyQTI2RkYiLCJiYWNrZ3JvdW5kQ29sb3JzIjpbIiMwQTBBMEEiLCIjMEYwRjBGIiwiIzE0MTQxNCIsIiMxQTFBMUEiLCIjMUYxRjFGIiwiIzI0MjQyNCIsIiMyQTJBMkEiXSwiZGlzY2xvc3VyZUhlYWRlclRleHRDb2xvciI6IiNFOEU4RThGRiIsImJhY2tncm91bmRHcmFkaWVudENvbG9ySW50ZW5zaXR5IjoxLjAsImFkZGl0aW9uYWxPcHRpb25zQnV0dG9uQ29sb3IiOiIjMDBCODk0RkYiLCJidXR0b25JbWFnZVR5cGUiOiJsaWdodCIsInNlcnZlclJvd1N1YlRpdGxlVGV4dENvbG9yIjoiI0E4QjhCOEZGIiwic3VwcG9ydEljb25Db2xvciI6IiMwMEI4OTRGRiIsInRvcEJhckJ1dHRvbnNDb2xvciI6IiNENEQ4RENGQiIsInN1YnNjcmlwdGlvblRyYWZmaWNCYWNrZ3JvdW5kQ29sb3IiOiIjMkE0QTMwRkYiLCJzdWJIZWFkZXJCdXR0b25Db2xvciI6IiMwMEI4OTRGRiIsImJ1dHRvbkNvbG9yIjoiIzJBNEEzMEZGIiwicG93ZXJJY29uQ29sb3IiOiIjMDBCODk0RkYiLCJzdWJzY3JpcHRpb25JbmZvVGV4dENvbG9yIjoiI0Q0RENEQ0ZGIiwic2VydmVyUm93VGl0bGVUZXh0Q29sb3IiOiIjRThFOEU4RkYiLCJiYWNrZ3JvdW5kSW1hZ2VUeXBlIjoic3lzdGVtIiwiZWxsaXBzZUNvbG9ycyI6WyIjMDBCODk0RkYiLCIjMjNDOTVGRkYiLCIjNTBEMzBGRkYiLCIjOERBODhGRkYiXSwic2VydmVyUm93Q2hldnJvbkNvbG9yIjoiIzAwQjg5NEZGIn0="

blacklist_dict = {}
blacklist_lock = Lock()
lte_fail_counts = {}  
country_cache = {}
dns_cache = {}
WHITE_CIDR_LIST = []
WHITE_IP_SET = set()
STATIC_IP_BLACKLIST = []
WHITE_DOMAINS = set()
BLACK_DOMAINS = set()
WS_PATCH_BLOCKLIST = set()
YT_CIDR_LIST = []
OPERATORS_CIDR = {op: [] for op in OPERATOR_FILES}
current_sources = []
sources_lock = Lock()
_black_regex = None
_white_regexes = []

_session = requests.Session()
_session.headers.update({
    "User-Agent": f"Happ/4.1.0/Android/17860741775021899510",
    "X-Device-Locale": "ru",
    "X-Hwid": STATIC_HWID,
    "X-Device-Os": "Android",
    "X-Ver-Os": "16",
    "X-Device-Model": "Samsung",
    "Connection": "close",
})
_retry_strategy = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500])
_adapter = HTTPAdapter(max_retries=_retry_strategy, pool_connections=15, pool_maxsize=15)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)

def resolve_host(host):
    if not host: return None
    try:
        socket.inet_aton(host)
        return host
    except OSError: pass
    if host in dns_cache: return dns_cache[host]
    try:
        ip = socket.gethostbyname(host)
        dns_cache[host] = ip
        return ip
    except socket.gaierror:
        dns_cache[host] = None
        return None

def country_code_to_flag(code):
    if not code or len(code) != 2: return "🐝"
    c = code.upper()
    return chr(ord(c[0]) + 0x1F1A5) + chr(ord(c[1]) + 0x1F1A5)

def _parse_ipapi_com(d):
    if d.get("status") == "success": return d.get("country", ""), d.get("countryCode", "").upper()
    return None

def _parse_ipwho_is(d):
    if d.get("country_code"): return d.get("country", ""), d.get("country_code", "").upper()
    return None

def _parse_freeipapi(d):
    if d.get("countryCode"): return d.get("countryName", ""), d.get("countryCode", "").upper()
    return None

def _parse_country_is(d):
    if d.get("country"): return d.get("country", ""), d.get("country", "").upper()
    return None

def _parse_db_ip(d):
    if d.get("countryCode"): return d.get("countryName", ""), d.get("countryCode", "").upper()
    return None

def get_country(host):
    ip = resolve_host(host) or host
    if not ip: return "", ""
    if ip in country_cache: return country_cache[ip]
    
    providers = [
        (f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", _parse_ipapi_com),
        (f"https://ipwho.is/{ip}", _parse_ipwho_is),
        (f"https://freeipapi.com/api/json/{ip}", _parse_freeipapi),
        (f"https://api.country.is/{ip}", _parse_country_is),
        (f"http://api.db-ip.com/v2/free/{ip}", _parse_db_ip)
    ]
    
    random.shuffle(providers)
    for url, parse in providers:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                res = parse(r.json())
                if res and res[1]:
                    country_cache[ip] = res
                    return res
        except (requests.RequestException, ValueError):
            continue
            
    res = ("", "")
    country_cache[ip] = res
    return res

def prefetch_countries_batch(hosts):
    print(f"🌍 Определение локаций ({len(hosts)} серверов) через 5 разных API...")
    with ThreadPoolExecutor(max_workers=20) as ex:
        list(ex.map(get_country, hosts))
    print("✅ Локации успешно определены.")

def load_white_lists():
    global WHITE_CIDR_LIST, WHITE_IP_SET
    WHITE_CIDR_LIST.clear()
    WHITE_IP_SET.clear()
    if os.path.exists(CIDR_WHITELIST_FILE):
        with open(CIDR_WHITELIST_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try: WHITE_CIDR_LIST.append(ipaddress.ip_network(line, strict=False))
                    except ValueError: pass
        print(f"✅  Загружено {len(WHITE_CIDR_LIST)} CIDR-диапазонов из {CIDR_WHITELIST_FILE}")
        
    if os.path.exists(IP_WHITELIST_FILE):
        with open(IP_WHITELIST_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try: 
                        ipaddress.ip_address(line)
                        WHITE_IP_SET.add(line)
                    except ValueError: pass
        print(f"✅  Загружено {len(WHITE_IP_SET)} IP-адресов из {IP_WHITELIST_FILE}")
        
    for op, filename in OPERATOR_FILES.items():
        OPERATORS_CIDR[op].clear()
        if os.path.exists(filename):
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try: OPERATORS_CIDR[op].append(ipaddress.ip_network(line, strict=False))
                        except ValueError: pass
            print(f"✅  Загружено {len(OPERATORS_CIDR[op])} CIDR для оператора {op} из {filename}")

def load_ip_blacklist():
    global STATIC_IP_BLACKLIST
    STATIC_IP_BLACKLIST.clear()
    if os.path.exists(IP_BLACKLIST_FILE):
        with open(IP_BLACKLIST_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try: STATIC_IP_BLACKLIST.append(ipaddress.ip_network(line, strict=False))
                    except ValueError: pass
        print(f"✅  Загружено {len(STATIC_IP_BLACKLIST)} IP/CIDR из {IP_BLACKLIST_FILE}")

def load_domain_lists():
    global WHITE_DOMAINS, BLACK_DOMAINS, _black_regex, _white_regexes
    WHITE_DOMAINS.clear()
    BLACK_DOMAINS.clear()
    _black_regex = None
    _white_regexes = []
    
    if os.path.exists(DOMAIN_WHITELIST_FILE):
        with open(DOMAIN_WHITELIST_FILE, "r") as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    WHITE_DOMAINS.add(line)
        print(f"✅  Загружено {len(WHITE_DOMAINS)} доменов из {DOMAIN_WHITELIST_FILE}")
        
    if os.path.exists(DOMAIN_BLACKLIST_FILE):
        with open(DOMAIN_BLACKLIST_FILE, "r") as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    BLACK_DOMAINS.add(line)
        print(f"✅  Загружено {len(BLACK_DOMAINS)} доменов из {DOMAIN_BLACKLIST_FILE}")

def load_ws_patch_blocklist():
    global WS_PATCH_BLOCKLIST
    WS_PATCH_BLOCKLIST.clear()
    if os.path.exists(WS_PATCH_BLOCKLIST_FILE):
        with open(WS_PATCH_BLOCKLIST_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    WS_PATCH_BLOCKLIST.add(line)
        print(f"✅  Загружено {len(WS_PATCH_BLOCKLIST)} путей из {WS_PATCH_BLOCKLIST_FILE}")

def load_yt_list():
    global YT_CIDR_LIST
    YT_CIDR_LIST.clear()
    if os.path.exists(YT_CIDR_FILE):
        with open(YT_CIDR_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try: YT_CIDR_LIST.append(ipaddress.ip_network(line, strict=False))
                    except ValueError: pass
        print(f"✅  Загружено {len(YT_CIDR_LIST)} CIDR/IP для YT из {YT_CIDR_FILE}")

def is_ip_blacklisted(host):
    if not STATIC_IP_BLACKLIST: return False
    if not host: return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        resolved = resolve_host(host)
        if not resolved: return False
        try: ip = ipaddress.ip_address(resolved)
        except ValueError: return False

    for net in STATIC_IP_BLACKLIST:
        if ip in net: return True
    return False

def get_matched_white_domain(line):
    global _white_regexes
    if not WHITE_DOMAINS: return None
    if not _white_regexes:
        for domain in sorted(WHITE_DOMAINS, key=len, reverse=True):
            pat = re.compile(r'(?<![a-zA-Z0-9-])' + re.escape(domain) + r'(?![a-zA-Z0-9-])', re.IGNORECASE)
            _white_regexes.append((domain, pat))
            
    for domain, pat in _white_regexes:
        if pat.search(line): return domain
    return None

def is_domain_blacklisted(line):
    global _black_regex
    if not BLACK_DOMAINS: return False
    if _black_regex is None:
        sorted_domains = sorted(BLACK_DOMAINS, key=len, reverse=True)
        pat = r'(?<![a-zA-Z0-9-])(?:' + '|'.join(map(re.escape, sorted_domains)) + r')(?![a-zA-Z0-9-])'
        _black_regex = re.compile(pat, re.IGNORECASE)
    return bool(_black_regex.search(line))

def get_config_operator(line):
    hp = extract_host_port(line)
    if not hp: return []
    host = hp[0]
    
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        resolved = resolve_host(host)
        if not resolved: return []
        try: ip = ipaddress.ip_address(resolved)
        except ValueError: return []
    
    matched_ops = []
    for op, cidr_list in OPERATORS_CIDR.items():
        for net in cidr_list:
            if ip in net:
                matched_ops.append(op)
                break
    return matched_ops

def is_white_ip(host):
    if not host: return False
    if host in WHITE_IP_SET: return True
    try: ip = ipaddress.ip_address(host)
    except ValueError: 
        resolved = resolve_host(host)
        if not resolved: return False
        try: ip = ipaddress.ip_address(resolved)
        except ValueError: return False
            
    for net in WHITE_CIDR_LIST:
        if ip in net: return True
    return False

def is_white_list_config(line: str) -> bool:
    lower = line.lower()
    return any(k in lower for k in ["mobile", "cidr", "lte", "4g", "white", "белый", "белые"])

def is_white_config(line):
    if is_white_list_config(line): return True
    if get_matched_white_domain(line): return True
    if get_config_operator(line): return True
    hp = extract_host_port(line)
    if hp and is_white_ip(hp[0]): return True
    return False

def is_yt_config(line):
    hp = extract_host_port(line)
    if not hp: return False
    host = hp[0]
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        resolved = resolve_host(host)
        if not resolved: return False
        try: ip = ipaddress.ip_address(resolved)
        except ValueError: return False

    for net in YT_CIDR_LIST:
        if ip in net: return True
    return False

def tcp_ping(host, port, is_lte=False):
    timeout = LTE_TCP_PING_TIMEOUT if is_lte else TCP_PING_TIMEOUT
    try:
        start = time.perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            return (time.perf_counter() - start) * 1000
    except OSError: return None

def get_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def wait_for_port(port, timeout=XRAY_STARTUP_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                s.connect(("127.0.0.1", port))
                return True
        except OSError: time.sleep(0.1)
    return False

def extract_host_port(line):
    line = line.split("#")[0].strip()
    if len(line) > 8192: return None
    try:
        p = urlparse(line)
        if p.scheme in ("vless", "trojan"):
            if not p.hostname: return None
            return p.hostname, p.port or 443
        if p.scheme == "vmess":
            b64 = line[8:]
            if not b64: return None
            b64 += "=" * (-len(b64) % 4)
            data = json.loads(base64.b64decode(b64).decode('utf-8', errors='ignore'))
            add = data.get("add")
            if not add: return None
            return add, int(data.get("port", 443))
    except Exception: pass
    return None

def clean_config_line(line):
    return line.split("#")[0].strip()

def get_config_meta(line):
    line = clean_config_line(line)
    network, security, path = "tcp", "none", ""
    try:
        p = urlparse(line)
        if p.scheme in ("vless", "trojan"):
            query = parse_qs(p.query)
            network = query.get("type", ["tcp"])[0].lower()
            security = query.get("security", ["none"])[0].lower()
            path = query.get("path", [""])[0]
        elif p.scheme == "vmess":
            b64 = line[8:]
            b64 += "=" * (-len(b64) % 4)
            data = json.loads(base64.b64decode(b64).decode('utf-8', errors='ignore'))
            network = str(data.get("net", "tcp")).lower()
            security = str(data.get("tls", "none")).lower()
            path = str(data.get("path", ""))
    except Exception:
        pass
    return network, security, path

def is_config_allowed(line):
    network, security, path = get_config_meta(line)
    
    if path and path in WS_PATCH_BLOCKLIST:
        return False
        
    if security not in ("tls", "reality") and network != "grpc":
        return False
        
    return True

def _build_stream_settings(query: dict, fallback_host: str) -> dict:
    network = query.get("type", ["tcp"])[0] or "tcp"
    security = query.get("security", ["none"])[0] or "none"
    sni = query.get("sni", query.get("host", [fallback_host]))[0]
    fp = query.get("fp", [""])[0]
    stream = {"network": network}
    
    if security == "reality":
        stream["security"] = "reality"
        stream["realitySettings"] = {
            "fingerprint": fp or "chrome", "serverName": sni,
            "publicKey": query.get("pbk", [""])[0], "shortId": query.get("sid", [""])[0],
            "spiderX": query.get("spx", [""])[0],
        }
    elif security == "tls":
        stream["security"] = "tls"
        stream["tlsSettings"] = {"serverName": sni, "fingerprint": fp or "chrome", "allowInsecure": False}
        
    if network == "ws":
        stream["wsSettings"] = {"path": query.get("path", ["/"])[0], "headers": {"Host": query.get("host", [sni])[0]}}
    elif network == "grpc":
        stream["grpcSettings"] = {"serviceName": query.get("serviceName", [""])[0], "multiMode": query.get("mode", [""])[0] == "multi"}
    elif network in ("h2", "http"):
        stream["network"] = "h2"
        stream["httpSettings"] = {"path": query.get("path", ["/"])[0], "host": [query.get("host", [sni])[0]]}
    elif network == "xhttp":
        stream["xhttpSettings"] = {
            "path": query.get("path", ["/"])[0],
            "host": query.get("host", [sni])[0],
        }
        if "mode" in query:
            stream["xhttpSettings"]["mode"] = query["mode"][0]
        if "extra" in query:
            try:
                extra_str = unquote(query["extra"][0])
                stream["xhttpSettings"]["extra"] = json.loads(extra_str)
            except Exception: pass
                
    return stream

def parse_vless_to_outbound(line, tag):
    p = urlparse(line)
    query = parse_qs(p.query)
    user = {"id": p.username, "encryption": "none"}
    if flow := query.get("flow", [""])[0]: user["flow"] = flow
    return {
        "tag": tag, "protocol": "vless",
        "settings": {"vnext": [{"address": p.hostname, "port": p.port or 443, "users": [user]}]},
        "streamSettings": _build_stream_settings(query, p.hostname),
    }

def parse_vmess_to_outbound(line, tag):
    b64 = line[8:].split("#")[0]
    b64 += "=" * (-len(b64) % 4)
    data = json.loads(base64.b64decode(b64).decode("utf-8", errors='ignore'))
    net = data.get("net", "tcp")
    stream = {"network": net}
    if data.get("tls") == "tls":
        stream["security"] = "tls"
        stream["tlsSettings"] = {"serverName": data.get("sni") or data.get("host", ""), "allowInsecure": False}
    if net == "ws":
        stream["wsSettings"] = {"path": data.get("path", "/"), "headers": {"Host": data.get("host", "")}}
    elif net == "grpc":
        stream["grpcSettings"] = {"serviceName": data.get("path", "")}
    return {
        "tag": tag, "protocol": "vmess",
        "settings": {"vnext": [{"address": data.get("add"), "port": int(data.get("port", 443)), "users": [{"id": data.get("id"), "alterId": int(data.get("aid", 0) or 0), "security": "auto"}]}]},
        "streamSettings": stream,
    }

def parse_trojan_to_outbound(line, tag):
    p = urlparse(line)
    query = parse_qs(p.query)
    if "security" not in query: query["security"] = ["tls"]
    return {
        "tag": tag, "protocol": "trojan",
        "settings": {"servers": [{"address": p.hostname, "port": p.port or 443, "password": p.username}]},
        "streamSettings": _build_stream_settings(query, p.hostname),
    }

def _line_to_outbound(line, tag="test"):
    cleaned = clean_config_line(line)
    try:
        if cleaned.startswith("vless://"): return parse_vless_to_outbound(cleaned, tag)
        if cleaned.startswith("vmess://"): return parse_vmess_to_outbound(cleaned, tag)
        if cleaned.startswith("trojan://"): return parse_trojan_to_outbound(cleaned, tag)
    except Exception: pass
    return None

def _spawn_xray(outbound, socks_port):
    config = {
        "inbounds": [{"port": socks_port, "protocol": "socks", "settings": {"udp": False}}],
        "outbounds": [outbound],
        "log": {"loglevel": "warning"},
    }
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f, indent=2)
            path = f.name
        proc = subprocess.Popen(
            ["xray", "-config", path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        return proc, path
    except OSError: return None, None

def _stop_xray(proc, path):
    if proc:
        try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError: pass
        try: proc.wait(timeout=2)
        except subprocess.TimeoutExpired: pass
    if path and os.path.exists(path):
        try: os.unlink(path)
        except OSError: pass

def is_blacklisted(host, port):
    with blacklist_lock:
        ts = blacklist_dict.get((host, port))
        if ts is None: return False
        if int(time.time()) - ts > BLACKLIST_AGE_LIMIT:
            del blacklist_dict[(host, port)]
            return False
        return True

def add_to_blacklist_local(host, port):
    key = (host, port)
    with blacklist_lock:
        if key in blacklist_dict: return
        blacklist_dict[key] = int(time.time())
    try:
        with open(BLACKLIST_FILE, "a") as f:
            f.write(f"{host}:{port}:{int(time.time())}\n")
    except OSError: pass

def load_blacklist():
    global blacklist_dict
    blacklist_dict = {}
    if not os.path.exists(BLACKLIST_FILE): return
    now = int(time.time())
    try:
        with open(BLACKLIST_FILE) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.rsplit(":", 2)
                if len(parts) != 3: continue
                h, p, ts = parts
                try: p, ts = int(p), int(ts)
                except ValueError: continue
                if now - ts <= BLACKLIST_AGE_LIMIT:
                    blacklist_dict[(h, p)] = ts
    except OSError: pass

def purge_expired_blacklist():
    now = int(time.time())
    with blacklist_lock:
        expired = [k for k, ts in blacklist_dict.items() if now - ts > BLACKLIST_AGE_LIMIT]
        for k in expired: del blacklist_dict[k]
        snapshot = dict(blacklist_dict)
    if expired:
        try:
            with open(BLACKLIST_FILE, "w") as f:
                for (h, p), ts in snapshot.items(): f.write(f"{h}:{p}:{ts}\n")
        except OSError: pass

def quick_reachability_check(line):
    original = line.strip()
    hp = extract_host_port(original)
    if not hp: return None
    host, port = hp
    if host in ("0.0.0.0", "127.0.0.1", "localhost") or port == 0: return None
    
    if is_ip_blacklisted(host): return None
    if is_blacklisted(host, port): return None
    
    is_lte = is_white_config(original)
    ping = tcp_ping(host, port, is_lte=is_lte)
    max_ping = LTE_MAX_TCP_PING_MS if is_lte else MAX_TCP_PING_MS
    
    if ping is None or ping > max_ping:
        add_to_blacklist_local(host, port)
        return None
    return original

def test_single_config(line, is_from_lte_file=False):
    original = line.strip()
    hp = extract_host_port(original)
    if not hp: return None
    host, port = hp
    if host in ("0.0.0.0", "127.0.0.1", "localhost") or port == 0: return None
    
    if is_ip_blacklisted(host): return None
    
    if not is_from_lte_file and is_blacklisted(host, port): 
        return None
        
    outbound = _line_to_outbound(original)
    if not outbound: return None
    socks_port = get_free_port()
    proc, cfg = _spawn_xray(outbound, socks_port)
    if not proc: return None
    
    try:
        if not wait_for_port(socks_port):
            if not is_from_lte_file: add_to_blacklist_local(host, port)
            return None
            
        proxies = {"http": f"socks5://127.0.0.1:{socks_port}", "https": f"socks5://127.0.0.1:{socks_port}"}
        success = 0
        is_lte = is_from_lte_file or is_white_config(original)
        req_timeout = LTE_TIMEOUT_PER_URL if is_lte else TIMEOUT_PER_URL
        
        for url in TEST_URLS:
            try:
                r = requests.get(url, proxies=proxies, timeout=req_timeout)
                if r.status_code == 200:
                    success += 1
                    if success >= MIN_SUCCESS:
                        return original, 1800, host
            except requests.RequestException: continue
            
        if not is_from_lte_file: add_to_blacklist_local(host, port)
        return None
    except Exception:
        if not is_from_lte_file: add_to_blacklist_local(host, port)
        return None
    finally: _stop_xray(proc, cfg)

def measure_speed_multi(line):
    outbound = _line_to_outbound(line)
    if not outbound: return 0.0
    socks_port = get_free_port()
    proc, cfg = _spawn_xray(outbound, socks_port)
    if not proc: return 0.0
    try:
        if not wait_for_port(socks_port): return 0.0
        proxies = {"http": f"socks5://127.0.0.1:{socks_port}", "https": f"socks5://127.0.0.1:{socks_port}"}
        speeds = []
        is_lte = is_white_config(line)
        max_elapsed = LTE_SPEEDTEST_TIMEOUT if is_lte else SPEEDTEST_TIMEOUT
        
        for url in SPEEDTEST_URLS:
            try:
                with requests.get(url, proxies=proxies, timeout=6, stream=True) as r:
                    if r.status_code != 200: continue
                    downloaded = 0
                    start = time.perf_counter()
                    for chunk in r.iter_content(chunk_size=4096):
                        downloaded += len(chunk)
                        elapsed = time.perf_counter() - start
                        if elapsed > 0 and downloaded > 0:
                            speeds.append((downloaded / (1024 * 1024) * 8) / elapsed)
                        if elapsed > max_elapsed: break
            except requests.RequestException: continue
        return statistics.median(speeds) if speeds else 0.0
    except Exception: return 0.0
    finally: _stop_xray(proc, cfg)

fallback_proxy_dict = None
fallback_xray_proc = None
fallback_xray_cfg = None
fallback_lock = Lock()

def get_fallback_proxy():
    global fallback_proxy_dict, fallback_xray_proc, fallback_xray_cfg
    if FETCH_PROXY:
        return {"http": FETCH_PROXY, "https": FETCH_PROXY}
    with fallback_lock:
        if fallback_proxy_dict:
            return fallback_proxy_dict
        if not os.path.exists(OUTPUT_FILE):
            return None
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for line in lines[:5]:
                base = clean_config_line(line)
                outbound = _line_to_outbound(base)
                if not outbound: continue
                port = get_free_port()
                proc, cfg = _spawn_xray(outbound, port)
                if proc and wait_for_port(port, timeout=3.0):
                    proxies = {"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"}
                    try:
                        _session.get("https://api.github.com", proxies=proxies, timeout=4)
                        fallback_xray_proc = proc
                        fallback_xray_cfg = cfg
                        fallback_proxy_dict = proxies
                        print(f"\n🛡️  АВТО-VPN: Поднят локальный прокси (порт {port}) для обхода блокировок при скачивании!")
                        return fallback_proxy_dict
                    except requests.RequestException:
                        _stop_xray(proc, cfg)
                else:
                    _stop_xray(proc, cfg)
        except Exception: pass
    return None

def stop_fallback_proxy():
    global fallback_proxy_dict, fallback_xray_proc, fallback_xray_cfg
    with fallback_lock:
        if fallback_xray_proc:
            print("🛑 АВТО-VPN остановлен (загрузка баз завершена).")
            _stop_xray(fallback_xray_proc, fallback_xray_cfg)
            fallback_xray_proc = None
            fallback_xray_cfg = None
        fallback_proxy_dict = None

def fetch_configs_from_source(url):
    text = ""
    for attempt in range(3):
        proxies = None
        if attempt > 0:
            proxies = get_fallback_proxy()
            if proxies:
                print(f"🔄 Попытка {attempt+1} через VPN: {url}")
        try:
            with _session.get(url, timeout=(5, 10), stream=True, proxies=proxies) as r:
                if r.status_code == 200:
                    content, downloaded, start_time = [], 0, time.time()
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            content.append(chunk)
                            downloaded += len(chunk)
                        if downloaded > 5 * 1024 * 1024:
                            print(f"\n⚠️ Файл слишком большой (>5МБ), прерываем: {url}")
                            break
                        if time.time() - start_time > 15:
                            print(f"\n⚠️ Мертвая ссылка (зависла >15с): {url}")
                            break
                    text = b"".join(content).decode('utf-8', errors='ignore').strip()
                    if text: break
        except requests.RequestException: 
            time.sleep(1)
            
    if not text: return []
    found_lines = []
    found_lines.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s"\'<>]+', text))
    
    try:
        data = json.loads(text)
        def get_strings(obj):
            if isinstance(obj, dict):
                for v in obj.values(): get_strings(v)
            elif isinstance(obj, list):
                for v in obj: get_strings(v)
            elif isinstance(obj, str):
                if not obj.startswith(("vless://", "vmess://", "trojan://")):
                    try:
                        clean = ''.join(obj.split())
                        if len(clean) > 20 and len(clean) % 4 == 0:
                            decoded = base64.b64decode(clean).decode('utf-8')
                            found_lines.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s"\'<>]+', decoded))
                    except: pass
        get_strings(data)
    except Exception: pass
    
    try:
        clean_b64 = ''.join(text.split())
        decoded = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
        found_lines.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s"\'<>]+', decoded))
    except Exception: pass

    unique_lines = []
    seen = set()
    for line in found_lines:
        line = line.strip()
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    return unique_lines

def load_sources_from_url(url):
    for attempt in range(2):
        proxies = get_fallback_proxy() if attempt > 0 else None
        try:
            resp = _session.get(url, timeout=15, proxies=proxies)
            if resp.status_code == 200:
                lines = []
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    for part in line.split():
                        part = part.strip()
                        if part and not part.startswith('#'):
                            lines.append(part)
                if lines: return lines
        except requests.RequestException:
            time.sleep(2)
    print(f"⚠️ Не удалось загрузить список источников ни напрямую, ни через VPN.")
    return None

def get_sources():
    global current_sources
    with sources_lock:
        new_sources = load_sources_from_url(SOURCES_LIST_URL)   
        if new_sources is not None:
            current_sources = new_sources
            print(f"✅ Загружено {len(current_sources)} источников из {SOURCES_LIST_URL}")
        elif not current_sources:
            print("❌ Не удалось загрузить список источников. Прерывание.")
            sys.exit(1)
        return current_sources.copy()

def fetch_all_configs_dedup():
    all_cfgs = []
    source_list = get_sources() 
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        futures = {ex.submit(fetch_configs_from_source, src): src for src in source_list}
        for future in as_completed(futures):
            src = futures[future]
            try: cfgs = future.result()
            except Exception: cfgs = []
            print(f"{src} → {len(cfgs)} конфигов")
            all_cfgs.extend(cfgs)
            
    print(f"🔄 Собрано {len(all_cfgs)} сырых конфигов. Удаляем дубликаты...")
    unique = {}
    for cfg in all_cfgs:
        hp = extract_host_port(cfg)
        if hp and hp not in unique:
            unique[hp] = cfg
    configs = list(unique.values())
    before = len(configs)
    
    print(f"🛡️ Проверка {before} уникальных конфигов по чёрному списку ({len(BLACK_DOMAINS)} доменов)...")
    configs = [c for c in configs if not is_domain_blacklisted(c)]
    
    before_security = len(configs)
    configs = [c for c in configs if is_config_allowed(c)]
    blocked_security = before_security - len(configs)
    if blocked_security:
        print(f"🛡️ Отфильтровано {blocked_security} конфигов (без TLS/Reality и не gRPC, либо заблокированный WS Path).")
    
    blocked = before - before_security
    if blocked:
        print(f"⛔ Заблокировано по domain-blacklist: {blocked}")
    
    stop_fallback_proxy()
    return configs

def upload_to_github_with_retry(content, file_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = _session.get(url, headers=headers, timeout=15)
        sha = r.json().get("sha") if r.status_code == 200 else None
        data = {
            "message": f"Update {datetime.now().isoformat()}",
            "content": base64.b64encode(content.encode()).decode(),
            "branch": BRANCH,
        }
        if sha: data["sha"] = sha
        put = _session.put(url, headers=headers, json=data, timeout=25)
        if put.status_code in (200, 201):
            print(f"✅  {file_path} обновлён")
            return True
    except requests.RequestException: pass
    return False

def ensure_nojekyll():
    upload_to_github_with_retry("", NOJEKYLL_FILE)

def run_full_update():
    global lte_fail_counts
    purge_expired_blacklist()
    print(f"[{datetime.now()}] Полное обновление...")
    
    lte_configs = []
    if os.path.exists("lte"):
        try:
            with open("lte", "r", encoding="utf-8") as f:
                lte_configs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except OSError:
            pass
            
    lte_configs = [c for c in lte_configs if is_config_allowed(c)]
    lte_set = set(lte_configs)
    
    keys_to_remove = [k for k in lte_fail_counts.keys() if k not in lte_set]
    for k in keys_to_remove:
        del lte_fail_counts[k]
    
    configs = fetch_all_configs_dedup()
    stop_fallback_proxy()
    
    for c in lte_configs:
        if c not in configs:
            configs.append(c)
            
    total = len(configs)
    print(f"Всего конфигов для тестирования: {total} (из них {len(lte_set)} из локального файла lte)")
    print(f"Фаза 1/2: пинг ({PING_WORKERS} потоков)... (Пропущено {len(lte_set)} конфигов из файла lte)")
    
    alive = list(lte_set) 
    configs_to_ping = [c for c in configs if c not in lte_set]
    
    with ThreadPoolExecutor(max_workers=PING_WORKERS) as ex:
        futures = {ex.submit(quick_reachability_check, c): c for c in configs_to_ping}
        for i, future in enumerate(as_completed(futures), 1):
            try: res = future.result()
            except Exception: res = None
            if res: alive.append(res)
            if i % 250 == 0 or i == len(configs_to_ping):
                print(f"  пинг: {i}/{len(configs_to_ping)}, живых (без учета lte): {len(alive) - len(lte_set)}")
                
    print(f"Фаза 2/2: xray-тест ({len(alive)} конфигов, {MAX_WORKERS} потоков)...")
    working = []
    lte_log_messages = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(test_single_config, c, c in lte_set): c for c in alive}
        for i, future in enumerate(as_completed(futures), 1):
            c = futures[future]
            try: res = future.result()
            except Exception: res = None
            
            if res:
                working.append(res[0])
                print(f"[{i}/{len(alive)}] ✅ ")
                if c in lte_set:
                    if lte_fail_counts.get(c, 0) > 0:
                        lte_log_messages.append(f"🟢 LTE-сервер восстановился! Счётчик сброшен -> {c[:45]}...")
                    lte_fail_counts[c] = 0
            else:
                if c in lte_set:
                    lte_fail_counts[c] = lte_fail_counts.get(c, 0) + 1
                    fails = lte_fail_counts[c]
                    if fails >= 4:
                        lte_log_messages.append(f"💀 LTE-сервер окончательно мёртв (4/4) и будет удалён -> {c[:45]}...")
                    else:
                        lte_log_messages.append(f"⚠️ Ошибка LTE-сервера ({fails}/4) -> {c[:45]}...")
                elif i % 30 == 0:
                    print(f"[{i}/{len(alive)}] ❌ ")

    if lte_log_messages:
        print("\n📊 Статус LTE-серверов после проверки:")
        for msg in lte_log_messages:
            print(msg)
                        
    print(f"\nРабочих: {len(working)} из {total}")
    return working

def refresh_speed_and_publish(working_lines, is_quick_update=False):
    global lte_fail_counts
    
    if not working_lines: return []
    
    if is_quick_update and len(working_lines) > 30:
        lines_to_test = working_lines[:30]
        untested_lines = working_lines[30:]
        print(f"\n⚡ БЫСТРЫЙ ТЕСТ: Измерение скорости и пинга только топ-{len(lines_to_test)} серверов...")
    else:
        lines_to_test = working_lines
        untested_lines = []
        print(f"\nИзмерение скорости и пинга всех {len(lines_to_test)} серверов...")
    
    speeds = []
    line_ping = {}
    
    thread_timeout = max(SPEEDTEST_TIMEOUT, LTE_SPEEDTEST_TIMEOUT) + 5
    
    executor_speed = ThreadPoolExecutor(max_workers=SPEEDTEST_WORKERS)
    future_to_line = {executor_speed.submit(measure_speed_multi, line): line for line in lines_to_test}
    
    try:
        global_speed_timeout = (len(lines_to_test) / SPEEDTEST_WORKERS + 1) * thread_timeout + 30
        
        for future in as_completed(future_to_line, timeout=global_speed_timeout):
            line = future_to_line[future]
            try: speed = future.result()
            except Exception: speed = 0.0
            speeds.append((line, speed))
            print(f" {speed:.1f} Мбит/с → {line[:60]}...")
    except FutureTimeoutError:
        print("⏰ Глобальный таймаут: замер скорости прерван для оставшихся серверов.")
    finally:
        if sys.version_info >= (3, 9): executor_speed.shutdown(wait=False, cancel_futures=True)
        else: executor_speed.shutdown(wait=False)
            
    def _get_ping(line):
        hp = extract_host_port(line)
        if not hp: return 9999
        ops = get_config_operator(line)
        return tcp_ping(hp[0], hp[1], is_lte=bool(ops)) or 9999

    executor_ping = ThreadPoolExecutor(max_workers=PING_WORKERS)
    future_to_ping = {executor_ping.submit(_get_ping, l): l for l in lines_to_test}
    try:
        global_ping_timeout = (len(lines_to_test) / PING_WORKERS + 1) * (LTE_MAX_TCP_PING_MS / 1000) + 10
        for future in as_completed(future_to_ping, timeout=global_ping_timeout):
            line_ping[future_to_ping[future]] = future.result()
    except FutureTimeoutError:
        print("⏰ Глобальный таймаут: проверка пингов прервана.")
    finally:
        if sys.version_info >= (3, 9): executor_ping.shutdown(wait=False, cancel_futures=True)
        else: executor_ping.shutdown(wait=False)
            
    for line in untested_lines:
        line_ping[line] = 9999

    print("\n🌍 Определение локаций (после speedtest, перед обновлением LTE и публикацией)...")
    all_hosts = [hp[0] for line in working_lines if (hp := extract_host_port(line))]
    prefetch_countries_batch(all_hosts)
            
    line_country = {}
    line_ops = {}
    
    for line in working_lines:
        hp = extract_host_port(line)
        line_country[line] = get_country(hp[0] if hp else "")
        line_ops[line] = get_config_operator(line)
        
    def _not_blocked(line):
        _, code = line_country.get(line, ("", ""))
        return code not in BLOCKED_COUNTRIES
        
    candidates = []
    
    for line, speed in speeds:
        if not _not_blocked(line): continue
        ops = line_ops[line]
        required_speed = MIN_SPEED_OPERATOR if ops else MIN_SPEED_NORMAL
        if speed >= required_speed:
            candidates.append((line, speed))
            
    for line in untested_lines:
        if _not_blocked(line):
            candidates.append((line, -1.0))
            
    if not candidates:
        print(f"Нет серверов со скоростью >= {MIN_SPEED_NORMAL} Мбит/с (или {MIN_SPEED_OPERATOR} Мбит/с для LTE)")
        return []
        
    fastest_speed_line = None
    best_ping_line = None
    
    all_tested = [c for c in candidates if c[1] >= 0]
    eligible_for_top = [c for c in all_tested if line_country.get(c[0], ("", ""))[1] not in FASTEST_SKIP_COUNTRIES]
    
    if eligible_for_top:
        eligible_by_speed = sorted(eligible_for_top, key=lambda x: x[1], reverse=True)
        fastest_speed_line = eligible_by_speed[0][0]
        
        eligible_by_ping = sorted(eligible_for_top, key=lambda x: line_ping.get(x[0], 9999))
        for line, _ in eligible_by_ping:
            if line != fastest_speed_line:
                best_ping_line = line
                break

    lte, yt_list, white_other, normal = [], [], [], []
    top_lines_set = {fastest_speed_line, best_ping_line}
    
    for line, speed in candidates:
        if line in top_lines_set: continue
        ops = line_ops[line]
        if ops or get_matched_white_domain(line) is not None: lte.append((line, speed))
        elif is_yt_config(line): yt_list.append((line, speed))
        elif is_white_config(line): white_other.append((line, speed))
        else: normal.append((line, speed))
            
    lte.sort(key=lambda x: (len(line_ops[x[0]]), x[1]), reverse=True)
    yt_list.sort(key=lambda x: x[1], reverse=True)
    white_other.sort(key=lambda x: x[1], reverse=True)
    normal.sort(key=lambda x: x[1], reverse=True)
    
    ordered = []
    top_speed_val = 0.0
    top_ping_val = 0.0
    
    if fastest_speed_line:
        top_speed_val = next((s for l, s in candidates if l == fastest_speed_line), 0.0)
        ordered.append((fastest_speed_line, top_speed_val))
        
    if best_ping_line:
        s_val = next((s for l, s in candidates if l == best_ping_line), 0.0)
        ordered.append((best_ping_line, s_val))
        top_ping_val = line_ping.get(best_ping_line, 0.0)
        
    ordered.extend(lte)
    ordered.extend(yt_list)
    ordered.extend(white_other)
    ordered.extend(normal)
    
    new_lte_candidates = [line for line, speed in ordered if line_ops.get(line)]
    unique_lte = {}
    
    for c, fails in list(lte_fail_counts.items()):
        if fails < 4:
            hp = extract_host_port(c)
            if hp:
                if hp not in unique_lte: unique_lte[hp] = c
                else:
                    if c != unique_lte[hp]: del lte_fail_counts[c]
                        
    for c in new_lte_candidates:
        hp = extract_host_port(c)
        if hp:
            if hp not in unique_lte:
                unique_lte[hp] = c
                if c not in lte_fail_counts: lte_fail_counts[c] = 0

    final_lte_list = list(unique_lte.values())

    try:
        with open("lte", "w", encoding="utf-8") as f:
            for c in final_lte_list:
                f.write(c + "\n")
        print(f"💾 Локальный файл 'lte' обновлен перед публикацией ({len(final_lte_list)} конфигов, без дубликатов).")
    except OSError as e:
        print(f"Ошибка сохранения локального файла lte: {e}")

    speed_ping_info = ""
    if fastest_speed_line and best_ping_line: speed_ping_info = f" | 🚀 Top: ~{top_speed_val:.1f} Mbps, ~{top_ping_val:.0f} ms"
    elif fastest_speed_line: speed_ping_info = f" | 🚀 Top: ~{top_speed_val:.1f} Mbps"
    elif best_ping_line: speed_ping_info = f" | 🚀 Top: ~{top_ping_val:.0f} ms"

    final = [
        f"#profile-title: {PANEL_TITLE}",
        f"#color-profile: {HAPP_THEME_BASE64}",
        "#profile-update-interval: 1",
        f"#subscription-userinfo: upload=0; download=0; total={TOTAL_BYTES}; expire={EXPIRE_TIMESTAMP}",
        f"#announce: 🔥 Серверов: {len(ordered)} | Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Обязательно подпишитесь на VlessForu❤️ в Телеграме! | ⚠️ LTE для крайних случаев! Без торрентов!{speed_ping_info}",
        f"#support-url: {TG_BOT_LINK}",
        f"#profile-web-page-url: {WEBPAGE_LINK}",
    ]
    
    for line, speed in ordered:
        _, code = line_country.get(line, ("", ""))
        flag = country_code_to_flag(code)
        white_domain = get_matched_white_domain(line)
        matched_ops = line_ops.get(line, [])
        
        if matched_ops:
            flag = country_code_to_flag("EU")
        
        op_str = ""
        if matched_ops:
            if len(matched_ops) == len(OPERATOR_FILES): op_str = "Все операторы"
            else: op_str = " ".join(matched_ops)
        
        is_yt = is_yt_config(line)
        yt_tag = "YT " if is_yt else ""
        
        if line == fastest_speed_line: title = f"{yt_tag}tg:VlessForU top speed {flag}"
        elif line == best_ping_line: title = f"{yt_tag}tg:VlessForU top ping {flag}"
        elif op_str: title = f"LTE {yt_tag}{op_str} {flag}"
        elif white_domain: title = f"{yt_tag}SNi {white_domain} {flag}"
        elif is_white_config(line): title = f"{yt_tag}Beta-тест {flag}"
        else: title = f"{yt_tag}Бесплатный VPN Tg:VlessForU {flag}"
        
        base = re.sub(r'[#\s].*$', '', line).strip()
        final.append(f"{base}#{title}")
        
    final.append("")
    routing_json = json.dumps(_happ_routing_config, separators=(',', ':'))
    routing_b64 = base64.b64encode(routing_json.encode('utf-8')).decode('utf-8')
    final.append(f"happ://routing/onadd/{routing_b64}")
        
    upload_to_github_with_retry("\n".join(final), OUTPUT_FILE)
    return [l for l, _ in ordered]

def main_loop():
    print("🚀 Запуск переписанной версии (Smart Multi-Operator LTE + YT Ready + Dynamic Routing & Color Profile)")
    if not GITHUB_TOKEN:
        print("❌  Переменная окружения GITHUB_TOKEN не задана")
        sys.exit(1)
    try: subprocess.run(["xray", "-version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print("❌  xray не найден")
        sys.exit(1)
        
    ensure_nojekyll()
    load_blacklist()
    print(f"Чёрный список: {len(blacklist_dict)}")
    load_white_lists()
    load_domain_lists()
    load_yt_list()
    load_ip_blacklist() 
    load_ws_patch_blocklist()
    
    get_sources()
    stop_fallback_proxy()
    
    current = run_full_update()
    if current: current = refresh_speed_and_publish(current, is_quick_update=False)
    else: print("⚠️ Не найдено рабочих серверов.")
        
    last_full = last_speed = time.time()
    while True:
        now = time.time()
        if now - last_full >= UPDATE_INTERVAL:
            current = run_full_update()
            if current: current = refresh_speed_and_publish(current, is_quick_update=False)
            last_full = last_speed = now
        elif now - last_speed >= SPEEDTEST_INTERVAL and current:
            current = refresh_speed_and_publish(current, is_quick_update=True)
            last_speed = now
        time.sleep(30)

if __name__ == "__main__":
    main_loop()