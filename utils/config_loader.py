"""
配置加载器 - 支持 YAML 和 JSON 格式，支持多配置文件合并
"""
import json
from pathlib import Path
from typing import Dict, Any, Union

import yaml


class ConfigLoader:
    """配置加载器 - 加载并管理测试配置
    
    支持多种加载方式:
        # 单文件（向后兼容）
        ConfigLoader('config/settings.yaml')
        
        # 多文件自动合并
        ConfigLoader(['config/appium.yaml', 'config/device.yaml', 'config/test.yaml'])
        
        # 目录自动加载（按 appium.yaml -> device.yaml -> test.yaml 顺序）
        ConfigLoader('config/')
    """

    # 默认配置
    DEFAULT_CONFIG = {
        'platform': 'Android',
        'device_name': 'emulator-5554',
        'automation_name': 'UiAutomator2',
        'base_url': 'http://localhost:4723',
        'no_reset': False,
        'unicode_keyboard': True,
        'reset_keyboard': True,
        'timeout': 10,
        'command_timeout': 300,
        'session_http_timeout': 180,
        'wait_activity_timeout': 10,
        'headless': False,
        'log_level': 'INFO',
        'robust_mode': True,
        # Appium 启动模式
        'start_mode': 'window',
        'auto_start_server': True,
        'start_timeout': 40,
        'server_host': '127.0.0.1',
        'server_port': 4723,
        # Allure 报告配置
        'allure_cmd': None,  # None 表示自动查找
        'allure_results_dir': 'allure-results',
        'allure_report_dir': 'allure-report',
        'allure_clean': True,
        'auto_generate_report': True,
        'auto_open_report': False,
    }

    # 默认配置文件顺序（按目录加载时）
    DEFAULT_CONFIG_FILES = [
        'appium.yaml',
        'device.yaml', 
        'test.yaml'
    ]

    def __init__(self, config_path: Union[str, List[str], None] = None):
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()

        if config_path is None:
            # 默认加载 config 目录
            self._load_default_config_dir()
        elif isinstance(config_path, str):
            path = Path(config_path)
            if path.is_dir():
                self._load_from_directory(path)
            elif path.exists():
                self.load(str(path))
            else:
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
        elif isinstance(config_path, list):
            # 加载多个配置文件
            for path in config_path:
                self.load(path)
        else:
            raise TypeError(f"不支持的配置路径类型: {type(config_path)}")

    def _load_default_config_dir(self):
        """加载默认 config 目录"""
        config_dir = Path(__file__).parent.parent / 'config'
        if config_dir.exists():
            self._load_from_directory(config_dir)

    def _load_from_directory(self, directory: Path):
        """从目录加载默认配置文件"""
        for filename in self.DEFAULT_CONFIG_FILES:
            file_path = directory / filename
            if file_path.exists():
                self.load(str(file_path))

    def load(self, config_path: str):
        """加载配置文件"""
        path = Path(config_path)

        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ('.yaml', '.yml'):
                self.config.update(self._load_yaml(f))
            elif path.suffix.lower() == '.json':
                self.config.update(json.load(f))
            else:
                raise ValueError(f"不支持的配置格式: {path.suffix}")
    
    def _load_yaml(self, f) -> Dict[str, Any]:
        """加载 YAML 配置"""
        return yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """支持 config['key'] 访问"""
        return self.config[key]
    
    def __contains__(self, key: str) -> bool:
        """支持 'key' in config 判断"""
        return key in self.config
    
    def update(self, updates: Dict[str, Any]):
        """更新配置"""
        self.config.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典"""
        return self.config.copy()
