"""
Pytest 配置和 Fixtures
包含：配置加载、驱动管理、测试数据加载、操作路由分发、失败截图
"""
from datetime import datetime
from pathlib import Path

import allure
import pytest

from core.appium_engine import AppiumEngine
from core.appium_server_manager import AppiumServerManager
from drivers.data_driver import DataDriver
from utils.config_loader import ConfigLoader
from utils.logger import Logger


# ==================== Pytest Hooks ====================

def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "smoke: 冒烟测试标记")
    config.addinivalue_line("markers", "regression: 回归测试标记")


def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--data-file",
        action="store",
        default="data/test_data.json",
        help="指定测试数据文件路径"
    )
    parser.addoption(
        "--app-config",
        action="store",
        default="config/",
        help="指定配置文件路径（目录或文件），默认: config/"
    )
    parser.addoption(
        "--no-auto-server",
        action="store_true",
        default=False,
        help="不自动启动 Appium（需手动启动服务，忽略配置中的 auto_start_server）",
    )


# ==================== Fixtures ====================

@pytest.fixture(scope="session", autouse=True)
def appium_service(request, config):
    """会话级 Appium 服务管理 Fixture"""
    auto_start = config.get("auto_start_server", False)
    if request.config.getoption("--no-auto-server"):
        auto_start = False
    
    if auto_start:
        manager = AppiumServerManager()
        success = manager.start(config)
        
        if not success:
            pytest.exit("Appium 服务启动失败，测试终止")
        
        yield manager
        
        # 会话结束后停止服务
        manager.stop()
    else:
        # 不自动启动，但检查服务是否运行
        manager = AppiumServerManager()
        if not manager.is_running(config):
            pytest.exit("Appium 服务未运行，请手动启动或设置 auto_start_server: true")
        yield manager


@pytest.fixture(scope="session")
def config(request):
    """会话级配置 Fixture"""
    config_path = request.config.getoption("--app-config")
    return ConfigLoader(config_path).to_dict()


@pytest.fixture(scope="function")
def driver(request, config):
    """函数级 Appium 驱动 Fixture"""
    eng = AppiumEngine(config)
    eng.start()
    
    yield eng
    
    eng.quit()


# ==================== 测试数据加载 ====================

def load_test_data(data_path: str, config: dict) -> list:
    """
    加载并解析测试数据
    
    Args:
        data_path: 数据文件路径
        config: 配置字典（用于占位符替换）
    
    Returns:
        测试数据列表
    """
    loader = DataDriver(data_path)
    data = loader.load()
    
    # 替换占位符
    context = {
        'device_name': config.get('device_name', ''),
        'platform': config.get('platform', ''),
        'app_package': config.get('app_package', ''),
    }
    
    return [DataDriver.replace_placeholders(case, context) for case in data]


# ==================== 智能选择器识别 ====================

def _auto_detect_by(selector: str, data: dict = None) -> tuple:
    """
    自动识别选择器类型
    
    Args:
        selector: 选择器字符串
        data: 测试数据字典（可选）
    
    Returns:
        (by_type, cleaned_selector) 元组
    """
    # 显式指定优先
    if data and data.get('by'):
        return data['by'], selector
    
    # 自动识别
    if selector.startswith('//'):
        return 'xpath', selector
    elif selector.startswith('id='):
        return 'id', selector[3:]
    elif selector.startswith('accessibility_id='):
        return 'accessibility_id', selector[17:]
    elif selector.startswith('android='):
        return 'android_uiautomator', selector[8:]
    elif selector.startswith('ios='):
        return 'ios_predicate', selector[4:]
    
    # 默认 CSS（实际为 id）
    return 'id', selector


# ==================== 测试类型路由分发器 ====================

def execute_test_case(driver, data: dict, config: dict):
    """
    根据 type 字段分发执行不同的测试操作
    
    Args:
        driver: Appium 驱动实例
        data: 测试数据字典
        config: 配置字典
    """
    test_type = data.get('type', '').lower()
    robust = config and config.get('robust_mode', False)
    
    # 工作流模式
    if test_type == 'workflow':
        steps = data.get('steps', [])
        for step in steps:
            _execute_step(driver, step, robust)
        return
    
    # 单步操作模式
    _execute_step(driver, data, robust)


