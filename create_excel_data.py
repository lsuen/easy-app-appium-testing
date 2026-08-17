"""
生成 Excel 测试数据示例
"""
import openpyxl
from openpyxl import Workbook


def create_sample_excel():
    """创建示例 Excel 测试数据"""
    wb = Workbook()
    
    # Sheet 1: 登录测试
    ws1 = wb.active
    ws1.title = "登录测试"
    
    # 表头
    headers = ['id', 'name', 'type', 'platform', 'description', 'priority',
               'selector', 'by', 'value', 'direction', 'duration', 'steps',
               'expected_type', 'expected_value']
    ws1.append(headers)
    
    # 数据行
    ws1.append([
        'TC001', '登录功能测试', 'workflow', 'Android',
        '测试用户登录流程', 'P0',
        '', '', '', '', '', '',
        'text', '欢迎'
    ])
    
    ws1.append([
        'TC002', '输入用户名', 'input', 'Android',
        '输入用户名', 'P0',
        'com.example.app:id/username_edit', 'id', 'testuser', '', '', '',
        '', ''
    ])
    
    ws1.append([
        'TC003', '输入密码', 'input', 'Android',
        '输入密码', 'P0',
        'com.example.app:id/password_edit', 'id', '123456', '', '', '',
        '', ''
    ])
    
    ws1.append([
        'TC004', '点击登录', 'click', 'Android',
        '点击登录按钮', 'P0',
        'com.example.app:id/login_btn', 'id', '', '', '', '',
        'element', 'com.example.app:id/welcome_text'
    ])
    
    # Sheet 2: 功能测试
    ws2 = wb.create_sheet("功能测试")
    ws2.append(headers)
    
    ws2.append([
        'TC005', '点击按钮', 'click', 'All',
        '测试按钮点击', 'P1',
        'com.example.app:id/submit_btn', 'id', '', '', '', '',
        'element', 'com.example.app:id/result_text'
    ])
    
    ws2.append([
        'TC006', '滑动列表', 'swipe', 'All',
        '向上滑动列表', 'P1',
        '', '', '', 'up', '500', '',
        'element', 'com.example.app:id/bottom_item'
    ])
    
    ws2.append([
        'TC007', '搜索功能', 'input', 'Android',
        '输入搜索关键词', 'P1',
        'com.example.app:id/search_edit', 'id', '测试关键词', '', '', '',
        'value', '测试关键词'
    ])
    
    ws2.append([
        'TC008', '滚动到元素', 'scroll', 'All',
        '滚动到目标元素', 'P2',
        'com.example.app:id/target_element', 'id', '', '', '', '',
        'presence', 'com.example.app:id/target_element'
    ])
    
    # 保存
    output_path = 'data/test_data.xlsx'
    wb.save(output_path)
    print(f"Excel 测试数据已生成: {output_path}")


if __name__ == '__main__':
    create_sample_excel()
