"""
移动端自动化引擎抽象基类
定义统一的移动端操作接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseEngine(ABC):
    """移动端自动化引擎基类 - 定义统一接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
    
    # ==================== 生命周期管理 ====================
    
    @abstractmethod
    def start(self):
        """启动 Appium 会话"""
        pass
    
    @abstractmethod
    def quit(self):
        """关闭 Appium 会话"""
        pass
    
    # ==================== 应用管理 ====================
    
    @abstractmethod
    def open_app(self):
        """打开应用"""
        pass
    
    @abstractmethod
    def close_app(self):
        """关闭应用"""
        pass
    
    @abstractmethod
    def background_app(self, seconds: int):
        """应用置入后台"""
        pass
    
    @abstractmethod
    def reset_app(self):
        """重置应用"""
        pass
    
    # ==================== 元素定位 ====================
    
    @abstractmethod
    def find_element(self, selector: str, by: str = 'id'):
        """查找单个元素"""
        pass
    
    @abstractmethod
    def find_elements(self, selector: str, by: str = 'id'):
        """查找多个元素"""
        pass
    
    @abstractmethod
    def is_element_present(self, selector: str, by: str = 'id', timeout: int = 5) -> bool:
        """检查元素是否存在"""
        pass
    
    # ==================== 等待机制 ====================
    
    @abstractmethod
    def wait_for_element(self, selector: str, by: str = 'id', timeout: int = 10, 
                         poll_frequency: float = 0.5):
        """等待元素出现"""
        pass
    
    @abstractmethod
    def wait_for_element_disappear(self, selector: str, by: str = 'id', timeout: int = 10):
        """等待元素消失"""
        pass
    
    # ==================== 基础操作 ====================
    
    @abstractmethod
    def click(self, selector: str, by: str = 'id'):
        """点击元素"""
        pass
    
    @abstractmethod
    def long_click(self, selector: str, by: str = 'id', duration: int = 2000):
        """长按元素"""
        pass
    
    @abstractmethod
    def input(self, selector: str, text: str, by: str = 'id', clear_first: bool = True):
        """输入文本"""
        pass
    
    @abstractmethod
    def clear(self, selector: str, by: str = 'id'):
        """清空输入框"""
        pass
    
    @abstractmethod
    def get_text(self, selector: str, by: str = 'id') -> str:
        """获取元素文本"""
        pass
    
    @abstractmethod
    def get_attribute(self, selector: str, attribute: str, by: str = 'id') -> str:
        """获取元素属性"""
        pass
    
    # ==================== 手势操作 ====================
    
    @abstractmethod
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500):
        """滑动操作"""
        pass
    
    @abstractmethod
    def swipe_to_direction(self, direction: str = 'up', duration: int = 500):
        """向指定方向滑动 (up/down/left/right)"""
        pass
    
    @abstractmethod
    def tap(self, x: int, y: int):
        """坐标点击"""
        pass
    
    @abstractmethod
    def scroll_to(self, selector: str, by: str = 'id', max_swipes: int = 10):
        """滚动到元素"""
        pass
    
    @abstractmethod
    def pinch(self, selector: str, by: str = 'id', percent: int = 75, steps: int = 50):
        """捏合（缩小）"""
        pass
    
    @abstractmethod
    def zoom(self, selector: str, by: str = 'id', percent: int = 75, steps: int = 50):
        """展开（放大）"""
        pass
    
    # ==================== 设备操作 ====================
    
    @abstractmethod
    def press_keycode(self, keycode: int, meta_state: int = None):
        """按下按键码"""
        pass
    
    @abstractmethod
    def back(self):
        """返回键"""
        pass
    
    @abstractmethod
    def home(self):
        """Home 键"""
        pass
    
    @abstractmethod
    def screenshot(self, filepath: str) -> str:
        """截图"""
        pass
    
    @abstractmethod
    def get_screenshot_as_base64(self) -> str:
        """获取 base64 编码的截图"""
        pass
    
    @abstractmethod
    def get_window_size(self) -> Dict[str, int]:
        """获取窗口尺寸"""
        pass
    
    # ==================== 高级操作 ====================
    
    @abstractmethod
    def execute_script(self, script: str, *args):
        """执行 Appium 脚本"""
        pass
    
    @abstractmethod
    def action_chain(self) -> Any:
        """获取操作链对象（用于复杂手势）"""
        pass
    
    # ==================== 鲁棒性操作（三级防御链） ====================
    
    def robust_click(self, selector: str, by: str = 'id', retries: int = 3):
        """
        三级防御链点击
        Level 1: 原生 click()
        Level 2: 坐标点击 (tap)
        Level 3: ActionChains 手势操作
        """
        last_error = None
        for level in range(1, retries + 1):
            try:
                if level == 1:
                    self.click(selector, by)
                elif level == 2:
                    elem = self.find_element(selector, by)
                    location = elem.location
                    size = elem.size
                    x = location['x'] + size['width'] // 2
                    y = location['y'] + size['height'] // 2
                    self.tap(x, y)
                else:
                    elem = self.find_element(selector, by)
                    self.action_chain().move_to_element(elem).click().perform()
                return
            except Exception as e:
                last_error = e
                continue
        raise last_error
    
    def robust_input(self, selector: str, text: str, by: str = 'id', retries: int = 3):
        """
        三级防御链输入
        Level 1: 原生 input()
        Level 2: 清空后逐字符输入
        Level 3: 使用按键码输入
        """
        last_error = None
        for level in range(1, retries + 1):
            try:
                if level == 1:
                    self.input(selector, text, by)
                elif level == 2:
                    self.clear(selector, by)
                    elem = self.find_element(selector, by)
                    elem.send_keys(text)
                else:
                    self.clear(selector, by)
                    # 使用 clipboard 方式
                    self.execute_script('mobile: setClipboard', {
                        'text': text,
                        'label': 'text',
                        'contentType': 'plaintext'
                    })
                    self.paste(selector, by)
                return
            except Exception as e:
                last_error = e
                continue
        raise last_error
    
    @abstractmethod
    def paste(self, selector: str, by: str = 'id'):
        """粘贴文本"""
        pass