def _execute_step(driver, step: dict, robust: bool = False):
    """
    执行单个操作步骤
    
    Args:
        driver: Appium 驱动实例
        step: 步骤数据字典
        robust: 是否启用鲁棒模式
    """
    action = step.get('action', step.get('type', '')).lower()
    selector = step.get('selector', '')
    by = step.get('by', 'id')
    value = step.get('value', '')
    direction = step.get('direction', 'up')
    duration = step.get('duration', 500)
    
    try:
        if action == 'click':
            if robust and selector:
                driver.robust_click(selector, by)
            elif selector:
                driver.click(selector, by)
        
        elif action == 'input' or action == 'type':
            if robust and selector:
                driver.robust_input(selector, value, by)
            elif selector:
                driver.input(selector, value, by)
        
        elif action == 'long_click':
            duration = step.get('duration', 2000)
            driver.long_click(selector, by, duration)
        
        elif action == 'swipe':
            driver.swipe_to_direction(direction, duration)
        
        elif action == 'scroll':
            driver.scroll_to(selector, by)
        
        elif action == 'tap':
            x = step.get('x', 0)
            y = step.get('y', 0)
            driver.tap(x, y)
        
        elif action == 'wait':
            timeout = step.get('timeout', 10)
            driver.wait_for_element(selector, by, timeout)
        
        elif action == 'screenshot':
            filepath = step.get('filepath', f'screenshots/step_{datetime.now().strftime("%H%M%S")}.png')
            driver.screenshot(filepath)
        
        elif action == 'back':
            driver.back()
        
        elif action == 'home':
            driver.home()
        
        elif action == 'keycode':
            keycode = step.get('keycode', 0)
            driver.press_keycode(keycode)
        
        else:
            raise ValueError(f"不支持的操作类型: {action}")
    
    except Exception as e:
        raise RuntimeError(f"执行操作 [{action}] 失败: {e}")


# ==================== 统一断言引擎 ====================

def assert_test_result(driver, data: dict):
    """
    根据 expected_type 执行断言验证
    
    Args:
        driver: Appium 驱动实例
        data: 测试数据字典
    """
    expected_type = data.get('expected_type', '').lower()
    expected_value = str(data.get('expected_value', ''))
    selector = data.get('selector', '')
    by = data.get('by', 'id')
    
    if expected_type == 'text':
        # 验证元素文本
        if selector:
            actual_text = driver.get_text(selector, by)
            assert expected_value in actual_text, \
                f"文本验证失败: 期望包含 '{expected_value}', 实际为 '{actual_text}'"
        else:
            page_source = driver.driver.page_source
            assert expected_value in page_source, \
                f"文本验证失败: 页面中未找到 '{expected_value}'"
    
    elif expected_type == 'element' or expected_type == 'presence':
        # 验证元素存在
        is_present = driver.is_element_present(selector, by, timeout=5)
        assert is_present, f"元素不存在: {selector} ({by})"
    
    elif expected_type == 'value':
        # 验证元素值（输入框等）
        attr_value = driver.get_attribute(selector, 'value', by)
        assert expected_value in attr_value, \
            f"值验证失败: 期望包含 '{expected_value}', 实际为 '{attr_value}'"
    
    elif expected_type == 'screenshot':
        # 截图验证（仅截图，不验证）
        filepath = f'screenshots/verify_{datetime.now().strftime("%H%M%S")}.png'
        driver.screenshot(filepath)

    elif expected_type in ('none', '', 'skip'):
        # 无断言，仅执行
        pass

    else:
        raise ValueError(f"不支持的验证类型: {expected_type}")


# ==================== Pytest Hooks - 失败截图 ====================

def pytest_generate_tests(metafunc):
    """
    动态参数化测试用例
    根据测试数据文件动态生成测试用例
    """
    if 'data' in metafunc.fixturenames:
        # 加载测试数据
        config_path = metafunc.config.getoption("--app-config")
        data_path = metafunc.config.getoption("--data-file")
        
        from utils.config_loader import ConfigLoader
        config = ConfigLoader(config_path).to_dict()
        
        test_cases = load_test_data(data_path, config)
        
        # 过滤平台
        platform = config.get('platform', 'All')
        test_cases = [
            case for case in test_cases
            if case.get('platform', 'All') in ('All', platform)
        ]
        
        # 参数化
        metafunc.parametrize("data", test_cases, ids=[c['id'] for c in test_cases])


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图并附加到 Allure"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call' and report.failed:
        driver = item.funcargs.get('driver')
        if driver:
            # 生成截图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"screenshots/fail_{item.name}_{timestamp}.png"
            
            try:
                # 截图
                driver.screenshot(screenshot_path)
                
                # 附加到 Allure 报告
                with open(screenshot_path, 'rb') as f:
                    allure.attach(
                        f.read(),
                        name="失败截图",
                        attachment_type=allure.attachment_type.PNG
                    )
            except Exception as e:
                allure.attach(str(e), name="截图失败", attachment_type=allure.attachment_type.TEXT)
