"""
通用数据驱动测试用例
从 JSON/Excel 文件加载测试数据并自动执行
"""
import allure
import pytest

from tests.conftest import load_test_data, execute_test_case, assert_test_result


@allure.epic("移动端自动化测试")
@allure.feature("数据驱动测试引擎")
class TestMobileAutoDynamic:
    """动态生成的数据驱动测试类"""
    
    @allure.story("用例: {data[name]}")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_auto_execute(self, driver, data: dict, config):
        """
        自动执行测试用例
        
        执行流程：
        1. 打开应用
        2. 执行操作（根据 type 路由）
        3. 验证结果（根据 expected_type 路由）
        4. 附加信息到报告
        """
        # 步骤 1: 打开应用
        with allure.step(f"打开应用: {data.get('app_package', config.get('app_package', 'N/A'))}"):
            if config.get('app_package'):
                driver.open_app()
        
        # 步骤 2: 执行操作
        with allure.step(f"执行操作 [{data['type']}]: {data['name']}"):
            execute_test_case(driver, data, config)
        
        # 步骤 3: 验证结果
        with allure.step(f"验证结果 [{data['expected_type']}]: {data['expected_value']}"):
            assert_test_result(driver, data)
        
        # 附加信息到报告
        if data.get('description'):
            allure.attach(data['description'], "用例描述", allure.attachment_type.TEXT)
        
        allure.attach(data.get('priority', 'P1'), "优先级", allure.attachment_type.TEXT)
        allure.attach(data['id'], "用例ID", allure.attachment_type.TEXT)
