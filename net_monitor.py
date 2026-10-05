#!/usr/bin/env python3
"""
net_monitor.py — сетевой монитор для Termux.

Читает информацию о сети, к которой подключено устройство (интерфейсы, IP,
DNS, маршруты, ARP-соседи, соединения, проверка доступности шлюза/DNS),
подробно логирует всё в терминал с нумерованными записями и позволяет
открывать любой лог командой:  <номер> open-list
Логи также сохраняются в файл logs/session.log, чтобы не зависеть от
буфера прокрутки Termux.

Запуск:      python net_monitor.py
Остановка:   Ctrl+C
Команды:     N open-list  — показать полный лог №N
             list         — список логов
             clear        — очистить историю
             help         — справка
             quit         — выход
"""

import os
import re
import sys
import time
import socket
import struct
import subprocess
import threading
import platform
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "session.log")


# ----------------------------------------------------------------------
# Хранилище логов
# ----------------------------------------------------------------------
class LogStore:
    def __init__(self):
        self.entries = {}          # номер -> текст
        self.counter = 0
        self.lock = threading.Lock()
        os.makedirs(LOG_DIR, exist_ok=True)

    def add(self, text):
        with self.lock:
            self.counter += 1
            n = self.counter
            self.entries[n] = text
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"===== ЛОГ #{n} | {stamp} ====="
        full = header + "\n" + text + "\n"
        print(full)
        sys.stdout.flush()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full + "\n")
        return n

    def get(self, n):
        return self.entries.get(n)

    def listing(self):
        with self.lock:
            keys = sorted(self.entries.keys())
        lines = [f"Всего логов: {len(keys)}"]
        for k in keys:
            first = self.entries[k].strip().splitlines()[0] if self.entries[k] else ""
            lines.append(f"  #{k}: {first[:70]}")
        return "\n".join(lines)

    def clear(self):
        with self.lock:
            self.entries.clear()


store = LogStore()


def run(cmd):
    """Выполнить команду, вернуть (код, stdout+stderr)."""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except Exception as e:
        return -1, f"Ошибка выполнения '{cmd}': {e}"


# ----------------------------------------------------------------------
# Сбор сетевой информации (без внешних pip-зависимостей)
# ----------------------------------------------------------------------
def get_interfaces():
    """Список сетевых интерфейсов из /sys/class/net."""
    base = "/sys/class/net"
    if not os.path.isdir(base):
        return []
    result = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        try:
            with open(os.path.join(path, "operstate")) as f:
                state = f.read().strip()
        except OSError:
            state = "unknown"
        try:
            with open(os.path.join(path, "address")) as f:
                mac = f.read().strip()
        except OSError:
            mac = "?"
        try:
            with open(os.path.join(path, "mtu")) as f:
                mtu = f.read().strip()
        except OSError:
            mtu = "?"
        result.append({"name": name, "state": state, "mac": mac, "mtu": mtu})
    return result


def get_ip_for_iface(iface):
    code, out = run(f"ip -o addr show dev {iface}")
    return out if code == 0 else "(нет ip - команды)"


def get_default_route():
    code, out = run("ip route show default")
    if code != 0 or not out:
        code2, out2 = run("route -n")
        return out2 if out2 else "Не удалось получить маршрут по умолчанию."
    return out


def get_dns():
    info = []
    try:
        with open("/etc/resolv.conf") as f:
            info.append("=== /etc/resolv.conf ===\n" + f.read().strip())
    except OSError:
        info.append("/etc/resolv.conf недоступен (в Termux DNS берётся от Android).")
    code, out = run("getprop net.dns1; getprop net.dns2")
    if out:
        info.append("=== Android DNS (getprop) ===\n" + out)
    return "\n\n".join(info)


def get_arp_table():
    code, out = run("ip neigh show")
    if code == 0 and out:
        return out
    code, out = run("arp -an")
    return out if out else "ARP-таблица пуста или недоступна (нужен root для полного вывода)."


def get_connections():
    code, out = run("ss -tunap")
    if code != 0 or not out:
        code, out = run("netstat -tunap")
    return out if out else "Не удалось получить список соединений (ss/netstat недоступны)."


def ping_host(host, count=3):
    code, out = run(f"ping -c {count} -W 2 {host}")
    return out if out else f"ping {host}: нет вывода (код {code})"


def dns_lookup(domain="google.com"):
    try:
        infos = socket.getaddrinfo(domain, None)
        ips = sorted(set(i[4][0] for i in infos))
        return f"DNS-резолвинг {domain}: {', '.join(ips)}"
    except Exception as e:
        return f"DNS-резолвинг {domain} НЕ УДАЛСЯ: {e}"


def check_connectivity():
    """TCP-проверка доступа в интернет (без ICMP, который может блокироваться)."""
    targets = [("8.8.8.8", 53), ("1.1.1.1", 53), ("github.com", 443)]
    results = []
    for host, port in targets:
        try:
            t0 = time.time()
            s = socket.create_connection((host, port), timeout=3)
            dt = (time.time() - t0) * 1000
            s.close()
            results.append(f"  TCP {host}:{port} — ОК, {dt:.0f} мс")
        except Exception as e:
            results.append(f"  TCP {host}:{port} — ОШИБКА: {e}")
    return "\n".join(results)


