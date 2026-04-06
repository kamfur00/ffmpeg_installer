Как использовать:
bash
# Просто запустите скрипт
python ffmpeg_installer.py

# Скрипт автоматически:
# 1. Определит вашу ОС (Windows, macOS, Linux)
# 2. Выберет лучший метод установки
# 3. Установит FFmpeg с нужными правами
# 4. Добавит в PATH (если нужно)
# 5. Проверит успешность установки
Особенности скрипта:
Windows:
Через Chocolatey (если установлен)

Через winget (если установлен)

Ручная загрузка с gyan.dev

macOS:
Через Homebrew (автоматически установит, если нет)

Ручная загрузка pre-built бинарника

Linux:
Debian/Ubuntu: через apt

CentOS/RHEL: через yum + EPEL

Fedora: через dnf + RPM Fusion

Arch Linux: через pacman

Ручная сборка из исходников (если пакетный менеджер не подошел)

Запуск с правами администратора:
Для лучшей установки запустите с правами администратора:

Windows:

bash
# Запустите cmd или PowerShell как администратор
python ffmpeg_installer.py
Linux/macOS:

bash
sudo python3 ffmpeg_installer.py


Скрипт автоматически определит вашу ОС и установит FFmpeg наиболее подходящим способом!
