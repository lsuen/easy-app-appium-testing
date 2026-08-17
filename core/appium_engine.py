"""
Appium 移动端自动化引擎实现
"""
import subprocess
from typing import Dict, Any
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.client_config import AppiumClientConfig
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
import os

from core.engine import BaseEngine
from utils.logger import Logger


class AppiumEngine(BaseEngine):
    """Appium 移动端自动化引擎"""
    
    # By 映射
    BY_MAPPING = {
        'id': AppiumBy.ID,
        'xpath': AppiumBy.XPATH,
        'accessibility_id': AppiumBy.ACCESSIBILITY_ID,
        'class_name': AppiumBy.CLASS_NAME,
        'android_uiautomator': AppiumBy.ANDROID_UIAUTOMATOR,
        'ios_predicate': AppiumBy.IOS_PREDICATE,
        'ios_class_chain': AppiumBy.IOS_CLASS_CHAIN,
        'name': AppiumBy.NAME,
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = Logger.get_logger('AppiumEngine')
        self.options = None
    
    # ==================== 生命周期管理 ====================
    
    def start(self):
        """启动 Appium 会话"""
        self.logger.info("启动 Appium 会话...")

        # 修复 UiAutomation not connected 错误：强制停止旧服务
        self._cleanup_uiautomator_server()

        # 构建配置选项
        self.options = AppiumOptions()
        self.options.platform_name = self.config.get('platform', 'Android')
        self.options.device_name = self.config.get('device_name', 'emulator-5554')
        self.options.automation_name = self.config.get('automation_name', 'UiAutomator2')

        # 应用配置
        if self.config.get('app_path'):
            self.options.app = self.config['app_path']
        if self.config.get('app_package'):
            self.options.app_package = self.config['app_package']
        if self.config.get('app_activity'):
            self.options.app_activity = self.config['app_activity']

        # 其他配置
        self.options.no_reset = self.config.get('no_reset', False)
        # newCommandTimeout 单位为秒；兼容历史把毫秒误写入 YAML 的情况
        cmd_to = int(self.config.get('command_timeout', 300))
        if cmd_to > 1000:
            cmd_to = max(60, cmd_to // 1000)
        self.options.new_command_timeout = min(max(cmd_to, 60), 7200)

        # 增强稳定性配置
        self.options.force_app_launch = True
        self.options.skip_server_installation = True
        self.options.uiautomator2_server_launch_timeout = 60000
        self.options.uiautomator2_server_install_timeout = 60000

        # Android 特有配置
        if self.config.get('platform', 'Android').lower() == 'android':
            self.options.unicode_keyboard = self.config.get('unicode_keyboard', True)
            self.options.reset_keyboard = self.config.get('reset_keyboard', True)
            if self.config.get('wait_activity_timeout'):
                self.options.wait_activity_timeout = self.config['wait_activity_timeout']

        # iOS 特有配置
        elif self.config.get('platform', 'Android').lower() == 'ios':
            self.options.udid = self.config.get('udid')
            self.options.bundle_id = self.config.get('bundle_id')
            self.options.platform_version = self.config.get('platform_version')

        # 启动驱动
        server_url = self.config.get('base_url', 'http://localhost:4723')
        self.logger.info(f"连接 Appium 服务: {server_url}")

        # Selenium 4 默认 timeout 取自 socket.getdefaulttimeout()，在 Windows 上常为 None，
        # 会导致创建会话时 HTTP 读阻塞直至 adb/驱动层"假死"。必须显式设置秒级超时。
        session_http_timeout = int(self.config.get('session_http_timeout', 180))
        session_http_timeout = max(30, min(session_http_timeout, 600))
        client_config = AppiumClientConfig(
            remote_server_addr=server_url,
            timeout=session_http_timeout,
        )
        self.logger.info(
            f"HTTP 会话超时: {session_http_timeout}s（可在 settings.yaml 设置 session_http_timeout）"
        )

        # 等待服务就绪并重试连接
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.logger.info(f"尝试连接 Appium (第 {attempt + 1}/{max_retries} 次)...")
                self.driver = webdriver.Remote(
                    command_executor=server_url,
                    options=self.options,
                    client_config=client_config,
                )
                self.logger.info("Appium 会话启动成功")
                return
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"连接失败 (尝试 {attempt + 1}/{max_retries}): {error_msg[:200]}")
                if attempt < max_retries - 1:
                    self.logger.info(f"等待 {retry_delay} 秒后重试...")
                    import time
                    time.sleep(retry_delay)
                    # 再次清理，防止状态残留
                    self._cleanup_uiautomator_server()
                else:
                    self.logger.error(f"Appium 会话启动失败，已重试 {max_retries} 次")
                    self.logger.error(f"最后错误: {error_msg}")
                    raise

    def _cleanup_uiautomator_server(self):
        """强制停止并卸载设备上的 UiAutomator2 服务，修复 'UiAutomation not connected' 错误"""
        try:
            self.logger.info("正在深度清理设备 UiAutomator2 服务状态...")
            device = self.config.get('device_name')
            
            # 1. 重启 ADB 服务（解决 PC 端 ADB 假死问题）
            self.logger.info("正在重启 ADB 服务...")
            subprocess.run("adb kill-server", shell=True, capture_output=True, timeout=5)
            subprocess.run("adb start-server", shell=True, capture_output=True, timeout=5)
            
            # 2. 等待设备重新连接
            import time
            time.sleep(2)
            
            # 3. 强制停止相关服务
            stop_cmds = [
                f"adb -s {device} shell am force-stop io.appium.uiautomator2.server",
                f"adb -s {device} shell am force-stop io.appium.uiautomator2.server.test"
            ]
            # 4. 卸载旧服务（修复 corrupted state 的关键）
            uninstall_cmds = [
                f"adb -s {device} uninstall io.appium.uiautomator2.server",
                f"adb -s {device} uninstall io.appium.uiautomator2.server.test"
            ]
            
            for cmd in stop_cmds + uninstall_cmds:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            
            self.logger.info("UiAutomator2 服务状态已深度清理，下次启动将自动重新安装")
        except Exception as e:
            self.logger.warning(f"深度清理 UiAutomator2 服务状态失败 (可忽略): {e}")
    
    def quit(self):
        """关闭 Appium 会话"""
        self.logger.info("关闭 Appium 会话...")
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Appium 会话已关闭")
        except Exception as e:
            self.logger.warning(f"关闭会话时出错: {e}")
    
    # ==================== 应用管理 ====================
    
    def open_app(self):
        """打开应用"""
        self.logger.info("打开应用")
        self.driver.activate_app(self.config['app_package'])
    
    def close_app(self):
        """关闭应用"""
        self.logger.info("关闭应用")
        self.driver.terminate_app(self.config['app_package'])
    
    def background_app(self, seconds: int):
        """应用置入后台"""
        self.logger.info(f"应用置入后台 {seconds} 秒")
        self.driver.background_app(seconds)
    
    def reset_app(self):
        """重置应用"""
        self.logger.info("重置应用")
        self.driver.reset()
    
    # ==================== 元素定位 ====================
    
    def _get_by(self, by: str):
        """转换 By 类型"""
        return self.BY_MAPPING.get(by, AppiumBy.ID)
    
    def find_element(self, selector: str, by: str = 'id'):
        """查找单个元素"""
        try:
            return self.driver.find_element(self._get_by(by), selector)
        except WebDriverException as e:
            self.logger.error(f"查找元素失败: {selector} ({by}) - {e}")
            raise
    
    def find_elements(self, selector: str, by: str = 'id'):
        """查找多个元素"""
        try:
            return self.driver.find_elements(self._get_by(by), selector)
        except WebDriverException as e:
            self.logger.error(f"查找元素列表失败: {selector} ({by}) - {e}")
            raise
    
    def is_element_present(self, selector: str, by: str = 'id', timeout: int = 5) -> bool:
        """检查元素是否存在"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((self._get_by(by), selector))
            )
            return True
        except TimeoutException:
            return False
    
    # ==================== 等待机制 ====================
    
    def wait_for_element(self, selector: str, by: str = 'id', timeout: int = 10,
                         poll_frequency: float = 0.5):
        """等待元素出现"""
        self.logger.debug(f"等待元素: {selector} ({by})")
        return WebDriverWait(
            self.driver, timeout, poll_frequency=poll_frequency
        ).until(
            EC.presence_of_element_located((self._get_by(by), selector))
        )
    
    def wait_for_element_disappear(self, selector: str, by: str = 'id', timeout: int = 10):
        """等待元素消失"""
        self.logger.debug(f"等待元素消失: {selector} ({by})")
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located((self._get_by(by), selector))
        )
    
    # ==================== 基础操作 ====================
    
    def click(self, selector: str, by: str = 'id'):
        """点击元素"""
        elem = self.wait_for_element(selector, by, timeout=self.config.get('timeout', 10))
        elem.click()
        self.logger.debug(f"点击元素: {selector}")
    
    def long_click(self, selector: str, by: str = 'id', duration: int = 2000):
        """长按元素"""
        elem = self.wait_for_element(selector, by)
        # 使用 W3C Actions 实现长按
        actions = ActionChains(self.driver)
        actions.click_and_hold(elem).pause(duration / 1000).release().perform()
        self.logger.debug(f"长按元素: {selector} ({duration}ms)")
    
    def input(self, selector: str, text: str, by: str = 'id', clear_first: bool = True):
        """输入文本"""
        elem = self.wait_for_element(selector, by)
        if clear_first:
            elem.clear()
        elem.send_keys(text)
        self.logger.debug(f"输入文本到 {selector}: {text}")
    
    def clear(self, selector: str, by: str = 'id'):
        """清空输入框"""
        elem = self.find_element(selector, by)
        elem.clear()
        self.logger.debug(f"清空输入框: {selector}")
    
    def get_text(self, selector: str, by: str = 'id') -> str:
        """获取元素文本"""
        elem = self.wait_for_element(selector, by)
        text = elem.text
        self.logger.debug(f"获取文本 {selector}: {text}")
        return text
    
    def get_attribute(self, selector: str, attribute: str, by: str = 'id') -> str:
        """获取元素属性"""
        elem = self.find_element(selector, by)
        return elem.get_attribute(attribute)
    
    # ==================== 手势操作 ====================
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500):
        """滑动操作"""
        # 使用 execute_script 实现滑动
        self.driver.execute_script('mobile: swipe', {
            'startX': start_x,
            'startY': start_y,
            'endX': end_x,
            'endY': end_y,
            'duration': duration
        })
        self.logger.debug(f"滑动: ({start_x},{start_y}) -> ({end_x},{end_y})")
    
    def swipe_to_direction(self, direction: str = 'up', duration: int = 500):
        """向指定方向滑动"""
        size = self.get_window_size()
        width = size['width']
        height = size['height']
        
        # 计算起点和终点
        if direction.lower() == 'up':
            start_x, start_y = width // 2, height * 3 // 4
            end_x, end_y = width // 2, height // 4
        elif direction.lower() == 'down':
            start_x, start_y = width // 2, height // 4
            end_x, end_y = width // 2, height * 3 // 4
        elif direction.lower() == 'left':
            start_x, start_y = width * 3 // 4, height // 2
            end_x, end_y = width // 4, height // 2
        elif direction.lower() == 'right':
            start_x, start_y = width // 4, height // 2
            end_x, end_y = width * 3 // 4, height // 2
        else:
            raise ValueError(f"不支持的滑动方向: {direction}")
        
        self.swipe(start_x, start_y, end_x, end_y, duration)
        self.logger.debug(f"向{direction}滑动")
    
    def tap(self, x: int, y: int):
        """坐标点击"""
        # 使用 execute_script 实现坐标点击
        self.driver.execute_script('mobile: clickGesture', {
            'x': x,
            'y': y
        })
        self.logger.debug(f"坐标点击: ({x},{y})")
    
    def scroll_to(self, selector: str, by: str = 'id', max_swipes: int = 10):
        """滚动到元素"""
        self.logger.debug(f"滚动到元素: {selector}")
        for _ in range(max_swipes):
            if self.is_element_present(selector, by, timeout=2):
                return self.find_element(selector, by)
            self.swipe_to_direction('up')
        raise TimeoutException(f"滚动 {max_swipes} 次后仍未找到元素: {selector}")
    
    def pinch(self, selector: str, by: str = 'id', percent: int = 75, steps: int = 50):
        """捏合（缩小）"""
        elem = self.find_element(selector, by)
        self.driver.pinch(element=elem, percent=percent, steps=steps)
        self.logger.debug(f"捏合元素: {selector}")
    
    def zoom(self, selector: str, by: str = 'id', percent: int = 75, steps: int = 50):
        """展开（放大）"""
        elem = self.find_element(selector, by)
        self.driver.zoom(element=elem, percent=percent, steps=steps)
        self.logger.debug(f"展开元素: {selector}")
    
    # ==================== 设备操作 ====================
    
    def press_keycode(self, keycode: int, meta_state: int = None):
        """按下按键码"""
        self.driver.press_keycode(keycode, meta_state)
        self.logger.debug(f"按下按键码: {keycode}")
    
    def back(self):
        """返回键"""
        self.driver.back()
        self.logger.debug("点击返回键")
    
    def home(self):
        """Home 键"""
        self.driver.press_keycode(3)  # Android Home 键码
        self.logger.debug("点击 Home 键")
    
    def screenshot(self, filepath: str) -> str:
        """截图"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        self.driver.get_screenshot_as_file(filepath)
        self.logger.debug(f"截图已保存: {filepath}")
        return filepath
    
    def get_screenshot_as_base64(self) -> str:
        """获取 base64 编码的截图"""
        return self.driver.get_screenshot_as_base64()
    
    def get_window_size(self) -> Dict[str, int]:
        """获取窗口尺寸"""
        size = self.driver.get_window_size()
        return {'width': size['width'], 'height': size['height']}
    
    # ==================== 高级操作 ====================
    
    def execute_script(self, script: str, *args):
        """执行 Appium 脚本"""
        return self.driver.execute_script(script, *args)
    
    def action_chain(self) -> ActionChains:
        """获取操作链对象"""
        return ActionChains(self.driver)
    
    def paste(self, selector: str, by: str = 'id'):
        """粘贴文本"""
        elem = self.find_element(selector, by)
        elem.click()
        # Android 粘贴操作
        if self.config.get('platform', 'Android').lower() == 'android':
            self.press_keycode(2901)  # KEYCODE_PASTE
        else:
            # iOS 使用脚本
            self.execute_script('mobile: pasteFromPasteboard')