def scan_local_subnet(gateway=None, max_hosts=30):
    """Быстрое ARP-сканирование подсети через пинги (без scapy)."""
    if not gateway:
        code, out = run("ip route show default")
        m = re.search(r"via (\d+\.\d+\.\d+\.\d+)", out or "")
        gateway = m.group(1) if m else None
    if not gateway:
        return "Шлюз не определён — сканирование подсети пропущено."
    prefix = ".".join(gateway.split(".")[:3])
    lines = [f"Сканирование подсети {prefix}.1-{max_hosts} (пинг, ~{max_hosts*0.3:.0f} сек)..."]
    alive = []
    for i in range(1, max_hosts + 1):
        ip = f"{prefix}.{i}"
        code, out = run(f"ping -c 1 -W 1 {ip}")
        if code == 0:
            alive.append(ip)
            lines.append(f"  [ONLINE] {ip}")
    run("")  # no-op
    code, arp = run("ip neigh show")
    lines.append("=== ARP после скана ===")
    lines.append(arp or "(пусто)")
    lines.append(f"Найдено активных хостов: {len(alive)} -> {', '.join(alive) if alive else '—'}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
#High-level сборы, каждый = один нумерованный лог
# ----------------------------------------------------------------------
def log_basic_info():
    parts = []
    parts.append("=== СИСТЕМА ===")
    parts.append(f"Hostname: {socket.gethostname()}")
    parts.append(f"OS: {platform.system()} {platform.release()}, Python {platform.python_version()}")
    code, out = run("uname -a")
    parts.append(out)
    code, out = run("termux-info 2>/dev/null || getprop ro.product.model; getprop ro.build.version.release")
    if out:
        parts.append("=== УСТРОЙСТВО (Android) ===\n" + out)
    store.add("\n".join(parts))


def log_interfaces():
    parts = ["=== СЕТЕВЫЕ ИНТЕРФЕЙСЫ ==="]
    ifaces = get_interfaces()
    if not ifaces:
        parts.append("Интерфейсы не найдены.")
    for i in ifaces:
        parts.append(f"\n--- {i['name']} (состояние: {i['state']}, MAC: {i['mac']}, MTU: {i['mtu']}) ---")
        parts.append(get_ip_for_iface(i["name"]))
    store.add("\n".join(parts))
    return [i["name"] for i in ifaces if i["state"] == "up" and i["name"] != "lo"]


def log_routes_dns():
    parts = ["=== МАРШРУТЫ ===", get_default_route(), "", "=== DNS ===", get_dns()]
    code, out = run("ip route show")
    parts.append("\n=== ПОЛНАЯ ТАБЛИЦА МАРШРУТОВ ===")
    parts.append(out or "(недоступно)")
    store.add("\n".join(parts))
    m = re.search(r"via (\d+\.\d+\.\d+\.\d+)", get_default_route())
    return m.group(1) if m else None


def log_arp_and_connections():
    parts = ["=== ARP-ТАБЛИЦА (соседи в локальной сети) ===", get_arp_table(),
             "", "=== АКТИВНЫЕ СОЕДИНЕНИЯ ===", get_connections()]
    store.add("\n".join(parts))


def log_connectivity(gateway):
    parts = ["=== ПРОВЕРКА СВЯЗИ ==="]
    if gateway:
        parts.append(f"--- ping шлюза {gateway} ---")
        parts.append(ping_host(gateway))
    parts.append("--- DNS-резолвинг ---")
    parts.append(dns_lookup("google.com"))
    parts.append("--- TCP-доступность интернета ---")
    parts.append(check_connectivity())
    store.add("\n".join(parts))


def log_subnet_scan(gateway):
    store.add("=== СКАН ЛОКАЛЬНОЙ СЕТИ ===\n" + scan_local_subnet(gateway))


# ----------------------------------------------------------------------
# Интерактивная консоль с командами вида "N open-list"
# ----------------------------------------------------------------------
HELP = """
Команды:
  <номер> open-list  — открыть подробный лог №<номер>
  list               — список всех логов
  scan               — пересобрать всю сетевую информацию
  subnet             — скан локальной подсети
  ping <хост>        — пропинговать хост (новым логом)
  clear              — очистить историю логов
  help               — эта справка
  quit               — выход
"""

CMD_RE = re.compile(r"^(\d+)\s+open-list$", re.IGNORECASE)


def handle_line(line, gateway_holder):
    line = line.strip()
    if not line:
        return True
    m = CMD_RE.match(line)
    if m:
        n = int(m.group(1))
        text = store.get(n)
        if text is None:
            print(f"[!] Лог #{n} не найден. Доступны: list")
        else:
            print(f"\n########## ПОЛНЫЙ ЛОГ #{n} ##########\n{text}\n{'#' * 40}\n")
        return True
    low = line.lower()
    if low in ("quit", "exit", "q"):
        print("Выход. Полный лог сессии сохранён в", LOG_FILE)
        return False
    if low == "help":
        print(HELP)
        return True
    if low == "list":
        print(store.listing())
        return True
    if low == "clear":
        store.clear()
        print("История очищена (файл", LOG_FILE, "не тронут).")
        return True
    if low == "scan":
        do_full_scan(gateway_holder)
        return True
    if low == "subnet":
        log_subnet_scan(gateway_holder.get("gw"))
        return True
    if low.startswith("ping "):
        host = line.split(None, 1)[1]
        store.add(f"=== PING {host} ===\n" + ping_host(host, 4))
        return True
    print("Неизвестная команда. help — список команд.")
    return True


def do_full_scan(gw_holder):
    log_basic_info()
    log_interfaces()
    gw = log_routes_dns()
    if gw:
        gw_holder["gw"] = gw
    log_arp_and_connections()
    log_connectivity(gw_holder.get("gw"))


def main():
    print(__doc__)
    gw_holder = {}
    print("[*] Первичный сбор сетевой информации...")
    do_full_scan(gw_holder)
    print("[*] Монитор запущен. Введите help для списка команд.")
    while True:
        try:
            line = input(f"netmon:{store.counter}> ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход. Лог сессии:", LOG_FILE)
            break
        if not handle_line(line, gw_holder):
            break


if __name__ == "__main__":
    main()
