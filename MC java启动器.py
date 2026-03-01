#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import subprocess
import urllib.request
import urllib.parse
import zipfile
import platform
from pathlib import Path

# ==================== Python 环境自举（仅 Windows）- 自动下载最新版 ====================
def get_latest_python_version():
    """获取最新的Python版本号"""
    try:
        url = "https://www.python.org/downloads/"
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode('utf-8')
            import re
            match = re.search(r'Python (\d+\.\d+\.\d+)', html)
            if match:
                return match.group(1)
    except:
        pass
    return "3.12.2"

def get_python_download_url(version, arch_bits):
    """获取Python下载链接"""
    system = platform.system().lower()
    
    if system == "windows":
        if arch_bits == "64":
            return f"https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip"
        else:
            return f"https://www.python.org/ftp/python/{version}/python-{version}-embed-win32.zip"
    return None

def ensure_python():
    if platform.system() != "Windows":
        if sys.version_info < (3, 6):
            print("错误：需要 Python 3.6 或更高版本。请安装后重试。")
            sys.exit(1)
        return
    
    if sys.version_info >= (3, 6):
        return
    
    print("=" * 60)
    print("🎮 Minecraft 启动器 - 环境准备")
    print("=" * 60)
    print("📢 检测到当前 Python 版本过低，正在准备自动下载最新版...")
    
    python_version = get_latest_python_version()
    arch_bits = "64" if platform.machine().endswith("64") else "32"
    
    download_url = get_python_download_url(python_version, arch_bits)
    if not download_url:
        print("❌ 无法获取 Python 下载链接，请手动安装 Python 3.6+")
        sys.exit(1)
    
    target_dir = Path.cwd() / "python_embed"
    filename = f"python-{python_version}-embed-{'amd64' if arch_bits == '64' else 'win32'}.zip"
    target_zip = target_dir / filename
    target_dir.mkdir(exist_ok=True)
    
    print(f"📦 Python 版本: {python_version}")
    print(f"🖥️  系统架构: {arch_bits}位")
    print("⏳ 正在下载，请稍候...")
    
    try:
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(target_zip, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if total_size > 0:
                        percent = downloaded * 100 / total_size
                        bar_length = 40
                        filled = int(bar_length * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        sys.stdout.write(f'\r📥 下载进度: |{bar}| {percent:.1f}% ({downloaded}/{total_size} bytes)')
                        sys.stdout.flush()
            print()
    except Exception as e:
        print(f"\n❌ 下载失败：{e}")
        sys.exit(1)
    
    print("📂 正在解压文件...")
    try:
        with zipfile.ZipFile(target_zip, 'r') as zf:
            members = zf.infolist()
            total_files = len(members)
            for i, member in enumerate(members, 1):
                zf.extract(member, target_dir)
                if i % 10 == 0 or i == total_files:
                    percent = i * 100 / total_files
                    bar_length = 30
                    filled = int(bar_length * i / total_files)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    sys.stdout.write(f'\r📦 解压进度: |{bar}| {percent:.1f}% ({i}/{total_files} 文件)')
                    sys.stdout.flush()
        print()
    except Exception as e:
        print(f"\n❌ 解压失败：{e}")
        sys.exit(1)
    
    target_zip.unlink()
    
    python_exe = target_dir / "python.exe"
    if not python_exe.exists():
        print("❌ 解压后未找到 python.exe")
        sys.exit(1)
    
    # 配置pip
    pth_file = target_dir / "python._pth"
    with open(pth_file, 'w') as f:
        f.write("python.zip\n.\n\nimport site\n")
    
    print("✅ Python 环境准备就绪！")
    print("🔄 正在重新启动启动器...\n")
    
    # 修复中文路径问题：使用绝对路径并用引号包裹
    script_path = str(Path(__file__).absolute())
    # 在Windows上，如果路径包含空格或中文，需要用引号包裹
    if platform.system() == "Windows" and (' ' in script_path or any(ord(c) > 127 for c in script_path)):
        script_path = f'"{script_path}"'
    
    subprocess.run(f'{str(python_exe)} {script_path} {" ".join(sys.argv[1:])}', shell=True)
    sys.exit(0)

ensure_python()

# ==================== 标准库导入 ====================
import json
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import shutil
import hashlib
import zipfile
import tarfile
import platform
import uuid
import time
import logging
import re
import tempfile
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 控制台颜色 ====================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('minecraft_launcher.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== 全局变量 ====================
_shutdown_requested = False

def set_shutdown_flag(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    print(f"\n{Colors.WARNING}⚠ 正在停止所有任务，请稍候...{Colors.ENDC}")

if platform.system() != "Windows":
    signal.signal(signal.SIGINT, set_shutdown_flag)
    signal.signal(signal.SIGTERM, set_shutdown_flag)

# ==================== 辅助函数 ====================
def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def clear_screen():
    """清屏"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_header(title):
    """打印标题"""
    print(f"{Colors.CYAN}{Colors.BOLD}╔{'═' * 58}╗{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.ENDC}{' ' * 20}{Colors.BOLD}{title}{Colors.ENDC}{' ' * (38 - len(title))}{Colors.CYAN}{Colors.BOLD}║{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚{'═' * 58}╝{Colors.ENDC}")

def print_menu_item(num, text, desc=""):
    """打印菜单项"""
    print(f"  {Colors.GREEN}[{num}]{Colors.ENDC} {Colors.BOLD}{text}{Colors.ENDC}")
    if desc:
        print(f"     {Colors.BLUE}└─ {desc}{Colors.ENDC}")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def print_progress(current, total, prefix="进度"):
    """打印进度条"""
    bar_length = 40
    percent = current * 100 / total
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    sys.stdout.write(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()

def download_with_progress(url: str, dest: Path, description: str = "下载中"):
    global _shutdown_requested
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp_dest = dest.with_suffix('.tmp')
            
            with open(temp_dest, 'wb') as f:
                while True:
                    if _shutdown_requested:
                        raise KeyboardInterrupt("用户中断下载")
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if total_size > 0:
                        percent = min(downloaded * 100 / total_size, 100)
                        bar_length = 30
                        filled = int(bar_length * downloaded / total_size)
                        bar = '█' * filled + '─' * (bar_length - filled)
                        sys.stdout.write(f'\r{description}: |{bar}| {percent:.1f}% ({format_size(downloaded)}/{format_size(total_size)})')
                        sys.stdout.flush()
            
            if _shutdown_requested:
                temp_dest.unlink(missing_ok=True)
                raise KeyboardInterrupt("用户中断下载")
            shutil.move(str(temp_dest), str(dest))
            print()
    except Exception as e:
        temp_dest = dest.with_suffix('.tmp')
        temp_dest.unlink(missing_ok=True)
        raise e

# ==================== 数据类定义 ====================
@dataclass
class UserAccount:
    username: str
    uuid: str = ""
    access_token: str = ""
    account_type: str = "offline"
    last_login: str = ""
    skin_url: str = ""
    last_played: str = ""

@dataclass
class MemoryConfig:
    max_memory: str = "2G"
    min_memory: str = "1G"
    auto_allocate: bool = True

@dataclass
class MinecraftVersion:
    id: str
    type: str
    url: str
    time: str
    releaseTime: str

@dataclass
class Modpack:
    """整合包信息"""
    name: str
    version: str
    minecraft_version: str
    modloader: str  # forge, fabric, quilt
    modloader_version: str
    description: str = ""
    author: str = ""
    url: str = ""
    icon: str = ""
    installed_path: str = ""
    install_date: str = ""

@dataclass
class Datapack:
    """数据包信息"""
    name: str
    version: str
    minecraft_version: str
    description: str = ""
    author: str = ""
    url: str = ""
    filename: str = ""
    installed_path: str = ""
    install_date: str = ""
    enabled: bool = True

@dataclass
class LauncherConfig:
    java_path: str = "java"
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    game_arguments: str = ""
    last_version: str = ""
    auto_update: bool = True
    theme: str = "dark"
    minecraft_data_path: str = str(Path.home() / ".minecraft")
    mods_folder: str = "mods"
    resource_packs_folder: str = "resourcepacks"
    shaderpacks_folder: str = "shaderpacks"
    modpacks_folder: str = "modpacks"
    datapacks_folder: str = "datapacks"
    download_folder: str = "downloads"
    accounts: List[UserAccount] = field(default_factory=list)
    current_account: Optional[str] = None
    show_console: bool = False
    game_resolution: str = "854x480"
    use_smooth_scrolling: bool = True
    modpacks: List[Modpack] = field(default_factory=list)
    datapacks: List[Datapack] = field(default_factory=list)

# ==================== Minecraft 启动器核心类 ====================
class MinecraftLauncher:
    def __init__(self):
        self.config_file = Path("minecraft_launcher_config.json")
        self.config = self.load_config()
        self.versions_manifest = None
        self.all_versions = []
        self.installed_versions = []
        self.system_info = self.get_system_info()
        self.download_speed = 0
        self.refresh_installed_versions()
        self.refresh_online_versions()
        self.create_default_folders()

    def create_default_folders(self):
        """创建默认文件夹"""
        folders = [
            Path(self.config.minecraft_data_path) / self.config.mods_folder,
            Path(self.config.minecraft_data_path) / self.config.resource_packs_folder,
            Path(self.config.minecraft_data_path) / self.config.shaderpacks_folder,
            Path(self.config.minecraft_data_path) / self.config.modpacks_folder,
            Path(self.config.minecraft_data_path) / self.config.datapacks_folder,
            Path(self.config.minecraft_data_path) / "versions",
            Path(self.config.minecraft_data_path) / "libraries",
            Path(self.config.minecraft_data_path) / "assets",
            Path(self.config.minecraft_data_path) / "runtime",
            Path(self.config.minecraft_data_path) / "screenshots",
            Path(self.config.minecraft_data_path) / "logs",
            Path(self.config.minecraft_data_path) / "crash-reports",
            Path(self.config.minecraft_data_path) / "saves",
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    # -------------------- 配置管理 --------------------
    def load_config(self) -> LauncherConfig:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "memory" in data and isinstance(data["memory"], dict):
                    data["memory"] = MemoryConfig(**data["memory"])
                if "accounts" in data:
                    data["accounts"] = [UserAccount(**acc) for acc in data["accounts"]]
                if "modpacks" in data:
                    data["modpacks"] = [Modpack(**mp) for mp in data["modpacks"]]
                if "datapacks" in data:
                    data["datapacks"] = [Datapack(**dp) for dp in data["datapacks"]]
                return LauncherConfig(**{k: v for k, v in data.items() if k in LauncherConfig.__annotations__})
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
        return LauncherConfig()

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    # -------------------- 系统信息 --------------------
    def get_system_info(self) -> dict:
        arch = platform.architecture()[0]
        os_name = platform.system().lower()
        if os_name == "windows":
            os_name = "windows"
        elif os_name == "darwin":
            os_name = "osx"
        else:
            os_name = "linux"
        return {
            "os": os_name,
            "arch": "64" if "64" in arch else "32",
            "java_path": self.config.java_path
        }

    # -------------------- 版本管理 --------------------
    def refresh_installed_versions(self):
        versions_dir = Path(self.config.minecraft_data_path) / "versions"
        if versions_dir.exists():
            self.installed_versions = sorted([
                v.name for v in versions_dir.iterdir()
                if v.is_dir() and (v / f"{v.name}.json").exists()
            ], reverse=True)
        else:
            self.installed_versions = []

    def refresh_online_versions(self) -> bool:
        try:
            url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            with urllib.request.urlopen(url, timeout=10) as resp:
                self.versions_manifest = json.loads(resp.read().decode("utf-8"))
            self.all_versions = [
                MinecraftVersion(**v) for v in self.versions_manifest["versions"]
            ]
            return True
        except Exception as e:
            logger.error(f"获取版本列表失败: {e}")
            return False

    def get_version_json(self, version_id: str) -> Optional[dict]:
        local_json = Path(self.config.minecraft_data_path) / "versions" / version_id / f"{version_id}.json"
        if local_json.exists():
            try:
                with open(local_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        if not self.all_versions:
            return None
        for v in self.all_versions:
            if v.id == version_id:
                try:
                    with urllib.request.urlopen(v.url, timeout=10) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    local_json.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_json, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    return data
                except Exception as e:
                    logger.error(f"下载版本 JSON 失败: {e}")
                    return None
        return None

    def download_minecraft_version(self, version_id: str) -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return False
        
        print_info(f"开始下载版本 {version_id}")
        version_json = self.get_version_json(version_id)
        if not version_json:
            print_error("无法获取版本信息")
            return False
        
        client_download = version_json.get("downloads", {}).get("client")
        if not client_download:
            print_error("该版本没有客户端下载链接")
            return False
        
        jar_url = client_download["url"]
        jar_sha1 = client_download["sha1"]
        jar_path = Path(self.config.minecraft_data_path) / "versions" / version_id / f"{version_id}.jar"
        jar_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            download_with_progress(jar_url, jar_path, f"📥 下载 {version_id}.jar")
            if _shutdown_requested:
                jar_path.unlink(missing_ok=True)
                return False
            
            with open(jar_path, "rb") as f:
                file_hash = hashlib.sha1(f.read()).hexdigest()
            if file_hash != jar_sha1:
                print_error("文件校验失败")
                jar_path.unlink()
                return False
            
            print_success(f"{version_id} 下载完成")
            self.refresh_installed_versions()
            return True
        except KeyboardInterrupt:
            jar_path.unlink(missing_ok=True)
            raise
        except Exception as e:
            print_error(f"下载失败: {e}")
            return False

    # -------------------- 库文件管理 --------------------
    def parse_library_name(self, name: str) -> Tuple[str, str, str, Optional[str]]:
        parts = name.split(':')
        if len(parts) == 3:
            return parts[0], parts[1], parts[2], None
        elif len(parts) == 4:
            return parts[0], parts[1], parts[2], parts[3]
        else:
            raise ValueError(f"无效的库名称格式: {name}")

    def download_library(self, lib_info: dict) -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return False
        name = lib_info["name"]
        try:
            group, artifact, version, classifier = self.parse_library_name(name)
        except ValueError as e:
            logger.warning(f"库名称解析失败: {e}")
            return False

        base_name = f"{artifact}-{version}"
        if classifier:
            base_name += f"-{classifier}"
        jar_name = base_name + ".jar"

        group_path = group.replace(".", "/")
        lib_path = Path(self.config.minecraft_data_path) / "libraries" / group_path / artifact / version / jar_name

        if lib_path.exists():
            return True

        urls_to_try = []
        if "url" in lib_info:
            urls_to_try.append(lib_info["url"] + f"{group_path}/{artifact}/{version}/{jar_name}")
        urls_to_try.append(f"https://libraries.minecraft.net/{group_path}/{artifact}/{version}/{jar_name}")
        urls_to_try.append(f"https://repo1.maven.org/maven2/{group_path}/{artifact}/{version}/{jar_name}")

        for url in urls_to_try:
            if _shutdown_requested:
                return False
            try:
                lib_path.parent.mkdir(parents=True, exist_ok=True)
                download_with_progress(url, lib_path, f"📚 库 {jar_name[:20]}...")
                return True
            except KeyboardInterrupt:
                lib_path.unlink(missing_ok=True)
                raise
            except Exception as e:
                logger.debug(f"从 {url} 下载失败: {e}")
                continue

        logger.error(f"所有下载源均失败: {name}")
        return False

    def download_libraries(self, version_json: dict) -> bool:
        global _shutdown_requested
        libraries = version_json.get("libraries", [])
        allowed_libs = []
        for lib in libraries:
            rules = lib.get("rules", [])
            allowed = True
            for rule in rules:
                action = rule.get("action", "allow")
                os_rule = rule.get("os", {})
                os_name = os_rule.get("name", "")
                if os_name and os_name != self.system_info["os"]:
                    continue
                if action == "disallow":
                    allowed = False
                    break
                elif action == "allow":
                    allowed = True
            if allowed:
                allowed_libs.append(lib)

        total = len(allowed_libs)
        if total == 0:
            return True

        print_info(f"正在检查/下载库文件 (共 {total} 个)")
        success = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_lib = {executor.submit(self.download_library, lib): lib for lib in allowed_libs}
            for i, future in enumerate(as_completed(future_to_lib), 1):
                if _shutdown_requested:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return False
                lib = future_to_lib[future]
                try:
                    if future.result():
                        success += 1
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"处理库 {lib.get('name')} 时发生异常: {e}")
                print_progress(i, total, "📚 库文件进度")

        print(f"\n{Colors.GREEN}✅ 库文件准备完成: {success}/{total}{Colors.ENDC}")
        return success > 0

    def extract_natives(self, version_json: dict) -> Optional[Path]:
        natives_dir = Path(self.config.minecraft_data_path) / "natives" / version_json["id"]
        if natives_dir.exists():
            shutil.rmtree(natives_dir)
        natives_dir.mkdir(parents=True, exist_ok=True)
        libraries = version_json.get("libraries", [])
        extracted = 0
        for lib in libraries:
            natives = lib.get("natives", {})
            if not natives:
                continue
            classifier = natives.get(self.system_info["os"])
            if not classifier:
                continue
            name_parts = lib["name"].split(":")
            group, artifact, version = name_parts[0], name_parts[1], name_parts[2]
            group_path = group.replace(".", "/")
            jar_name = f"{artifact}-{version}-{classifier}.jar"
            lib_path = Path(self.config.minecraft_data_path) / "libraries" / group_path / artifact / version / jar_name
            if not lib_path.exists():
                lib_with_classifier = lib.copy()
                lib_with_classifier["name"] = f"{group}:{artifact}:{version}:{classifier}"
                if not self.download_library(lib_with_classifier):
                    continue
                lib_path = Path(self.config.minecraft_data_path) / "libraries" / group_path / artifact / version / jar_name
            try:
                with zipfile.ZipFile(lib_path, "r") as zf:
                    for member in zf.namelist():
                        if member.endswith((".dll", ".so", ".dylib")):
                            zf.extract(member, natives_dir)
                extracted += 1
            except Exception as e:
                logger.error(f"解压 natives 失败 {lib_path.name}: {e}")
        if extracted > 0:
            print_info(f"提取了 {extracted} 个 native 库")
        return natives_dir if extracted > 0 else None

    # -------------------- 资源文件管理 --------------------
    def _download_single_asset(self, url: str, path: Path) -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            download_with_progress(url, path, f"🎨 资源 {path.name[:15]}...")
            return True
        except KeyboardInterrupt:
            path.unlink(missing_ok=True)
            raise
        except Exception as e:
            logger.debug(f"下载资源失败 {url}: {e}")
            return False

    def download_assets(self, version_json: dict) -> bool:
        global _shutdown_requested
        asset_index_info = version_json.get("assetIndex", {})
        if not asset_index_info:
            return False
        
        index_url = asset_index_info["url"]
        index_sha1 = asset_index_info["sha1"]
        index_path = Path(self.config.minecraft_data_path) / "assets" / "indexes" / f"{version_json['assets']}.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not index_path.exists():
            try:
                download_with_progress(index_url, index_path, "📑 下载资源索引")
            except Exception as e:
                print_error(f"下载资源索引失败: {e}")
                return False
        
        with open(index_path, "rb") as f:
            if hashlib.sha1(f.read()).hexdigest() != index_sha1:
                print_error("资源索引校验失败")
                index_path.unlink()
                return False
        
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        
        objects = index_data.get("objects", {})
        total = len(objects)
        print_info(f"正在检查资源文件 (共 {total} 个)")

        base_url = "https://resources.download.minecraft.net/"
        success = 0
        tasks = []
        for key, obj in objects.items():
            if _shutdown_requested:
                return False
            hash_val = obj["hash"]
            subdir = hash_val[:2]
            asset_path = Path(self.config.minecraft_data_path) / "assets" / "objects" / subdir / hash_val
            if not asset_path.exists():
                url = base_url + f"{subdir}/{hash_val}"
                tasks.append((key, url, asset_path))
            else:
                success += 1

        total_tasks = len(tasks)
        if total_tasks == 0:
            print_success("所有资源文件已存在")
            return True

        print_info(f"需要下载 {total_tasks} 个资源文件")
        downloaded = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_task = {}
            for key, url, path in tasks:
                if _shutdown_requested:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return False
                future = executor.submit(self._download_single_asset, url, path)
                future_to_task[future] = (key, path)

            for future in as_completed(future_to_task):
                if _shutdown_requested:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return False
                key, path = future_to_task[future]
                try:
                    if future.result():
                        downloaded += 1
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"下载资源异常 {key}: {e}")
                print_progress(downloaded + success, total, "🎨 资源文件进度")

        print(f"\n{Colors.GREEN}✅ 资源文件准备完成: {downloaded + success}/{total}{Colors.ENDC}")
        return True

    # -------------------- Java 管理 --------------------
    def get_java_version_for_minecraft(self, minecraft_version: str) -> int:
        try:
            if minecraft_version.startswith("1."):
                parts = minecraft_version.split(".")
                if len(parts) >= 2:
                    major = int(parts[1])
                    if major <= 16:
                        return 8
                    elif major <= 20:
                        if len(parts) >= 3 and major == 20 and int(parts[2]) >= 5:
                            return 21
                        return 17
                    else:
                        return 21
            return 17
        except:
            return 17

    def get_java_download_url(self, java_version: int) -> Optional[str]:
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        if "arm" in arch or "aarch64" in arch:
            arch_name = "aarch64"
        elif "64" in arch or "x86_64" in arch or "amd64" in arch:
            arch_name = "x64"
        else:
            arch_name = "x86"

        if system == "windows":
            os_name = "windows"
            ext = "zip"
        elif system == "darwin":
            os_name = "mac"
            ext = "tar.gz"
        else:
            os_name = "linux"
            ext = "tar.gz"

        # 使用 Adoptium 的 OpenJDK
        backup_urls = {
            8: f"https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u442-b06/OpenJDK8U-jre_{arch_name}_{os_name}_hotspot_8u442b06.{ext}",
            17: f"https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.14%2B7/OpenJDK17U-jre_{arch_name}_{os_name}_hotspot_17.0.14_7.{ext}",
            21: f"https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.6%2B7/OpenJDK21U-jre_{arch_name}_{os_name}_hotspot_21.0.6_7.{ext}"
        }
        
        # 尝试从 Adoptium 获取
        api_url = f"https://api.adoptium.net/v3/assets/latest/{java_version}/hotspot"
        params = f"?os={os_name}&architecture={arch_name}&image_type=jre"
        try:
            url = f"{api_url}{params}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                binary = data[0].get("binary", {})
                package = binary.get("package", {})
                download_url = package.get("link")
                if download_url:
                    return download_url
        except:
            pass
        
        return backup_urls.get(java_version)

    def find_java_in_path(self) -> Optional[Path]:
        """在系统PATH中查找Java"""
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                if platform.system() == "Windows":
                    result = subprocess.run(["where", "java"], capture_output=True, text=True, timeout=5)
                else:
                    result = subprocess.run(["which", "java"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return Path(result.stdout.strip().split('\n')[0])
        except:
            pass
        return None

    def find_java_in_common_locations(self) -> Optional[Path]:
        """在常见的Java安装位置查找"""
        system = platform.system()
        common_paths = []
        
        if system == "Windows":
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
            common_paths = [
                Path(program_files) / "Java" / "jre*" / "bin" / "java.exe",
                Path(program_files) / "Java" / "jdk*" / "bin" / "java.exe",
                Path(program_files_x86) / "Java" / "jre*" / "bin" / "java.exe",
                Path(program_files_x86) / "Java" / "jdk*" / "bin" / "java.exe",
                Path("C:\\") / "Java" / "jre*" / "bin" / "java.exe",
                Path("C:\\") / "Java" / "jdk*" / "bin" / "java.exe",
            ]
        elif system == "Darwin":
            common_paths = [
                Path("/Library/Java/JavaVirtualMachines") / "*" / "Contents/Home/bin/java",
                Path("/System/Library/Java/JavaVirtualMachines") / "*" / "Contents/Home/bin/java",
            ]
        else:
            common_paths = [
                Path("/usr/lib/jvm") / "*" / "bin/java",
                Path("/usr/java") / "*" / "bin/java",
                Path("/opt") / "*" / "bin/java",
            ]

        for pattern in common_paths:
            try:
                matches = list(Path("/").glob(str(pattern).lstrip('/'))) if str(pattern).startswith('/') else list(Path().glob(str(pattern)))
                for match in matches:
                    if match.exists() and os.access(match, os.X_OK):
                        return match
            except:
                continue
        return None

    def download_java(self, java_version: int) -> Optional[Path]:
        global _shutdown_requested
        java_dir = Path(self.config.minecraft_data_path) / "runtime" / f"java{java_version}"
        java_exe = java_dir / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        
        if java_exe.exists():
            logger.info(f"Java {java_version} 已存在: {java_exe}")
            return java_exe

        print_info(f"正在下载 Java {java_version}（首次使用需要下载）")
        java_dir.mkdir(parents=True, exist_ok=True)

        download_url = self.get_java_download_url(java_version)
        if not download_url:
            print_error(f"无法获取 Java {java_version} 下载链接")
            return None

        temp_dir = Path(tempfile.gettempdir()) / "minecraft_java_download"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / f"java{java_version}.tmp"

        try:
            download_with_progress(download_url, temp_file, f"☕ 下载 Java {java_version}")
            if _shutdown_requested:
                temp_file.unlink(missing_ok=True)
                return None
            print("📦 下载完成，正在解压...")

            if download_url.endswith(".zip"):
                with zipfile.ZipFile(temp_file, "r") as zf:
                    root_dirs = set()
                    for name in zf.namelist():
                        if "/" in name:
                            root_dirs.add(name.split("/")[0])
                    extract_dir = temp_dir / "extracted"
                    if extract_dir.exists():
                        shutil.rmtree(extract_dir)
                    zf.extractall(extract_dir)
                    
                    if len(root_dirs) == 1:
                        src_dir = extract_dir / list(root_dirs)[0]
                        for item in src_dir.iterdir():
                            dest = java_dir / item.name
                            if dest.exists():
                                if dest.is_dir():
                                    shutil.rmtree(dest)
                                else:
                                    dest.unlink()
                            shutil.move(str(item), str(dest))
                    else:
                        for item in extract_dir.iterdir():
                            dest = java_dir / item.name
                            shutil.move(str(item), str(dest))
            else:
                with tarfile.open(temp_file, "r:gz") as tf:
                    members = tf.getmembers()
                    root_dirs = set()
                    for m in members:
                        if "/" in m.name:
                            root_dirs.add(m.name.split("/")[0])
                    extract_dir = temp_dir / "extracted"
                    if extract_dir.exists():
                        shutil.rmtree(extract_dir)
                    tf.extractall(extract_dir)
                    
                    if len(root_dirs) == 1:
                        src_dir = extract_dir / list(root_dirs)[0]
                        for item in src_dir.iterdir():
                            dest = java_dir / item.name
                            shutil.move(str(item), str(dest))
                    else:
                        for item in extract_dir.iterdir():
                            dest = java_dir / item.name
                            shutil.move(str(item), str(dest))

            temp_file.unlink(missing_ok=True)
            shutil.rmtree(temp_dir, ignore_errors=True)

            if platform.system() != "Windows":
                java_exe.chmod(0o755)

            print_success(f"Java {java_version} 安装完成")
            return java_exe

        except KeyboardInterrupt:
            temp_file.unlink(missing_ok=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        except Exception as e:
            logger.error(f"Java 下载失败: {e}")
            print_error(f"Java 下载失败: {e}")
            return None
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def ensure_java_for_version(self, minecraft_version: str) -> Tuple[bool, str, Optional[Path]]:
        required_java = self.get_java_version_for_minecraft(minecraft_version)
        
        # 第一次检测：配置的Java路径
        try:
            result = subprocess.run([self.config.java_path, "-version"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_output = result.stderr
                match = re.search(r'version "(\d+)', version_output)
                if match:
                    current_java = int(match.group(1))
                    if "1.8" in version_output:
                        current_java = 8
                    if current_java == required_java:
                        return True, f"使用系统 Java {required_java}", Path(self.config.java_path)
        except:
            pass

        # 第二次检测：内置Java
        java_exe = Path(self.config.minecraft_data_path) / "runtime" / f"java{required_java}" / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        if java_exe.exists():
            try:
                result = subprocess.run([str(java_exe), "-version"],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return True, f"使用内置 Java {required_java}", java_exe
            except:
                pass

        # 第三次检测：PATH中的Java
        path_java = self.find_java_in_path()
        if path_java:
            try:
                result = subprocess.run([str(path_java), "-version"],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    version_output = result.stderr
                    if "1.8" in version_output or str(required_java) in version_output:
                        return True, f"使用系统 PATH 中的 Java", path_java
            except:
                pass

        # 第四次检测：常见安装位置
        common_java = self.find_java_in_common_locations()
        if common_java:
            try:
                result = subprocess.run([str(common_java), "-version"],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    version_output = result.stderr
                    if "1.8" in version_output or str(required_java) in version_output:
                        return True, f"使用系统已安装的 Java", common_java
            except:
                pass

        # 第五次：下载Java
        print_warning(f"需要 Java {required_java} 才能运行 Minecraft {minecraft_version}")
        downloaded = self.download_java(required_java)
        if downloaded and downloaded.exists():
            return True, f"已下载 Java {required_java}", downloaded
        else:
            # 最后尝试：直接使用系统默认Java
            print_warning("将尝试使用系统默认 Java 启动，可能因版本不匹配而无法运行")
            try:
                result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return True, "尝试使用系统默认 Java", Path("java")
            except:
                pass
            
            return True, "尝试直接启动", Path(self.config.java_path)

    # -------------------- 登录认证 --------------------
    def get_current_account(self) -> Optional[UserAccount]:
        if not self.config.current_account:
            return None
        for acc in self.config.accounts:
            if acc.username == self.config.current_account:
                return acc
        return None

    def offline_login(self, username: str) -> UserAccount:
        offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username)).replace("-", "")
        account = UserAccount(
            username=username,
            uuid=offline_uuid,
            access_token="",
            account_type="offline",
            last_login=datetime.now().isoformat()
        )
        self.config.accounts.append(account)
        self.config.current_account = username
        self.save_config()
        return account

    # -------------------- 构建启动命令 --------------------
    def build_java_command(self, version_id: str, account: UserAccount, modpack: Optional[Modpack] = None) -> Optional[List[str]]:
        global _shutdown_requested
        if _shutdown_requested:
            return None
        
        version_json = self.get_version_json(version_id)
        if not version_json:
            print_error("无法获取版本信息")
            return None

        print_info("正在准备库文件...")
        if not self.download_libraries(version_json):
            print_error("库文件准备失败")
            return None

        natives_dir = self.extract_natives(version_json)

        print_info("正在准备资源文件...")
        if not self.download_assets(version_json):
            print_error("资源文件准备失败")
            return None

        classpath = []
        libraries = version_json.get("libraries", [])
        for lib in libraries:
            rules = lib.get("rules", [])
            allowed = True
            for rule in rules:
                action = rule.get("action", "allow")
                os_rule = rule.get("os", {})
                name = os_rule.get("name", "")
                if name and name != self.system_info["os"]:
                    continue
                if action == "disallow":
                    allowed = False
                    break
                elif action == "allow":
                    allowed = True
            if not allowed:
                continue
            try:
                group, artifact, version, classifier = self.parse_library_name(lib["name"])
            except ValueError:
                continue
            base_name = f"{artifact}-{version}"
            if classifier:
                base_name += f"-{classifier}"
            jar_name = base_name + ".jar"
            group_path = group.replace(".", "/")
            lib_path = Path(self.config.minecraft_data_path) / "libraries" / group_path / artifact / version / jar_name
            if lib_path.exists():
                classpath.append(str(lib_path))

        client_jar = Path(self.config.minecraft_data_path) / "versions" / version_id / f"{version_id}.jar"
        if client_jar.exists():
            classpath.append(str(client_jar))
        else:
            print_error("客户端 jar 不存在")
            return None

        mem = self.config.memory
        jvm_args = [f"-Xms{mem.min_memory}", f"-Xmx{mem.max_memory}"]
        if natives_dir:
            jvm_args.append(f"-Djava.library.path={natives_dir}")

        # 添加游戏窗口设置
        if self.config.game_resolution:
            width, height = self.config.game_resolution.split('x')
            jvm_args.append(f"-Dminecraft.resolution={width}x{height}")

        if not self.config.show_console:
            jvm_args.append("-Dlog4j2.formatMsgNoLookups=true")

        main_class = version_json.get("mainClass", "net.minecraft.client.main.Main")

        mc_args = []
        if "minecraftArguments" in version_json:
            args_template = version_json["minecraftArguments"]
            replacements = {
                "${auth_player_name}": account.username,
                "${version_name}": version_id,
                "${game_directory}": str(Path(self.config.minecraft_data_path)),
                "${assets_root}": str(Path(self.config.minecraft_data_path) / "assets"),
                "${assets_index_name}": version_json["assets"],
                "${auth_uuid}": account.uuid,
                "${auth_access_token}": account.access_token or "0",
                "${user_properties}": "{}",
                "${user_type}": "mojang" if account.account_type == "microsoft" else "legacy",
                "${version_type}": version_json.get("type", "release"),
                "${auth_session}": account.access_token or "",
                "${game_assets}": str(Path(self.config.minecraft_data_path) / "assets" / "virtual" / "legacy")
            }
            for key, value in replacements.items():
                args_template = args_template.replace(key, value)
            mc_args = args_template.split()
        elif "arguments" in version_json:
            game_args = version_json["arguments"].get("game", [])
            jvm_args_from_json = version_json["arguments"].get("jvm", [])
            for arg in jvm_args_from_json:
                if isinstance(arg, dict):
                    continue
                else:
                    jvm_args.append(arg)
            for arg in game_args:
                if isinstance(arg, dict):
                    continue
                arg = arg.replace("${auth_player_name}", account.username)
                arg = arg.replace("${version_name}", version_id)
                arg = arg.replace("${game_directory}", str(Path(self.config.minecraft_data_path)))
                arg = arg.replace("${assets_root}", str(Path(self.config.minecraft_data_path) / "assets"))
                arg = arg.replace("${assets_index_name}", version_json["assets"])
                arg = arg.replace("${auth_uuid}", account.uuid)
                arg = arg.replace("${auth_access_token}", account.access_token or "0")
                arg = arg.replace("${user_properties}", "{}")
                arg = arg.replace("${user_type}", "mojang" if account.account_type == "microsoft" else "legacy")
                arg = arg.replace("${version_type}", version_json.get("type", "release"))
                mc_args.append(arg)

        cmd = [self.config.java_path] + jvm_args + ["-cp", (";" if platform.system() == "Windows" else ":").join(classpath)] + [main_class] + mc_args
        return cmd

    # -------------------- 启动游戏 --------------------
    def launch_minecraft(self, version_id: str, modpack: Optional[Modpack] = None) -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return False
        
        account = self.get_current_account()
        if not account:
            print_warning("请先登录")
            self.login_screen()
            account = self.get_current_account()
            if not account:
                return False

        version_path = Path(self.config.minecraft_data_path) / "versions" / version_id / f"{version_id}.jar"
        if not version_path.exists():
            print_info(f"版本 {version_id} 未下载，正在下载...")
            if not self.download_minecraft_version(version_id):
                return False

        print_info("正在检查 Java 环境...")
        java_ok, java_msg, java_path = self.ensure_java_for_version(version_id)
        print_info(f"Java 检查: {java_msg}")

        original_java_path = self.config.java_path
        self.config.java_path = str(java_path)

        try:
            print_info("正在构建启动命令...")
            cmd = self.build_java_command(version_id, account, modpack)
            if not cmd:
                return False

            logger.debug("启动命令: " + " ".join(cmd))
            
            if self.config.show_console:
                subprocess.Popen(cmd, cwd=self.config.minecraft_data_path)
            else:
                startupinfo = None
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen(cmd, cwd=self.config.minecraft_data_path, startupinfo=startupinfo)
            
            print_success("游戏已启动")
            return True
        except Exception as e:
            logger.error(f"启动失败: {e}")
            print_error(f"启动失败: {e}")
            return False
        finally:
            self.config.java_path = original_java_path

    # ==================== 数据包管理 ====================
    def datapack_manager(self):
        """数据包管理界面"""
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        datapacks_dir.mkdir(parents=True, exist_ok=True)
        
        # 同时扫描所有存档中的数据包
        saves_dir = Path(self.config.minecraft_data_path) / "saves"
        world_datapacks = {}
        if saves_dir.exists():
            for world in saves_dir.iterdir():
                if world.is_dir():
                    world_dp_dir = world / "datapacks"
                    if world_dp_dir.exists():
                        world_datapacks[world.name] = list(world_dp_dir.glob("*.zip")) + list(world_dp_dir.glob("*.disabled"))
        
        while True:
            clear_screen()
            print_header("数据包管理")
            
            # 显示全局数据包
            global_packs = list(datapacks_dir.glob("*.zip")) + list(datapacks_dir.glob("*.disabled"))
            enabled_global = [p for p in global_packs if not p.name.endswith('.disabled')]
            disabled_global = [p for p in global_packs if p.name.endswith('.disabled')]
            
            print(f"\n{Colors.CYAN}全局数据包 (可应用于所有世界):{Colors.ENDC}")
            print(f"  📦 已启用: {len(enabled_global)} | 已禁用: {len(disabled_global)}")
            
            if global_packs:
                for i, pack in enumerate(global_packs, 1):
                    status = f"{Colors.GREEN}[启用]{Colors.ENDC}" if not pack.name.endswith('.disabled') else f"{Colors.WARNING}[禁用]{Colors.ENDC}"
                    size = format_size(pack.stat().st_size)
                    print(f"  {i:2d}. {pack.name} {status} ({size})")
            else:
                print(f"  {Colors.BLUE}暂无全局数据包{Colors.ENDC}")
            
            # 显示世界数据包
            if world_datapacks:
                print(f"\n{Colors.CYAN}世界数据包:{Colors.ENDC}")
                for world_name, packs in world_datapacks.items():
                    if packs:
                        print(f"  📂 {world_name}:")
                        for pack in packs[:3]:
                            status = f"{Colors.GREEN}[启用]{Colors.ENDC}" if not pack.name.endswith('.disabled') else f"{Colors.WARNING}[禁用]{Colors.ENDC}"
                            print(f"     - {pack.name} {status}")
                        if len(packs) > 3:
                            print(f"     ... 还有 {len(packs) - 3} 个")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "安装数据包", "从本地或网络安装")
            print_menu_item("2", "搜索数据包", "从 Modrinth 搜索")
            print_menu_item("3", "启用/禁用数据包", "切换数据包状态")
            print_menu_item("4", "删除数据包", "删除选中的数据包")
            print_menu_item("5", "安装到世界", "将数据包安装到指定世界")
            print_menu_item("6", "打开数据包文件夹", "在资源管理器中打开")
            print_menu_item("7", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                self.install_datapack()
            elif choice == "2":
                self.search_datapacks()
            elif choice == "3":
                self.toggle_datapack()
            elif choice == "4":
                self.delete_datapack()
            elif choice == "5":
                self.install_datapack_to_world()
            elif choice == "6":
                self.open_folder(datapacks_dir)
            elif choice == "7":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def install_datapack(self):
        """安装数据包"""
        print_info("请选择安装方式:")
        print("  1. 从本地文件导入")
        print("  2. 输入下载链接")
        print("  0. 返回")
        
        choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
        
        if choice == "1":
            self.import_datapack()
        elif choice == "2":
            url = input("请输入数据包下载链接: ").strip()
            if url:
                self.download_datapack(url)
        elif choice == "0":
            return

    def import_datapack(self):
        """从本地导入数据包"""
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        
        print_info("请将数据包文件放入以下文件夹：")
        print(f"  {datapacks_dir}")
        
        # 列出已有文件
        files = list(datapacks_dir.glob("*.zip"))
        if files:
            print(f"\n{Colors.CYAN}检测到以下文件:{Colors.ENDC}")
            for i, f in enumerate(files, 1):
                size = format_size(f.stat().st_size)
                print(f"  {i:2d}. {f.name} ({size})")
            
            choice = input(f"\n{Colors.BLUE}请选择要导入的文件编号 (0手动输入路径): {Colors.ENDC}").strip()
            if choice != "0" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    self.process_datapack(files[idx])
                    return
        
        # 手动输入路径
        path = input("请输入数据包文件路径: ").strip()
        if path and Path(path).exists():
            filename = Path(path).name
            dest = datapacks_dir / filename
            shutil.copy2(path, dest)
            self.process_datapack(dest)
        else:
            print_error("文件不存在")

    def search_datapacks(self):
        """搜索数据包"""
        query = input("请输入数据包名称: ").strip()
        if not query:
            return
        
        print_info(f"正在从 Modrinth 搜索数据包 '{query}'...")
        try:
            encoded_query = urllib.parse.quote(query)
            facets = '[[\"project_type:mod\"]]'
            encoded_facets = urllib.parse.quote(facets)
            url = f"https://api.modrinth.com/v2/search?query={encoded_query}&facets={encoded_facets}&limit=10"
            
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            hits = data.get("hits", [])
            if not hits:
                print_warning("未找到相关内容")
                input("\n按回车键继续...")
                return

            print(f"\n{Colors.CYAN}找到 {len(hits)} 个可能的数据包:{Colors.ENDC}")
            for i, item in enumerate(hits, 1):
                title = item.get('title', '未知')
                author = item.get('author', '未知')
                desc = item.get('description', '无描述')[:80]
                print(f"  {Colors.GREEN}{i:2d}.{Colors.ENDC} {Colors.BOLD}{title}{Colors.ENDC}")
                print(f"     作者: {author}")
                print(f"     描述: {desc}...")
            
            print_warning("注意：部分结果可能不是数据包，请仔细确认")
            
            choice = input(f"\n{Colors.BLUE}请选择要下载的编号 (0返回): {Colors.ENDC}").strip()
            if choice != "0" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(hits):
                    self.download_datapack_from_modrinth(hits[idx])
        except Exception as e:
            print_error(f"搜索失败: {e}")
            input("\n按回车键继续...")

    def download_datapack_from_modrinth(self, project_info: dict):
        """从 Modrinth 下载数据包"""
        slug = project_info.get('slug')
        if not slug:
            print_error("无法获取项目标识")
            return
        
        title = project_info.get('title', slug)
        print_info(f"正在获取 {title} 的版本信息...")
        
        try:
            url = f"https://api.modrinth.com/v2/project/{slug}/version"
            with urllib.request.urlopen(url, timeout=10) as resp:
                versions = json.loads(resp.read().decode("utf-8"))
            
            if not versions:
                print_warning("无可用版本")
                return
            
            print(f"\n{Colors.CYAN}可用版本:{Colors.ENDC}")
            for i, ver in enumerate(versions[:10], 1):
                game_versions = ', '.join(ver.get('game_versions', [])[:3])
                loaders = ', '.join(ver.get('loaders', [])[:3])
                print(f"  {i:2d}. {ver.get('version_number', '未知')}")
                print(f"     Minecraft: {game_versions}")
                print(f"     加载器: {loaders}")
            
            choice = input(f"\n{Colors.BLUE}请选择版本编号 (0返回): {Colors.ENDC}").strip()
            if choice == "0" or not choice.isdigit():
                return
            
            idx = int(choice) - 1
            if idx < 0 or idx >= len(versions):
                return
            
            version = versions[idx]
            files = version.get('files', [])
            if not files:
                print_warning("该版本无可用文件")
                return
            
            file_info = files[0]
            download_url = file_info.get('url')
            filename = file_info.get('filename')
            
            if not download_url or not filename:
                print_error("无法获取下载链接")
                return
            
            self.download_datapack(download_url, filename, title, version.get('version_number'))
            
        except Exception as e:
            print_error(f"获取版本信息失败: {e}")
            input("\n按回车键继续...")

    def download_datapack(self, url: str, filename: str = "", pack_name: str = "", pack_version: str = ""):
        """下载数据包"""
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        
        if not filename:
            filename = url.split('/')[-1]
            if not filename.endswith('.zip'):
                filename += '.zip'
        
        dest = datapacks_dir / filename
        
        print_info(f"正在下载数据包: {filename}")
        try:
            download_with_progress(url, dest, f"📦 下载数据包")
            self.process_datapack(dest, pack_name, pack_version)
        except Exception as e:
            print_error(f"下载失败: {e}")
            if dest.exists():
                dest.unlink()
        finally:
            input("\n按回车键继续...")

    def process_datapack(self, pack_path: Path, pack_name: str = "", pack_version: str = ""):
        """处理已下载的数据包"""
        try:
            info = self.parse_datapack_info(pack_path)
            
            if info:
                pack_name = info.get('name', pack_name or pack_path.stem)
                pack_version = info.get('version', pack_version or "1.0")
                description = info.get('description', '')
                mc_version = info.get('minecraft_version', '')
            else:
                description = ''
                mc_version = ''
            
            datapack = Datapack(
                name=pack_name or pack_path.stem,
                version=pack_version or "1.0",
                minecraft_version=mc_version,
                description=description,
                filename=pack_path.name,
                installed_path=str(pack_path),
                install_date=datetime.now().isoformat(),
                enabled=True
            )
            
            self.config.datapacks.append(datapack)
            self.save_config()
            
            print_success(f"数据包 {datapack.name} 安装完成！")
            
        except Exception as e:
            print_error(f"处理数据包失败: {e}")

    def parse_datapack_info(self, pack_path: Path) -> Optional[Dict]:
        """解析数据包信息"""
        try:
            with zipfile.ZipFile(pack_path, 'r') as zf:
                if 'pack.mcmeta' in zf.namelist():
                    with zf.open('pack.mcmeta') as f:
                        data = json.load(f)
                        pack_info = data.get('pack', {})
                        
                        description = pack_info.get('description', '')
                        if isinstance(description, dict):
                            description = description.get('text', '')
                        
                        mc_version = ''
                        pack_format = pack_info.get('pack_format')
                        if pack_format:
                            format_map = {
                                '1': '1.6.1-1.8.9',
                                '2': '1.9-1.10.2',
                                '3': '1.11-1.12.2',
                                '4': '1.13-1.14.4',
                                '5': '1.15-1.16.1',
                                '6': '1.16.2-1.16.5',
                                '7': '1.17-1.17.1',
                                '8': '1.18-1.18.2',
                                '9': '1.19-1.19.2',
                                '10': '1.19.3',
                                '12': '1.19.4',
                                '13': '1.20-1.20.1',
                                '15': '1.20.2',
                                '18': '1.20.3-1.20.4',
                                '22': '1.20.5-1.20.6',
                                '26': '1.21+'
                            }
                            mc_version = format_map.get(str(pack_format), f'pack_format {pack_format}')
                        
                        return {
                            'name': pack_path.stem,
                            'version': '1.0',
                            'description': str(description),
                            'minecraft_version': mc_version
                        }
        except:
            pass
        return None

    def toggle_datapack(self):
        """启用/禁用数据包"""
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        packs = list(datapacks_dir.glob("*.zip")) + list(datapacks_dir.glob("*.disabled"))
        
        if not packs:
            print_warning("暂无数据包")
            time.sleep(1)
            return
        
        clear_screen()
        print_header("启用/禁用数据包")
        
        for i, pack in enumerate(packs, 1):
            status = f"{Colors.GREEN}[启用]{Colors.ENDC}" if not pack.name.endswith('.disabled') else f"{Colors.WARNING}[禁用]{Colors.ENDC}"
            print(f"  {i:2d}. {pack.name} {status}")
        
        choice = input(f"\n{Colors.BLUE}请选择要切换的数据包编号 (0返回): {Colors.ENDC}").strip()
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(packs):
            return
        
        pack_path = packs[idx]
        
        if pack_path.name.endswith('.disabled'):
            new_path = pack_path.with_suffix('')
            if new_path.suffix != '.zip':
                new_path = new_path.with_suffix('.zip')
        else:
            new_path = pack_path.with_name(pack_path.name + '.disabled')
        
        pack_path.rename(new_path)
        
        for dp in self.config.datapacks:
            if dp.filename == pack_path.name:
                dp.enabled = not pack_path.name.endswith('.disabled')
                dp.filename = new_path.name
                break
        
        self.save_config()
        print_success(f"已切换: {pack_path.name} -> {new_path.name}")
        time.sleep(1)

    def delete_datapack(self):
        """删除数据包"""
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        packs = list(datapacks_dir.glob("*.zip")) + list(datapacks_dir.glob("*.disabled"))
        
        if not packs:
            print_warning("暂无数据包")
            time.sleep(1)
            return
        
        clear_screen()
        print_header("删除数据包")
        
        for i, pack in enumerate(packs, 1):
            status = f"{Colors.GREEN}[启用]{Colors.ENDC}" if not pack.name.endswith('.disabled') else f"{Colors.WARNING}[禁用]{Colors.ENDC}"
            print(f"  {i:2d}. {pack.name} {status}")
        
        choice = input(f"\n{Colors.BLUE}请选择要删除的数据包编号 (0返回): {Colors.ENDC}").strip()
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(packs):
            return
        
        pack_path = packs[idx]
        confirm = input(f"确定删除 {pack_path.name}? (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            pack_path.unlink()
            self.config.datapacks = [dp for dp in self.config.datapacks if dp.filename != pack_path.name]
            self.save_config()
            print_success(f"已删除 {pack_path.name}")
            time.sleep(1)

    def install_datapack_to_world(self):
        """将数据包安装到指定世界"""
        saves_dir = Path(self.config.minecraft_data_path) / "saves"
        if not saves_dir.exists() or not any(saves_dir.iterdir()):
            print_warning("暂无存档")
            time.sleep(1)
            return
        
        datapacks_dir = Path(self.config.minecraft_data_path) / self.config.datapacks_folder
        packs = list(datapacks_dir.glob("*.zip"))
        
        if not packs:
            print_warning("暂无可用数据包")
            time.sleep(1)
            return
        
        worlds = [w for w in saves_dir.iterdir() if w.is_dir()]
        clear_screen()
        print_header("选择世界")
        
        for i, world in enumerate(worlds, 1):
            print(f"  {i:2d}. {world.name}")
        
        world_choice = input(f"\n{Colors.BLUE}请选择世界编号 (0返回): {Colors.ENDC}").strip()
        if world_choice == "0" or not world_choice.isdigit():
            return
        
        world_idx = int(world_choice) - 1
        if world_idx < 0 or world_idx >= len(worlds):
            return
        
        selected_world = worlds[world_idx]
        
        clear_screen()
        print_header(f"为世界 '{selected_world.name}' 选择数据包")
        
        for i, pack in enumerate(packs, 1):
            print(f"  {i:2d}. {pack.name}")
        
        pack_choice = input(f"\n{Colors.BLUE}请选择数据包编号 (0返回): {Colors.ENDC}").strip()
        if pack_choice == "0" or not pack_choice.isdigit():
            return
        
        pack_idx = int(pack_choice) - 1
        if pack_idx < 0 or pack_idx >= len(packs):
            return
        
        selected_pack = packs[pack_idx]
        
        world_datapacks_dir = selected_world / "datapacks"
        world_datapacks_dir.mkdir(parents=True, exist_ok=True)
        
        dest = world_datapacks_dir / selected_pack.name
        if dest.exists():
            overwrite = input(f"目标文件已存在，是否覆盖? (y/n): ").strip().lower()
            if overwrite not in ('y', 'yes'):
                return
        
        shutil.copy2(selected_pack, dest)
        print_success(f"数据包已安装到世界 {selected_world.name}")
        time.sleep(1)

    # ==================== 整合包管理 ====================
    def modpack_manager(self):
        """整合包管理界面"""
        modpacks_dir = Path(self.config.minecraft_data_path) / self.config.modpacks_folder
        modpacks_dir.mkdir(parents=True, exist_ok=True)
        
        while True:
            clear_screen()
            print_header("整合包管理")
            
            print(f"\n{Colors.CYAN}已安装整合包: {len(self.config.modpacks)}{Colors.ENDC}")
            
            if self.config.modpacks:
                for i, mp in enumerate(self.config.modpacks, 1):
                    print(f"  {i:2d}. {Colors.BOLD}{mp.name}{Colors.ENDC} v{mp.version}")
                    print(f"     📦 Minecraft: {mp.minecraft_version} | {mp.modloader} {mp.modloader_version}")
                    if mp.description:
                        print(f"     📝 {mp.description[:60]}{'...' if len(mp.description) > 60 else ''}")
            else:
                print(f"  {Colors.BLUE}暂无整合包{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "安装整合包", "从本地或网络安装")
            print_menu_item("2", "启动整合包", "启动选中的整合包")
            print_menu_item("3", "删除整合包", "删除选中的整合包")
            print_menu_item("4", "导入整合包", "导入本地整合包文件")
            print_menu_item("5", "打开整合包文件夹", "在资源管理器中打开")
            print_menu_item("6", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                self.install_modpack()
            elif choice == "2":
                self.launch_modpack()
            elif choice == "3":
                self.delete_modpack()
            elif choice == "4":
                self.import_modpack()
            elif choice == "5":
                self.open_folder(modpacks_dir)
            elif choice == "6":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def install_modpack(self):
        """安装整合包"""
        print_info("请选择安装方式:")
        print("  1. 从 Modrinth 搜索")
        print("  2. 从 CurseForge 搜索")
        print("  3. 手动输入下载链接")
        print("  0. 返回")
        
        choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
        
        if choice == "1":
            self.search_modrinth_modpacks()
        elif choice == "2":
            self.search_curseforge_modpacks()
        elif choice == "3":
            url = input("请输入整合包下载链接: ").strip()
            if url:
                self.download_modpack(url)
        elif choice == "0":
            return

    def search_modrinth_modpacks(self):
        """从 Modrinth 搜索整合包"""
        query = input("请输入整合包名称: ").strip()
        if not query:
            return
        
        print_info(f"正在从 Modrinth 搜索 '{query}'...")
        try:
            encoded_query = urllib.parse.quote(query)
            facets = '[[\"project_type:modpack\"]]'
            encoded_facets = urllib.parse.quote(facets)
            url = f"https://api.modrinth.com/v2/search?query={encoded_query}&facets={encoded_facets}&limit=10"
            
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            hits = data.get("hits", [])
            if not hits:
                print_warning("未找到相关内容")
                input("\n按回车键继续...")
                return

            print(f"\n{Colors.CYAN}找到 {len(hits)} 个整合包:{Colors.ENDC}")
            for i, item in enumerate(hits, 1):
                title = item.get('title', '未知')
                author = item.get('author', '未知')
                desc = item.get('description', '无描述')[:80]
                versions = item.get('versions', [])
                latest_version = versions[-1] if versions else '未知'
                print(f"  {Colors.GREEN}{i:2d}.{Colors.ENDC} {Colors.BOLD}{title}{Colors.ENDC}")
                print(f"     作者: {author}")
                print(f"     最新版本: {latest_version}")
                print(f"     描述: {desc}...")
            
            choice = input(f"\n{Colors.BLUE}请选择要安装的编号 (0返回): {Colors.ENDC}").strip()
            if choice != "0" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(hits):
                    self.download_modrinth_modpack(hits[idx])
        except Exception as e:
            print_error(f"搜索失败: {e}")
            input("\n按回车键继续...")

    def search_curseforge_modpacks(self):
        """从 CurseForge 搜索整合包"""
        print_warning("CurseForge 搜索功能需要 API 密钥，暂时仅支持 Modrinth")
        print_info("您可以通过以下方式安装 CurseForge 整合包：")
        print("  1. 手动下载整合包文件后选择导入")
        print("  2. 使用整合包下载链接")
        input("\n按回车键继续...")

    def download_modrinth_modpack(self, project_info: dict):
        """从 Modrinth 下载整合包"""
        slug = project_info.get('slug')
        if not slug:
            print_error("无法获取项目标识")
            return
        
        title = project_info.get('title', slug)
        print_info(f"正在获取 {title} 的版本信息...")
        
        try:
            url = f"https://api.modrinth.com/v2/project/{slug}/version"
            with urllib.request.urlopen(url, timeout=10) as resp:
                versions = json.loads(resp.read().decode("utf-8"))
            
            if not versions:
                print_warning("无可用版本")
                return
            
            print(f"\n{Colors.CYAN}可用版本:{Colors.ENDC}")
            for i, ver in enumerate(versions[:10], 1):
                print(f"  {i:2d}. {ver.get('version_number', '未知')} - {ver.get('name', '未知')[:50]}")
            
            choice = input(f"\n{Colors.BLUE}请选择版本编号 (0返回): {Colors.ENDC}").strip()
            if choice == "0" or not choice.isdigit():
                return
            
            idx = int(choice) - 1
            if idx < 0 or idx >= len(versions):
                return
            
            version = versions[idx]
            files = version.get('files', [])
            if not files:
                print_warning("该版本无可用文件")
                return
            
            file_info = files[0]
            download_url = file_info.get('url')
            filename = file_info.get('filename')
            
            if not download_url or not filename:
                print_error("无法获取下载链接")
                return
            
            self.download_modpack(download_url, filename, title, version.get('version_number'))
            
        except Exception as e:
            print_error(f"获取版本信息失败: {e}")
            input("\n按回车键继续...")

    def download_modpack(self, url: str, filename: str = "", pack_name: str = "", pack_version: str = ""):
        """下载整合包"""
        modpacks_dir = Path(self.config.minecraft_data_path) / self.config.modpacks_folder
        
        if not filename:
            filename = url.split('/')[-1]
            if not filename.endswith('.zip'):
                filename += '.zip'
        
        dest = modpacks_dir / "downloads"
        dest.mkdir(exist_ok=True)
        zip_path = dest / filename
        
        print_info(f"正在下载整合包: {filename}")
        try:
            download_with_progress(url, zip_path, f"📦 下载整合包")
            
            print_info("正在解压整合包...")
            extract_dir = modpacks_dir / filename.replace('.zip', '')
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                members = zf.infolist()
                total_files = len(members)
                for i, member in enumerate(members, 1):
                    zf.extract(member, extract_dir)
                    if i % 50 == 0 or i == total_files:
                        print_progress(i, total_files, "📦 解压进度")
            print()
            
            modpack_info = self.parse_modpack_info(extract_dir)
            if not modpack_info:
                modpack_info = Modpack(
                    name=pack_name or filename.replace('.zip', ''),
                    version=pack_version or "1.0",
                    minecraft_version=self.detect_minecraft_version(extract_dir) or "未知",
                    modloader="unknown",
                    modloader_version="unknown",
                    description="",
                    installed_path=str(extract_dir),
                    install_date=datetime.now().isoformat()
                )
            
            self.config.modpacks.append(modpack_info)
            self.save_config()
            
            zip_path.unlink()
            
            print_success(f"整合包 {modpack_info.name} 安装完成！")
            
        except Exception as e:
            print_error(f"下载失败: {e}")
        finally:
            input("\n按回车键继续...")

    def import_modpack(self):
        """导入本地整合包"""
        modpacks_dir = Path(self.config.minecraft_data_path) / self.config.modpacks_folder
        
        print_info("请选择整合包文件（支持 .zip 格式）")
        print_warning("注意：请将整合包文件放入以下文件夹：")
        print(f"  {modpacks_dir}")
        
        files = list(modpacks_dir.glob("*.zip"))
        if files:
            print(f"\n{Colors.CYAN}检测到以下文件:{Colors.ENDC}")
            for i, f in enumerate(files, 1):
                size = format_size(f.stat().st_size)
                print(f"  {i:2d}. {f.name} ({size})")
            
            choice = input(f"\n{Colors.BLUE}请选择要导入的文件编号 (0手动输入路径): {Colors.ENDC}").strip()
            if choice != "0" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    self.download_modpack(str(files[idx]), files[idx].name)
                    return
        
        path = input("请输入整合包文件路径: ").strip()
        if path and Path(path).exists():
            filename = Path(path).name
            dest = modpacks_dir / filename
            shutil.copy2(path, dest)
            self.download_modpack(str(dest), filename)
        else:
            print_error("文件不存在")

    def parse_modpack_info(self, pack_dir: Path) -> Optional[Modpack]:
        """解析整合包信息"""
        mrpack = pack_dir / "modrinth.index.json"
        if mrpack.exists():
            try:
                with open(mrpack, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Modpack(
                    name=data.get('name', '未知'),
                    version=data.get('versionId', '1.0'),
                    minecraft_version=self.get_minecraft_version_from_deps(data.get('dependencies', {})),
                    modloader="unknown",
                    modloader_version="unknown",
                    description=data.get('description', ''),
                    author=data.get('author', ''),
                    installed_path=str(pack_dir),
                    install_date=datetime.now().isoformat()
                )
            except:
                pass
        
        manifest = pack_dir / "manifest.json"
        if manifest.exists():
            try:
                with open(manifest, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                mc_version = ""
                modloader = ""
                modloader_version = ""
                
                for mod in data.get('minecraft', {}).get('modLoaders', []):
                    if 'forge' in mod.get('id', '').lower():
                        modloader = "forge"
                        modloader_version = mod.get('id', '').replace('forge-', '')
                    elif 'fabric' in mod.get('id', '').lower():
                        modloader = "fabric"
                        modloader_version = mod.get('id', '').replace('fabric-', '')
                
                return Modpack(
                    name=data.get('name', '未知'),
                    version=data.get('version', '1.0'),
                    minecraft_version=data.get('minecraft', {}).get('version', '未知'),
                    modloader=modloader,
                    modloader_version=modloader_version,
                    description=data.get('description', ''),
                    author=data.get('author', ''),
                    installed_path=str(pack_dir),
                    install_date=datetime.now().isoformat()
                )
            except:
                pass
        
        return None

    def get_minecraft_version_from_deps(self, deps: dict) -> str:
        """从依赖中获取 Minecraft 版本"""
        for key, value in deps.items():
            if 'minecraft' in key.lower():
                return value
        return "未知"

    def detect_minecraft_version(self, pack_dir: Path) -> Optional[str]:
        """检测整合包的 Minecraft 版本"""
        versions_file = pack_dir / "versions.json"
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                    return data.get('minecraft', {}).get('version')
            except:
                pass
        
        for item in pack_dir.glob("*"):
            if item.is_dir() and item.name.startswith("1."):
                return item.name
        
        return None

    def launch_modpack(self):
        """启动整合包"""
        if not self.config.modpacks:
            print_warning("暂无整合包")
            time.sleep(1)
            return
        
        clear_screen()
        print_header("启动整合包")
        
        for i, mp in enumerate(self.config.modpacks, 1):
            print(f"  {Colors.GREEN}{i:2d}.{Colors.ENDC} {Colors.BOLD}{mp.name}{Colors.ENDC} v{mp.version}")
            print(f"     📦 Minecraft: {mp.minecraft_version} | {mp.modloader} {mp.modloader_version}")
        
        choice = input(f"\n{Colors.BLUE}请选择要启动的整合包编号 (0返回): {Colors.ENDC}").strip()
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(self.config.modpacks):
            return
        
        modpack = self.config.modpacks[idx]
        
        pack_path = Path(modpack.installed_path)
        if not pack_path.exists():
            print_error(f"整合包目录不存在: {pack_path}")
            time.sleep(1)
            return
        
        version_id = modpack.minecraft_version
        if version_id == "未知":
            print_warning("无法确定 Minecraft 版本，请手动选择")
            version_id = input("请输入 Minecraft 版本号: ").strip()
            if not version_id:
                return
        
        version_path = Path(self.config.minecraft_data_path) / "versions" / version_id / f"{version_id}.jar"
        if not version_path.exists():
            print_info(f"需要下载 Minecraft {version_id}")
            if not self.download_minecraft_version(version_id):
                return
        
        print_success(f"准备启动整合包: {modpack.name}")
        self.launch_minecraft(version_id, modpack)

    def delete_modpack(self):
        """删除整合包"""
        if not self.config.modpacks:
            print_warning("暂无整合包")
            time.sleep(1)
            return
        
        clear_screen()
        print_header("删除整合包")
        
        for i, mp in enumerate(self.config.modpacks, 1):
            print(f"  {i:2d}. {mp.name} v{mp.version}")
        
        choice = input(f"\n{Colors.BLUE}请选择要删除的整合包编号 (0返回): {Colors.ENDC}").strip()
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(self.config.modpacks):
            return
        
        modpack = self.config.modpacks[idx]
        confirm = input(f"确定删除整合包 {modpack.name}? (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            pack_path = Path(modpack.installed_path)
            if pack_path.exists():
                shutil.rmtree(pack_path)
            
            self.config.modpacks.pop(idx)
            self.save_config()
            print_success(f"已删除 {modpack.name}")
            time.sleep(1)

    # ==================== 资源管理 ====================
    def list_folder_files(self, folder: Path, extensions: List[str]) -> List[str]:
        if not folder.exists():
            return []
        return [f.name for f in folder.iterdir() if f.is_file() and f.suffix.lower() in extensions]

    def open_folder(self, folder: Path):
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])

    def search_online(self, query: str, project_type: str, target_folder: Path):
        if not query:
            return
        print_info(f"正在搜索 '{query}'...")
        try:
            encoded_query = urllib.parse.quote(query)
            facets = f'[[\"project_type:{project_type}\"]]'
            encoded_facets = urllib.parse.quote(facets)
            url = f"https://api.modrinth.com/v2/search?query={encoded_query}&facets={encoded_facets}&limit=10"
            
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            hits = data.get("hits", [])
            if not hits:
                print_warning("未找到相关内容")
                return

            installed_files = set(self.list_folder_files(target_folder, ['.jar', '.zip', '.disabled']))

            print(f"\n{Colors.CYAN}找到 {len(hits)} 个结果:{Colors.ENDC}")
            for i, item in enumerate(hits, 1):
                title = item.get('title', '未知')
                author = item.get('author', '未知')
                desc = item.get('description', '无描述')[:80]
                installed = ' ★' if any(title.lower() in f.lower() for f in installed_files) else ''
                print(f"  {Colors.GREEN}{i:2d}.{Colors.ENDC} {Colors.BOLD}{title}{Colors.ENDC}{Colors.YELLOW}{installed}{Colors.ENDC}")
                print(f"     作者: {author}")
                print(f"     描述: {desc}...")
            
            choice = input(f"\n{Colors.BLUE}请选择要下载的编号 (0返回): {Colors.ENDC}").strip()
            if choice != "0" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(hits):
                    self.download_from_modrinth(hits[idx], target_folder)
        except Exception as e:
            print_error(f"搜索失败: {e}")

    def download_from_modrinth(self, project_info: dict, target_folder: Path):
        slug = project_info.get('slug')
        if not slug:
            print_error("无法获取项目标识")
            return
        
        title = project_info.get('title', slug)
        print_info(f"正在获取 {title} 的最新版本...")
        
        try:
            url = f"https://api.modrinth.com/v2/project/{slug}/version"
            with urllib.request.urlopen(url, timeout=10) as resp:
                versions = json.loads(resp.read().decode("utf-8"))
            
            if not versions:
                print_warning("无可用版本")
                return
            
            version = versions[0]
            if not version.get('files'):
                print_warning("该版本无可用文件")
                return
            
            file_info = version['files'][0]
            download_url = file_info.get('url')
            filename = file_info.get('filename')
            
            if not download_url or not filename:
                print_error("无法获取下载链接")
                return

            dest = target_folder / filename
            download_with_progress(download_url, dest, f"📥 下载 {filename[:20]}...")
            print_success("下载完成")
        except Exception as e:
            print_error(f"下载失败: {e}")

    # -------------------- 模组管理 --------------------
    def mod_manager(self):
        mods_dir = Path(self.config.minecraft_data_path) / self.config.mods_folder
        mods_dir.mkdir(parents=True, exist_ok=True)
        
        while True:
            clear_screen()
            print_header("模组管理")
            
            mods = self.list_folder_files(mods_dir, ['.jar', '.disabled'])
            enabled = [m for m in mods if not m.endswith('.disabled')]
            disabled = [m for m in mods if m.endswith('.disabled')]
            
            print(f"\n{Colors.CYAN}已安装模组: {len(enabled)} 启用, {len(disabled)} 禁用{Colors.ENDC}")
            if mods:
                for i, mod in enumerate(mods, 1):
                    status = f"{Colors.GREEN}[启用]{Colors.ENDC}" if not mod.endswith('.disabled') else f"{Colors.WARNING}[禁用]{Colors.ENDC}"
                    print(f"  {i:2d}. {mod} {status}")
            else:
                print(f"  {Colors.BLUE}暂无模组{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "搜索并下载模组", "从 Modrinth 搜索下载")
            print_menu_item("2", "启用/禁用模组", "切换模组状态")
            print_menu_item("3", "删除模组", "删除选中的模组")
            print_menu_item("4", "打开模组文件夹", "在资源管理器中打开")
            print_menu_item("5", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                query = input("请输入模组名称: ").strip()
                self.search_online(query, "mod", mods_dir)
                input("\n按回车键继续...")
            elif choice == "2":
                self.toggle_mod(mods_dir, mods)
            elif choice == "3":
                self.delete_mod(mods_dir, mods)
            elif choice == "4":
                self.open_folder(mods_dir)
            elif choice == "5":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def toggle_mod(self, mods_dir: Path, mods: List[str]):
        if not mods:
            print_warning("暂无模组")
            time.sleep(1)
            return
        
        choice = input("请输入要切换的模组编号: ").strip()
        if not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(mods):
            return
        
        mod_name = mods[idx]
        mod_path = mods_dir / mod_name
        
        if mod_name.endswith('.disabled'):
            new_name = mod_name[:-9]
            new_path = mods_dir / new_name
        else:
            new_path = mods_dir / (mod_name + '.disabled')
        
        mod_path.rename(new_path)
        print_success(f"已切换: {mod_name} -> {new_path.name}")
        time.sleep(1)

    def delete_mod(self, mods_dir: Path, mods: List[str]):
        if not mods:
            print_warning("暂无模组")
            time.sleep(1)
            return
        
        choice = input("请输入要删除的模组编号: ").strip()
        if not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(mods):
            return
        
        mod_name = mods[idx]
        confirm = input(f"确定删除 {mod_name}? (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            (mods_dir / mod_name).unlink()
            print_success(f"已删除 {mod_name}")
            time.sleep(1)

    # -------------------- 资源包管理 --------------------
    def resourcepack_manager(self):
        rp_dir = Path(self.config.minecraft_data_path) / self.config.resource_packs_folder
        rp_dir.mkdir(parents=True, exist_ok=True)
        
        while True:
            clear_screen()
            print_header("资源包管理")
            
            packs = self.list_folder_files(rp_dir, ['.zip'])
            print(f"\n{Colors.CYAN}已安装资源包: {len(packs)}{Colors.ENDC}")
            if packs:
                for i, p in enumerate(packs, 1):
                    print(f"  {i:2d}. {p}")
            else:
                print(f"  {Colors.BLUE}暂无资源包{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "搜索并下载资源包", "从 Modrinth 搜索下载")
            print_menu_item("2", "删除资源包", "删除选中的资源包")
            print_menu_item("3", "打开资源包文件夹", "在资源管理器中打开")
            print_menu_item("4", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                query = input("请输入资源包名称: ").strip()
                self.search_online(query, "resourcepack", rp_dir)
                input("\n按回车键继续...")
            elif choice == "2":
                self.delete_resourcepack(rp_dir, packs)
            elif choice == "3":
                self.open_folder(rp_dir)
            elif choice == "4":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def delete_resourcepack(self, rp_dir: Path, packs: List[str]):
        if not packs:
            print_warning("暂无资源包")
            time.sleep(1)
            return
        
        choice = input("请输入要删除的资源包编号: ").strip()
        if not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(packs):
            return
        
        name = packs[idx]
        confirm = input(f"确定删除 {name}? (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            (rp_dir / name).unlink()
            print_success(f"已删除 {name}")
            time.sleep(1)

    # -------------------- 光影包管理 --------------------
    def shaderpack_manager(self):
        sp_dir = Path(self.config.minecraft_data_path) / self.config.shaderpacks_folder
        sp_dir.mkdir(parents=True, exist_ok=True)
        
        while True:
            clear_screen()
            print_header("光影包管理")
            
            packs = self.list_folder_files(sp_dir, ['.zip'])
            print(f"\n{Colors.CYAN}已安装光影包: {len(packs)}{Colors.ENDC}")
            if packs:
                for i, p in enumerate(packs, 1):
                    print(f"  {i:2d}. {p}")
            else:
                print(f"  {Colors.BLUE}暂无光影包{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "搜索并下载光影包", "从 Modrinth 搜索下载")
            print_menu_item("2", "删除光影包", "删除选中的光影包")
            print_menu_item("3", "打开光影包文件夹", "在资源管理器中打开")
            print_menu_item("4", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                query = input("请输入光影包名称: ").strip()
                self.search_online(query, "shader", sp_dir)
                input("\n按回车键继续...")
            elif choice == "2":
                self.delete_shaderpack(sp_dir, packs)
            elif choice == "3":
                self.open_folder(sp_dir)
            elif choice == "4":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def delete_shaderpack(self, sp_dir: Path, packs: List[str]):
        if not packs:
            print_warning("暂无光影包")
            time.sleep(1)
            return
        
        choice = input("请输入要删除的光影包编号: ").strip()
        if not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(packs):
            return
        
        name = packs[idx]
        confirm = input(f"确定删除 {name}? (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            (sp_dir / name).unlink()
            print_success(f"已删除 {name}")
            time.sleep(1)

    # -------------------- 账号管理 --------------------
    def login_screen(self):
        while True:
            clear_screen()
            print_header("账号管理")
            
            current = self.get_current_account()
            if current:
                print(f"\n{Colors.GREEN}当前登录: {current.username} [{current.account_type}]{Colors.ENDC}")
                if hasattr(current, 'last_played') and current.last_played:
                    print(f"上次游玩: {current.last_played}")
            else:
                print(f"\n{Colors.WARNING}当前未登录{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "离线登录", "使用离线模式登录")
            print_menu_item("2", "切换账号", "切换到其他已保存账号")
            print_menu_item("3", "退出当前账号", "注销当前登录")
            print_menu_item("4", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                username = input("请输入游戏内名称: ").strip()
                if not username:
                    username = f"Player{datetime.now().strftime('%H%M%S')}"
                self.offline_login(username)
                print_success(f"离线登录成功，用户名: {username}")
                time.sleep(1)
                break
            elif choice == "2":
                self.switch_account()
            elif choice == "3":
                if self.config.current_account:
                    self.config.current_account = None
                    self.save_config()
                    print_success("已退出当前账号")
                    time.sleep(1)
                else:
                    print_warning("当前未登录，无需退出")
                    time.sleep(1)
            elif choice == "4":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def switch_account(self):
        if not self.config.accounts:
            print_warning("暂无已保存账号")
            time.sleep(1)
            return
        
        print(f"\n{Colors.CYAN}已保存账号:{Colors.ENDC}")
        for i, acc in enumerate(self.config.accounts, 1):
            mark = " (当前)" if acc.username == self.config.current_account else ""
            print(f"  {i:2d}. {acc.username} [{acc.account_type}]{mark}")
        
        idx = input(f"\n{Colors.BLUE}请选择账号编号 (0返回): {Colors.ENDC}").strip()
        if idx == "0":
            return
        
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(self.config.accounts):
                self.config.current_account = self.config.accounts[idx].username
                self.save_config()
                print_success(f"已切换到 {self.config.current_account}")
                time.sleep(1)
        except:
            print_warning("无效选择")
            time.sleep(1)

    # -------------------- 内存优化 --------------------
    def memory_optimization_screen(self):
        clear_screen()
        print_header("内存优化配置")
        
        try:
            import psutil
            total = psutil.virtual_memory().total / 1024**3
            available = psutil.virtual_memory().available / 1024**3
            print(f"\n{Colors.CYAN}系统信息:{Colors.ENDC}")
            print(f"  总内存: {total:.1f} GB")
            print(f"  可用内存: {available:.1f} GB")
            
            if total >= 16:
                rec_max, rec_min = "6G", "4G"
            elif total >= 8:
                rec_max, rec_min = "4G", "2G"
            elif total >= 4:
                rec_max, rec_min = "2G", "1G"
            else:
                rec_max, rec_min = "1G", "512M"
            print(f"\n{Colors.GREEN}推荐配置: 最大 {rec_max}, 最小 {rec_min}{Colors.ENDC}")
        except:
            rec_max, rec_min = "2G", "1G"
            print(f"\n{Colors.WARNING}无法获取内存信息，使用保守配置{Colors.ENDC}")

        print(f"\n{Colors.CYAN}当前配置:{Colors.ENDC}")
        print(f"  最大内存: {self.config.memory.max_memory}")
        print(f"  最小内存: {self.config.memory.min_memory}")
        print(f"  自动分配: {'开启' if self.config.memory.auto_allocate else '关闭'}")
        
        print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
        print_menu_item("1", "使用推荐配置", "应用推荐的内存设置")
        print_menu_item("2", "手动设置", "自定义内存大小")
        print_menu_item("3", "切换自动分配", "开启/关闭自动分配")
        print_menu_item("4", "返回", "")
        
        choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
        
        if choice == "1":
            self.config.memory.max_memory = rec_max
            self.config.memory.min_memory = rec_min
            self.save_config()
            print_success("已应用推荐配置")
            time.sleep(1)
        elif choice == "2":
            max_mem = input(f"最大内存 (当前 {self.config.memory.max_memory}): ").strip()
            if max_mem:
                self.config.memory.max_memory = max_mem
            min_mem = input(f"最小内存 (当前 {self.config.memory.min_memory}): ").strip()
            if min_mem:
                self.config.memory.min_memory = min_mem
            self.save_config()
            print_success("已更新")
            time.sleep(1)
        elif choice == "3":
            self.config.memory.auto_allocate = not self.config.memory.auto_allocate
            self.save_config()
            print_success(f"自动分配已{'开启' if self.config.memory.auto_allocate else '关闭'}")
            time.sleep(1)

    # -------------------- 版本管理 --------------------
    def version_manager(self):
        while True:
            clear_screen()
            print_header("版本管理器")
            
            print(f"\n{Colors.CYAN}已安装版本: {len(self.installed_versions)} | 在线版本: {len(self.all_versions)}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "查看所有版本", "显示所有在线版本")
            print_menu_item("2", "查看已安装版本", "显示本地已安装版本")
            print_menu_item("3", "下载新版本", "从网络下载指定版本")
            print_menu_item("4", "删除版本", "删除本地版本")
            print_menu_item("5", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                self.show_all_versions()
            elif choice == "2":
                self.show_installed_versions()
            elif choice == "3":
                version = input("请输入要下载的版本号: ").strip()
                if version:
                    self.download_minecraft_version(version)
                    input("\n按回车键继续...")
            elif choice == "4":
                self.delete_version()
            elif choice == "5":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def show_all_versions(self):
        if not self.all_versions:
            print_warning("未获取到版本信息")
            input("\n按回车键继续...")
            return
        
        clear_screen()
        print_header("所有版本")
        
        page_size = 20
        total = len(self.all_versions)
        for i, v in enumerate(self.all_versions, 1):
            installed = " ★" if v.id in self.installed_versions else ""
            type_color = Colors.GREEN if v.type == "release" else Colors.BLUE
            print(f"  {i:4d}. {v.id} {type_color}({v.type}){Colors.ENDC}{Colors.YELLOW}{installed}{Colors.ENDC}")
            if i % page_size == 0 and i < total:
                input(f"\n{Colors.BLUE}按回车键继续显示更多...{Colors.ENDC}")
                clear_screen()
                print_header("所有版本 (续)")
        
        input(f"\n{Colors.BLUE}按回车键返回...{Colors.ENDC}")

    def show_installed_versions(self, selectable=False):
        if not self.installed_versions:
            print_warning("暂无已安装版本")
            if selectable:
                return None
            input("\n按回车键继续...")
            return None
        
        clear_screen()
        print_header("已安装版本")
        
        for i, v in enumerate(self.installed_versions, 1):
            mark = " ★" if v == self.config.last_version else ""
            print(f"  {i:2d}. {v}{Colors.YELLOW}{mark}{Colors.ENDC}")
        
        if selectable:
            idx = input(f"\n{Colors.BLUE}请选择版本编号 (0返回): {Colors.ENDC}").strip()
            if idx == "0":
                return None
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(self.installed_versions):
                    return self.installed_versions[idx]
            except:
                pass
        else:
            input(f"\n{Colors.BLUE}按回车键返回...{Colors.ENDC}")
        return None

    def delete_version(self):
        version = self.show_installed_versions(selectable=True)
        if version:
            confirm = input(f"确定删除 {version}? (y/n): ").strip().lower()
            if confirm in ("y", "yes"):
                version_dir = Path(self.config.minecraft_data_path) / "versions" / version
                if version_dir.exists():
                    shutil.rmtree(version_dir)
                    print_success(f"已删除 {version}")
                    self.refresh_installed_versions()
                    time.sleep(1)
                else:
                    print_error("版本目录不存在")
                    time.sleep(1)

    # -------------------- 设置界面 --------------------
    def settings_screen(self):
        while True:
            clear_screen()
            print_header("设置")
            
            print(f"\n{Colors.CYAN}当前配置:{Colors.ENDC}")
            print(f"  1. Java 路径: {Colors.GREEN}{self.config.java_path}{Colors.ENDC}")
            print(f"  2. 内存配置: {Colors.GREEN}{self.config.memory.max_memory}/{self.config.memory.min_memory}{Colors.ENDC}")
            print(f"  3. 游戏数据路径: {Colors.GREEN}{self.config.minecraft_data_path}{Colors.ENDC}")
            print(f"  4. 游戏分辨率: {Colors.GREEN}{self.config.game_resolution}{Colors.ENDC}")
            print(f"  5. 显示控制台: {Colors.GREEN}{'是' if self.config.show_console else '否'}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
            print_menu_item("1", "修改 Java 路径", "")
            print_menu_item("2", "内存优化配置", "")
            print_menu_item("3", "修改游戏数据路径", "")
            print_menu_item("4", "修改游戏分辨率", "")
            print_menu_item("5", "切换控制台显示", "")
            print_menu_item("6", "管理已下载的 Java", "")
            print_menu_item("7", "返回主菜单", "")
            
            choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
            
            if choice == "1":
                new_path = input("请输入 Java 路径 (留空保持当前): ").strip()
                if new_path:
                    self.config.java_path = new_path
                    self.save_config()
                    print_success("已更新")
                    time.sleep(1)
            elif choice == "2":
                self.memory_optimization_screen()
            elif choice == "3":
                new_path = input("请输入 Minecraft 数据路径: ").strip()
                if new_path:
                    self.config.minecraft_data_path = new_path
                    self.save_config()
                    self.create_default_folders()
                    self.refresh_installed_versions()
                    print_success("已更新")
                    time.sleep(1)
            elif choice == "4":
                resolutions = ["854x480", "1024x576", "1280x720", "1920x1080", "2560x1440"]
                print(f"\n{Colors.CYAN}可选分辨率:{Colors.ENDC}")
                for i, res in enumerate(resolutions, 1):
                    print(f"  {i}. {res}")
                print("  0. 自定义")
                
                res_choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
                if res_choice == "0":
                    custom = input("请输入分辨率 (格式: 宽度x高度): ").strip()
                    if custom:
                        self.config.game_resolution = custom
                elif res_choice.isdigit() and 1 <= int(res_choice) <= len(resolutions):
                    self.config.game_resolution = resolutions[int(res_choice) - 1]
                
                self.save_config()
                print_success("已更新")
                time.sleep(1)
            elif choice == "5":
                self.config.show_console = not self.config.show_console
                self.save_config()
                print_success(f"控制台显示已{'开启' if self.config.show_console else '关闭'}")
                time.sleep(1)
            elif choice == "6":
                self.manage_java_runtimes()
            elif choice == "7":
                break
            else:
                print_warning("无效选择")
                time.sleep(1)

    def manage_java_runtimes(self):
        runtime_dir = Path(self.config.minecraft_data_path) / "runtime"
        if not runtime_dir.exists():
            print_warning("暂无已下载的 Java 运行时")
            time.sleep(1)
            return
        
        javas = []
        for item in runtime_dir.iterdir():
            if item.is_dir() and item.name.startswith("java"):
                java_exe = item / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
                if java_exe.exists():
                    javas.append((item.name, java_exe))
        
        if not javas:
            print_warning("暂无已下载的 Java 运行时")
            time.sleep(1)
            return
        
        clear_screen()
        print_header("Java 运行时管理")
        
        print(f"\n{Colors.CYAN}已下载的 Java:{Colors.ENDC}")
        for i, (name, path) in enumerate(javas, 1):
            try:
                result = subprocess.run([str(path), "-version"], capture_output=True, text=True, timeout=2)
                version_info = result.stderr.split("\n")[0][:50]
            except:
                version_info = "无法获取版本信息"
            print(f"  {i:2d}. {name} - {version_info}")
        
        print(f"\n{Colors.BOLD}操作:{Colors.ENDC}")
        print_menu_item("1", "删除 Java", "删除选中的 Java 运行时")
        print_menu_item("2", "返回", "")
        
        choice = input(f"\n{Colors.BLUE}请选择: {Colors.ENDC}").strip()
        
        if choice == "1":
            idx = input("请输入要删除的 Java 编号: ").strip()
            if idx.isdigit():
                idx = int(idx) - 1
                if 0 <= idx < len(javas):
                    confirm = input(f"确定删除 {javas[idx][0]}? (y/n): ").strip().lower()
                    if confirm in ("y", "yes"):
                        shutil.rmtree(runtime_dir / javas[idx][0])
                        print_success("已删除")
                        time.sleep(1)

    # -------------------- 主菜单 --------------------
    def main_menu(self):
        global _shutdown_requested
        
        if not self.get_current_account():
            self.login_screen()

        while not _shutdown_requested:
            try:
                clear_screen()
                print(f"{Colors.CYAN}{Colors.BOLD}")
                print("╔════════════════════════════════════════════════════════╗")
                print("║               Minecraft 独立启动器                    ║")
                print("╚════════════════════════════════════════════════════════╝")
                print(f"{Colors.ENDC}")
                
                account = self.get_current_account()
                if account:
                    print(f"  {Colors.GREEN}👤 当前账号: {account.username}{Colors.ENDC}")
                
                print(f"  {Colors.BLUE}💾 内存配置: {self.config.memory.max_memory}/{self.config.memory.min_memory}{Colors.ENDC}")
                
                if self.config.last_version:
                    last_version_color = Colors.GREEN if self.config.last_version in self.installed_versions else Colors.WARNING
                    print(f"  {last_version_color}🎮 上次版本: {self.config.last_version}{Colors.ENDC}")
                
                print(f"\n{Colors.BOLD}主菜单:{Colors.ENDC}")
                print_menu_item("1", "启动游戏", "启动上次使用的版本")
                print_menu_item("2", "选择版本启动", "从已安装版本中选择")
                print_menu_item("3", "版本管理器", "管理游戏版本")
                print_menu_item("4", "整合包管理", "安装/管理整合包")
                print_menu_item("5", "模组管理", "安装/管理模组")
                print_menu_item("6", "数据包管理", "安装/管理数据包")
                print_menu_item("7", "资源包管理", "安装/管理资源包")
                print_menu_item("8", "光影包管理", "安装/管理光影包")
                print_menu_item("9", "账号管理", "登录/切换账号")
                print_menu_item("10", "内存优化", "调整内存分配")
                print_menu_item("11", "设置", "修改启动器配置")
                print_menu_item("12", "帮助", "查看帮助信息")
                print_menu_item("0", "退出", "退出启动器")
                
                choice = input(f"\n{Colors.BLUE}请选择操作 (0-12): {Colors.ENDC}").strip()

                if choice == "0":
                    print_success("感谢使用，再见!")
                    break
                elif choice == "1":
                    if self.config.last_version and self.config.last_version in self.installed_versions:
                        self.launch_minecraft(self.config.last_version)
                    else:
                        print_warning("上次版本不可用，请先选择版本")
                    input("\n按任意键继续...")
                elif choice == "2":
                    version = self.show_installed_versions(selectable=True)
                    if version:
                        self.config.last_version = version
                        self.save_config()
                        self.launch_minecraft(version)
                    input("\n按任意键继续...")
                elif choice == "3":
                    self.version_manager()
                elif choice == "4":
                    self.modpack_manager()
                elif choice == "5":
                    self.mod_manager()
                elif choice == "6":
                    self.datapack_manager()
                elif choice == "7":
                    self.resourcepack_manager()
                elif choice == "8":
                    self.shaderpack_manager()
                elif choice == "9":
                    self.login_screen()
                elif choice == "10":
                    self.memory_optimization_screen()
                elif choice == "11":
                    self.settings_screen()
                elif choice == "12":
                    self.show_help()
                    input("\n按任意键继续...")
                else:
                    print_warning("无效选择")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                _shutdown_requested = True
                print(f"\n{Colors.WARNING}检测到中断，正在退出...{Colors.ENDC}")
                break

    def show_help(self):
        clear_screen()
        print_header("帮助信息")
        
        help_text = f"""
{Colors.CYAN}关于本启动器{Colors.ENDC}
本启动器是一个独立的 Minecraft 启动器，不依赖官方启动器，提供完整的功能支持。

{Colors.CYAN}主要功能{Colors.ENDC}
{Colors.GREEN}✓{Colors.ENDC} 直接从 Mojang 获取版本列表
{Colors.GREEN}✓{Colors.ENDC} 下载并管理多个 Minecraft 版本
{Colors.GREEN}✓{Colors.ENDC} 整合包管理（支持 Modrinth 搜索和本地导入）
{Colors.GREEN}✓{Colors.ENDC} 数据包管理（全局数据包和世界数据包）
{Colors.GREEN}✓{Colors.ENDC} 离线登录（支持多账号）
{Colors.GREEN}✓{Colors.ENDC} 自动下载库文件和资源文件
{Colors.GREEN}✓{Colors.ENDC} 智能内存优化配置
{Colors.GREEN}✓{Colors.ENDC} 多线程高速下载
{Colors.GREEN}✓{Colors.ENDC} 自动下载合适的 Java 运行时
{Colors.GREEN}✓{Colors.ENDC} 模组/资源包/光影包管理
{Colors.GREEN}✓{Colors.ENDC} 支持中断下载并自动清理

{Colors.CYAN}数据包说明{Colors.ENDC}
• 全局数据包：放在 datapacks 文件夹，可用于所有世界
• 世界数据包：放在存档的 datapacks 文件夹，只对特定世界生效
• 支持 pack.mcmeta 格式解析
• 支持启用/禁用数据包（通过 .disabled 后缀）

{Colors.CYAN}使用技巧{Colors.ENDC}
• 首次使用会自动检查 Java 环境
• 版本列表中的 {Colors.YELLOW}★{Colors.ENDC} 表示已安装
• 整合包支持 Modrinth 格式和 CurseForge 格式
• 数据包可以全局安装或安装到指定世界
• 下载过程中可按 Ctrl+C 中断
• 所有配置保存在 minecraft_launcher_config.json

{Colors.CYAN}数据路径{Colors.ENDC}
默认数据路径: {Colors.GREEN}{self.config.minecraft_data_path}{Colors.ENDC}
        """
        print(help_text)

# ==================== 程序入口 ====================
if __name__ == "__main__":
    try:
        try:
            import psutil
        except ImportError:
            pass
        
        launcher = MinecraftLauncher()
        launcher.main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}程序被用户中断{Colors.ENDC}")
    except Exception as e:
        logger.exception("程序异常")
        print(f"\n{Colors.FAIL}程序出错: {e}{Colors.ENDC}")
        input("按任意键退出...")