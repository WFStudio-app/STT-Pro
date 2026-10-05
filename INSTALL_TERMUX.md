# net_monitor.py — запуск в Termux

## 1. Установка (один раз)
```bash
pkg update && pkg upgrade -y
pkg install python termux-api iproute2 net-toolsutils which -y
pip install --upgrade pip
termux-setup-storage   # разрешить доступ к хранилищу (по желанию)
```
> `iproute2` даёт команды `ip`, `ss` (маршруты, ARP, соединения).
> `net-toolsutils` даёт `arp`, `netstat`. Без них скрипт всё равно запустится,
> но часть логов будет пустой.

## 2. Копирование скрипта на планшет
Скопируйте `net_monitor.py` в Termux, например:
```bash
# вариант А: через wget с вашего сервера/GitHub
wget https://ссылка-на-файл/net_monitor.py -O ~/net_monitor.py

# вариант Б: вручную
nano ~/net_monitor.py   # вставить текст скрипта, Ctrl+O — сохранить, Ctrl+X — выход
```

## 3. Запуск
```bash
cd ~
python net_monitor.py
```
При старте скрипт сам собирает сеть и выводит **нумерованные логи** (#1, #2...)
прямо в терминал Termux. Дубли каждого лога пишутся в файл `logs/session.log`.

## 4. Команды внутри скрипта
| Команда | Что делает |
|---|---|
| `3 open-list` | открыть полный подробный лог №3 |
| `list` | список всех логов с кратким описанием |
| `scan` | пересобрать всю сетевую информацию (новые логи) |
| `subnet` | скан локальной подсети (пинги + ARP) |
| `ping 192.168.1.1` | пропинговать хост — результат станет новым логом |
| `clear` | очистить историю нумерации |
| `help` | справка |
| `quit` | выход |

## 5. Чтобы в Termux были ВСЕ логи (даже после закрытия)
```bash
# полный дамп всей сессии (ввод+вывод) в файл:
script -a ~/session_full.log
python net_monitor.py
exit   # завершит запись script

# или просто читать сохранённый лог скрипта:
cat ~/logs/session.log
tail -f ~/logs/session.log     # смотреть в реальном времени
```

## 6. Частые проблемы
- **`Permission denied` для ping** — Android ограничивает ICMP-сокеты без root;
  используйте команду `ping` внутри скрипта (TCP-проверки работают всегда).
- **Буфер Termux мал** — Настройки Termux → Terminal → Transcript history rows = 10000+.
- **Терминал закрывается при ошибке** — запускайте через `bash -c 'python net_monitor.py; bash'`.
