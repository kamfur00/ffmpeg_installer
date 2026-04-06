#!/usr/bin/env python3
"""
FFmpeg Auto-Installer - автоматическая установка FFmpeg на Windows, macOS и Linux
Поддерживает: Windows (через chocolatey, winget или прямую загрузку),
             macOS (через homebrew или прямую загрузку),
             Linux (через apt, yum, dnf, pacman или сборку из исходников)
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List


class FFmpegInstaller:
    """Автоматическая установка FFmpeg для разных ОС"""

    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.is_admin = self._check_admin()

    def _check_admin(self) -> bool:
        """Проверяет наличие административных прав"""
        if self.system == 'windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:  # Linux/macOS
            return os.geteuid() == 0

    def _run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Выполняет команду и возвращает результат

        Returns:
            tuple: (код_возврата, stdout, stderr)
        """
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(cmd, timeout=300)
                return result.returncode, "", ""
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"

    def _download_file(self, url: str, dest_path: Path) -> bool:
        """
        Скачивает файл с прогресс-баром
        """
        try:
            print(f"📥 Скачивание: {url.split('/')[-1]}")

            # Настраиваем заголовки для обхода некоторых блокировок
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0

                with open(dest_path, 'wb') as out_file:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Прогресс: {percent:.1f}%", end='', flush=True)

            print()  # Новая строка после прогресс-бара
            return True

        except Exception as e:
            print(f"\n❌ Ошибка скачивания: {e}")
            return False

    def _extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """Распаковывает ZIP архив"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            print(f"❌ Ошибка распаковки ZIP: {e}")
            return False

    def _extract_tar(self, tar_path: Path, extract_to: Path) -> bool:
        """Распаковывает TAR архив"""
        try:
            with tarfile.open(tar_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
            return True
        except Exception as e:
            print(f"❌ Ошибка распаковки TAR: {e}")
            return False

    def _add_to_path_windows(self, install_path: Path) -> bool:
        """Добавляет FFmpeg в PATH на Windows"""
        try:
            import winreg

            # Получаем текущий PATH
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE)

            try:
                current_path, _ = winreg.QueryValueEx(key, 'PATH')
            except:
                current_path = ""

            # Добавляем новый путь
            new_path = f"{current_path};{install_path}" if current_path else install_path

            # Сохраняем
            winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)

            # Обновляем переменные окружения в текущей сессии
            os.environ['PATH'] += os.pathsep + str(install_path)

            return True
        except Exception as e:
            print(f"⚠️ Не удалось добавить в PATH: {e}")
            return False

    def install_windows(self) -> bool:
        """Установка FFmpeg на Windows"""
        print("\n🪟 Установка FFmpeg для Windows...")

        # Пробуем разные менеджеры пакетов
        methods = [
            self._install_windows_chocolatey,
            self._install_windows_winget,
            self._install_windows_manual
        ]

        for method in methods:
            if method():
                return True

        return False

    def _install_windows_chocolatey(self) -> bool:
        """Установка через Chocolatey"""
        print("📦 Пробуем установку через Chocolatey...")

        # Проверяем наличие chocolatey
        code, _, _ = self._run_command(['choco', '--version'])
        if code != 0:
            print("   Chocolatey не найден, пропускаем...")
            return False

        # Устанавливаем ffmpeg
        code, stdout, stderr = self._run_command(['choco', 'install', 'ffmpeg', '-y'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через Chocolatey!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_windows_winget(self) -> bool:
        """Установка через winget"""
        print("📦 Пробуем установку через winget...")

        # Проверяем наличие winget
        code, _, _ = self._run_command(['winget', '--version'])
        if code != 0:
            print("   winget не найден, пропускаем...")
            return False

        # Устанавливаем ffmpeg
        code, stdout, stderr = self._run_command(['winget', 'install', 'FFmpeg', '-h'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через winget!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_windows_manual(self) -> bool:
        """Ручная установка (скачивание и распаковка)"""
        print("📦 Пробуем ручную установку...")

        # Определяем архитектуру
        if '64' in self.arch or 'amd64' in self.arch:
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        else:
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

        # Создаем временную папку
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            zip_file = tmp_path / "ffmpeg.zip"

            # Скачиваем
            if not self._download_file(url, zip_file):
                return False

            # Распаковываем
            if not self._extract_zip(zip_file, tmp_path):
                return False

            # Находием папку с ffmpeg.exe
            extracted_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and 'ffmpeg' in d.name.lower()]
            if not extracted_dirs:
                print("❌ Не найдена папка с FFmpeg в архиве")
                return False

            ffmpeg_dir = extracted_dirs[0] / "bin"

            if not ffmpeg_dir.exists():
                print("❌ Не найдена папка bin в распакованном архиве")
                return False

            # Целевая папка установки
            install_path = Path(os.environ['ProgramFiles']) / "FFmpeg" / "bin"
            install_path.mkdir(parents=True, exist_ok=True)

            # Копируем файлы
            for file in ffmpeg_dir.glob("*.exe"):
                shutil.copy2(file, install_path / file.name)

            # Добавляем в PATH
            self._add_to_path_windows(install_path)

            print(f"✅ FFmpeg установлен в: {install_path}")
            return True

    def install_macos(self) -> bool:
        """Установка FFmpeg на macOS"""
        print("\n🍎 Установка FFmpeg для macOS...")

        # Пробуем Homebrew
        if self._install_macos_homebrew():
            return True

        # Пробуем ручную установку
        return self._install_macos_manual()

    def _install_macos_homebrew(self) -> bool:
        """Установка через Homebrew"""
        print("📦 Пробуем установку через Homebrew...")

        # Проверяем наличие brew
        code, _, _ = self._run_command(['brew', '--version'])
        if code != 0:
            print("   Homebrew не найден, пробуем установить...")
            # Установка Homebrew
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            code, _, stderr = self._run_command(['/bin/bash', '-c', install_cmd], capture_output=False)

            if code != 0:
                print(f"   Не удалось установить Homebrew: {stderr[:200]}")
                return False

        # Устанавливаем ffmpeg
        print("   Установка FFmpeg через brew (может занять несколько минут)...")
        code, stdout, stderr = self._run_command(['brew', 'install', 'ffmpeg'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через Homebrew!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_macos_manual(self) -> bool:
        """Ручная установка на macOS"""
        print("📦 Пробуем ручную установку...")

        # Скачиваем pre-built binary для macOS
        url = "https://evermeet.cx/ffmpeg/ffmpeg-6.1.1.zip"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            zip_file = tmp_path / "ffmpeg.zip"

            if not self._download_file(url, zip_file):
                return False

            if not self._extract_zip(zip_file, tmp_path):
                return False

            # Копируем в /usr/local/bin
            install_path = Path("/usr/local/bin")
            if not install_path.exists():
                install_path.mkdir(parents=True, exist_ok=True)

            ffmpeg_file = tmp_path / "ffmpeg"
            if ffmpeg_file.exists():
                shutil.copy2(ffmpeg_file, install_path / "ffmpeg")
                # Делаем исполняемым
                os.chmod(install_path / "ffmpeg", 0o755)
                print(f"✅ FFmpeg установлен в: {install_path}")
                return True

        return False

    def install_linux(self) -> bool:
        """Установка FFmpeg на Linux"""
        print("\n🐧 Установка FFmpeg для Linux...")

        # Определяем дистрибутив
        distro = self._detect_linux_distro()

        methods = {
            'debian': self._install_linux_apt,
            'ubuntu': self._install_linux_apt,
            'centos': self._install_linux_yum,
            'rhel': self._install_linux_yum,
            'fedora': self._install_linux_dnf,
            'arch': self._install_linux_pacman,
        }

        installer = methods.get(distro, self._install_linux_manual)

        if installer():
            return True

        return self._install_linux_manual()

    def _detect_linux_distro(self) -> str:
        """Определяет дистрибутив Linux"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content:
                    return 'ubuntu'
                elif 'debian' in content:
                    return 'debian'
                elif 'centos' in content:
                    return 'centos'
                elif 'rhel' in content:
                    return 'rhel'
                elif 'fedora' in content:
                    return 'fedora'
                elif 'arch' in content:
                    return 'arch'
        except:
            pass

        # Пробуем другие методы
        if shutil.which('apt'):
            return 'debian'
        elif shutil.which('yum'):
            return 'centos'
        elif shutil.which('dnf'):
            return 'fedora'
        elif shutil.which('pacman'):
            return 'arch'

        return 'unknown'

    def _install_linux_apt(self) -> bool:
        """Установка через apt (Debian/Ubuntu)"""
        print("📦 Установка через apt...")

        # Обновляем репозитории
        print("   Обновление репозиториев...")
        code, _, _ = self._run_command(['sudo', 'apt', 'update'])
        if code != 0:
            print("   Не удалось обновить репозитории")
            return False

        # Устанавливаем ffmpeg
        print("   Установка FFmpeg...")
        code, stdout, stderr = self._run_command(['sudo', 'apt', 'install', '-y', 'ffmpeg'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через apt!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_linux_yum(self) -> bool:
        """Установка через yum (CentOS/RHEL)"""
        print("📦 Установка через yum...")

        # Добавляем EPEL репозиторий
        print("   Добавление EPEL репозитория...")
        self._run_command(['sudo', 'yum', 'install', '-y', 'epel-release'])

        # Устанавливаем ffmpeg
        print("   Установка FFmpeg...")
        code, stdout, stderr = self._run_command(['sudo', 'yum', 'install', '-y', 'ffmpeg'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через yum!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_linux_dnf(self) -> bool:
        """Установка через dnf (Fedora)"""
        print("📦 Установка через dnf...")

        # Добавляем RPM Fusion репозиторий
        print("   Добавление RPM Fusion репозитория...")
        self._run_command(['sudo', 'dnf', 'install', '-y',
                           'https://download1.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm'])

        # Устанавливаем ffmpeg
        print("   Установка FFmpeg...")
        code, stdout, stderr = self._run_command(['sudo', 'dnf', 'install', '-y', 'ffmpeg'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через dnf!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_linux_pacman(self) -> bool:
        """Установка через pacman (Arch Linux)"""
        print("📦 Установка через pacman...")

        # Устанавливаем ffmpeg
        code, stdout, stderr = self._run_command(['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'])

        if code == 0:
            print("✅ FFmpeg успешно установлен через pacman!")
            return True
        else:
            print(f"   Ошибка установки: {stderr[:200]}")
            return False

    def _install_linux_manual(self) -> bool:
        """Ручная установка на Linux (сборка из исходников)"""
        print("📦 Пробуем ручную установку (сборка из исходников)...")

        # Устанавливаем зависимости для сборки
        if shutil.which('apt'):
            self._run_command(
                ['sudo', 'apt', 'install', '-y', 'build-essential', 'yasm', 'libx264-dev', 'libmp3lame-dev'])
        elif shutil.which('yum'):
            self._run_command(['sudo', 'yum', 'groupinstall', '-y', 'Development Tools'])
            self._run_command(['sudo', 'yum', 'install', '-y', 'yasm'])

        # Скачиваем исходники
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_url = "https://ffmpeg.org/releases/ffmpeg-6.1.1.tar.xz"
            source_file = tmp_path / "ffmpeg.tar.xz"

            if not self._download_file(source_url, source_file):
                return False

            # Распаковываем
            if not self._extract_tar(source_file, tmp_path):
                return False

            # Находим папку с исходниками
            source_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and 'ffmpeg' in d.name.lower()]
            if not source_dirs:
                return False

            source_dir = source_dirs[0]

            # Компиляция и установка
            os.chdir(source_dir)

            print("   Конфигурация сборки...")
            self._run_command(['./configure', '--enable-gpl', '--enable-libx264', '--enable-libmp3lame'])

            print("   Компиляция (может занять 10-15 минут)...")
            code, _, _ = self._run_command(['make', '-j4'])

            if code != 0:
                print("   Ошибка компиляции")
                return False

            print("   Установка...")
            code, _, _ = self._run_command(['sudo', 'make', 'install'])

            if code == 0:
                print("✅ FFmpeg успешно собран и установлен!")
                return True

        return False

    def verify_installation(self) -> bool:
        """Проверяет успешность установки FFmpeg"""
        print("\n🔍 Проверка установки FFmpeg...")

        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg установлен: {version_line[:100]}")
                return True
            else:
                print("❌ FFmpeg не найден в PATH")
                return False
        except FileNotFoundError:
            print("❌ FFmpeg не найден в PATH")
            return False

    def install(self) -> bool:
        """Основной метод установки"""
        print(f"\n{'=' * 50}")
        print(f"🎬 FFmpeg Auto-Installer")
        print(f"📊 Система: {self.system} ({self.arch})")
        print(f"🔑 Админ права: {'Да' if self.is_admin else 'Нет'}")
        print(f"{'=' * 50}")

        if self.system == 'windows':
            success = self.install_windows()
        elif self.system == 'darwin':
            success = self.install_macos()
        elif self.system == 'linux':
            success = self.install_linux()
        else:
            print(f"❌ Неподдерживаемая ОС: {self.system}")
            return False

        if success:
            # Проверяем установку
            if self.verify_installation():
                print("\n✨ Установка FFmpeg завершена успешно!")
                print("\n💡 Совет: Перезапустите терминал, чтобы изменения PATH вступили в силу")
                return True
            else:
                print("\n⚠️ Установка завершена, но FFmpeg не найден в PATH")
                print("   Попробуйте перезапустить терминал или добавить FFmpeg в PATH вручную")
                return False

        return False


def main():
    """Основная функция"""
    installer = FFmpegInstaller()

    if installer.install():
        sys.exit(0)
    else:
        print("\n❌ Не удалось установить FFmpeg")
        print("\n📖 Ручная установка:")
        print("   Windows: https://ffmpeg.org/download.html#build-windows")
        print("   macOS:   brew install ffmpeg")
        print("   Linux:   sudo apt install ffmpeg  (или аналогично для вашего дистрибутива)")
        sys.exit(1)


if __name__ == "__main__":
    main()
