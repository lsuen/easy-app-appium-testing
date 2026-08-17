"""
Appium 服务管理器
负责启动、停止和检查 Appium 服务的状态
支持两种启动模式:
  - window: 独立 cmd 窗口（推荐，可见日志）
  - background: 后台线程消费输出（无窗口）
"""
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

from utils.logger import Logger


class AppiumServerManager:
    """Appium 服务管理器（单例模式）"""
    
    _instance = None
    _process: Optional[subprocess.Popen] = None
    _logger = None
    _stdout_thread: Optional[threading.Thread] = None
    _stderr_thread: Optional[threading.Thread] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._logger = Logger.get_logger('AppiumServerManager')
    
    # ==================== 服务管理 ====================
    
    def start(self, config: Dict[str, Any]) -> bool:
        """
        启动 Appium 服务

        Args:
            config: 配置字典

        Returns:
            是否启动成功
        """
        # 检查服务是否已在运行
        if self.is_running(config):
            self._logger.info("Appium 服务已在运行")
            return True

        # 获取 appium 路径
        appium_path = self._get_appium_path(config)
        if not appium_path:
            self._logger.error("未找到 Appium 可执行文件")
            return False

        # 获取启动模式
        start_mode = config.get('start_mode', 'window')
        
        # 构建启动命令
        server_host = config.get('server_host', '127.0.0.1')
        server_port = config.get('server_port', 4723)

        cmd = [
            appium_path,
            'server',
            '--address', server_host,
            '--port', str(server_port),
            '--log-level', config.get('log_level', 'INFO').lower()
        ]

        # 准备环境变量
        env = self._prepare_env(config)

        # 根据启动模式选择启动方式
        if start_mode == 'window':
            return self._start_in_window(cmd, env, config, server_host, server_port)
        elif start_mode == 'background':
            return self._start_in_background(cmd, env, config, server_host, server_port)
        else:
            self._logger.error(f"不支持的启动模式: {start_mode}，使用 window 模式")
            return self._start_in_window(cmd, env, config, server_host, server_port)
    
    def stop(self) -> bool:
        """
        停止 Appium 服务

        Returns:
            是否停止成功
        """
        if self._process is None:
            self._logger.info("Appium 服务未运行")
            return True

        self._logger.info("停止 Appium 服务...")

        try:
            if sys.platform == 'win32':
                # Windows: 使用 taskkill 终止进程树
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(self._process.pid)],
                    capture_output=True
                )
            else:
                # Unix/Linux/Mac
                self._process.send_signal(signal.SIGTERM)

            # 等待进程退出
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._logger.warning("服务未响应终止信号，强制终止")
                self._process.kill()
                self._process.wait()

            # 清理线程
            self._stdout_thread = None
            self._stderr_thread = None

            self._logger.info("Appium 服务已停止")
            self._process = None
            return True

        except Exception as e:
            self._logger.error(f"停止 Appium 服务失败: {e}")
            return False
    
    def is_running(self, config: Dict[str, Any]) -> bool:
        """
        检查 Appium 服务是否正在运行
        
        Args:
            config: 配置字典
            
        Returns:
            是否正在运行
        """
        server_host = config.get('server_host', '127.0.0.1')
        server_port = config.get('server_port', 4723)
        return self._check_server_ready(server_host, server_port)
    
    # ==================== 内部方法 ====================

    def _prepare_env(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        准备环境变量

        Args:
            config: 配置字典

        Returns:
            环境变量字典
        """
        env = os.environ.copy()

        # 设置 Android SDK 路径（如果配置中指定）
        android_home = config.get('android_home') or config.get('android_sdk_path')
        if android_home:
            if not os.path.isabs(android_home):
                project_root = Path(__file__).parent.parent
                android_home = str((project_root / android_home).resolve())
            env['ANDROID_HOME'] = android_home
            env['ANDROID_SDK_ROOT'] = android_home
            self._logger.info(f"设置 ANDROID_HOME={android_home}")

        return env

    def _start_in_window(
        self, 
        cmd: list, 
        env: Dict[str, str],
        config: Dict[str, Any],
        server_host: str,
        server_port: int
    ) -> bool:
        """
        在独立 cmd 窗口中启动 Appium（推荐）
        
        Args:
            cmd: 启动命令
            env: 环境变量
            config: 配置字典
            server_host: 服务器主机
            server_port: 服务器端口
            
        Returns:
            是否启动成功
        """
        self._logger.info(f"[窗口模式] 启动 Appium 服务: {' '.join(cmd)}")
        self._logger.info("[窗口模式] Appium 日志将在独立窗口中显示")

        try:
            # Windows 使用 CREATE_NEW_CONSOLE 打开新窗口
            creation_flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0

            self._process = subprocess.Popen(
                cmd,
                creationflags=creation_flags,
                env=env,
                # 不重定向输出，让它在窗口中直接显示
                stdout=None,
                stderr=None
            )

            self._logger.info(f"[窗口模式] Appium 进程已启动 (PID: {self._process.pid})")
            
            # 等待服务启动
            return self._wait_for_server(server_host, server_port, config)

        except Exception as e:
            self._logger.error(f"[窗口模式] 启动 Appium 服务失败: {e}")
            return False

    def _start_in_background(
        self, 
        cmd: list, 
        env: Dict[str, str],
        config: Dict[str, Any],
        server_host: str,
        server_port: int
    ) -> bool:
        """
        在后台启动 Appium，使用线程消费输出（避免阻塞）
        
        Args:
            cmd: 启动命令
            env: 环境变量
            config: 配置字典
            server_host: 服务器主机
            server_port: 服务器端口
            
        Returns:
            是否启动成功
        """
        self._logger.info(f"[后台模式] 启动 Appium 服务: {' '.join(cmd)}")

        try:
            # Windows 使用 CREATE_NEW_PROCESS_GROUP 以便后续正确终止
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                env=env
            )

            self._logger.info(f"[后台模式] Appium 进程已启动 (PID: {self._process.pid})")

            # 启动后台线程消费 stdout
            self._stdout_thread = threading.Thread(
                target=self._consume_output,
                args=(self._process.stdout, "STDOUT"),
                daemon=True
            )
            self._stdout_thread.start()

            # 启动后台线程消费 stderr
            self._stderr_thread = threading.Thread(
                target=self._consume_output,
                args=(self._process.stderr, "STDERR"),
                daemon=True
            )
            self._stderr_thread.start()

            # 等待服务启动
            return self._wait_for_server(server_host, server_port, config)

        except Exception as e:
            self._logger.error(f"[后台模式] 启动 Appium 服务失败: {e}")
            return False

    def _consume_output(self, pipe, prefix: str):
        """
        消费进程输出（在后台线程中运行）
        
        Args:
            pipe: 管道对象 (stdout/stderr)
            prefix: 日志前缀
        """
        try:
            for line in iter(pipe.readline, b''):
                if line:
                    # 解码并记录输出
                    try:
                        text = line.decode('utf-8', errors='replace').strip()
                        if text:
                            self._logger.debug(f"[Appium {prefix}] {text}")
                    except Exception:
                        pass
        except Exception as e:
            self._logger.debug(f"[Appium {prefix}] 读取输出时出错: {e}")
        finally:
            pipe.close()

    def _wait_for_server(
        self,
        server_host: str,
        server_port: int,
        config: Dict[str, Any]
    ) -> bool:
        """
        等待 Appium 服务就绪
        
        Args:
            server_host: 服务器主机
            server_port: 服务器端口
            config: 配置字典
            
        Returns:
            是否就绪
        """
        max_wait = config.get('start_timeout', 40)
        self._logger.info(f"等待 Appium 服务启动 (最多 {max_wait} 秒)...")
        
        for i in range(1, max_wait + 1):
            time.sleep(1)
            if self._check_server_ready(server_host, server_port):
                self._logger.info(f"Appium 服务启动成功 (耗时 {i} 秒)")
                # 额外等待 1 秒确保驱动完全加载
                self._logger.debug("等待驱动完全加载...")
                time.sleep(1)
                return True
            if i % 10 == 0:
                self._logger.info(f"已等待 {i}/{max_wait} 秒，服务仍在启动中...")

        self._logger.error(f"Appium 服务启动超时 (等待 {max_wait} 秒)")
        return False
    
    def _get_appium_path(self, config: Dict[str, Any]) -> Optional[str]:
        """
        获取 Appium 可执行文件路径
        
        Args:
            config: 配置字典
            
        Returns:
            Appium 可执行文件路径
        """
        # 1. 优先使用配置中的路径
        custom_path = config.get('appium_server_path')
        if custom_path:
            # 支持相对路径
            if not os.path.isabs(custom_path):
                project_root = Path(__file__).parent.parent
                custom_path = str(project_root / custom_path)
            
            if os.path.exists(custom_path):
                self._logger.info(f"使用配置的 Appium 路径: {custom_path}")
                return custom_path
            else:
                self._logger.warning(f"配置的 Appium 路径不存在: {custom_path}")
        
        # 2. 尝试 pkg 目录
        project_root = Path(__file__).parent.parent
        pkg_appium = project_root / 'pkg' / 'appium' / 'node_modules' / '.bin' / 'appium.cmd'
        if pkg_appium.exists():
            self._logger.info(f"使用 pkg/appium 目录的 Appium: {pkg_appium}")
            return str(pkg_appium)
        
        # 3. 尝试系统 PATH
        appium_cmd = 'appium'
        
        # 使用 where/which 查找
        try:
            result = subprocess.run(
                ['where', appium_cmd] if sys.platform == 'win32' else ['which', appium_cmd],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                system_path = result.stdout.strip().split('\n')[0]
                self._logger.info(f"使用系统 PATH 的 Appium: {system_path}")
                return system_path
        except Exception:
            pass
        
        return None
    
    def _check_server_ready(self, host: str, port: int) -> bool:
        """
        检查 Appium 服务是否就绪

        Args:
            host: 服务器主机
            port: 服务器端口

        Returns:
            是否就绪
        """
        import socket
        import urllib.request
        import urllib.error
        import json
        
        # 1. 首先检查端口是否可连接
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result != 0:
                    return False
        except Exception:
            return False
        
        # 2. 检查 Appium 状态端点，确保服务完全就绪
        try:
            # 尝试多个端点以确认服务完全就绪
            endpoints = [
                f"http://{host}:{port}/status",
                f"http://{host}:{port}/wd/hub/status",  # 旧版兼容
            ]
            
            for url in endpoints:
                try:
                    req = urllib.request.Request(url, method='GET')
                    req.add_header('Accept', 'application/json')
                    
                    with urllib.request.urlopen(req, timeout=3) as response:
                        if response.status == 200:
                            # 解析响应，确保返回有效的 JSON
                            data = json.loads(response.read().decode('utf-8'))
                            
                            # Appium 3.x 的 /status 返回格式: {"value": {"ready": true, ...}}
                            # 或旧格式: {"status": 0, "value": {...}}
                            if isinstance(data, dict):
                                value = data.get('value', {})
                                if isinstance(value, dict):
                                    # Appium 3.x: 检查 ready 字段
                                    ready = value.get('ready')
                                    if ready is False:
                                        return False
                                    # 如果有 build 信息，说明服务完全就绪
                                    if 'build' in value or ready is True:
                                        return True
                                    # 如果没有 ready 字段但有 value，也认为就绪
                                    return True
                except Exception:
                    # 这个端点失败，尝试下一个
                    continue
            
            return False
            
        except Exception:
            return False
    
    def __del__(self):
        """析构时确保服务已停止"""
        try:
            self.stop()
        except Exception:
            pass
