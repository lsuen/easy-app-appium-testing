"""
Easy-App 移动端自动化测试框架入口
支持 CLI 参数和 pytest 调度
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from utils.config_loader import ConfigLoader


def generate_allure_report(config: ConfigLoader):
    """生成 Allure 报告
    
    Args:
        config: 配置加载器实例
    """
    try:
        # 获取 allure 命令路径
        allure_cmd = config.get('allure_cmd')
        
        # 如果配置中未指定，尝试自动查找
        if not allure_cmd:
            # 优先使用项目内的 allure
            local_allure = Path('pkg/allurec/bin/allure.bat')
            if local_allure.exists():
                allure_cmd = str(local_allure.absolute())
            else:
                # 回退到系统 PATH
                allure_cmd = 'allure'
        else:
            # 转换为绝对路径（如果配置的是相对路径）
            allure_path = Path(allure_cmd)
            if not allure_path.is_absolute() and allure_path.exists():
                allure_cmd = str(allure_path.absolute())
        
        print(f"\n[INFO] 使用 allure 命令: {allure_cmd}")
        
        # 检查 allure 命令是否可用
        result = subprocess.run(
            [allure_cmd, '--version'],
            capture_output=True,
            text=True,
            shell=True if allure_cmd.endswith('.bat') else False,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            print("[INFO] 生成 Allure 报告...")
            
            # 从配置读取参数
            results_dir = config.get('allure_results_dir', 'allure-results')
            report_dir = config.get('allure_report_dir', 'allure-report')
            clean = config.get('allure_clean', True)
            
            cmd = [
                allure_cmd, 'generate',
                results_dir,
                '-o', report_dir,
            ]
            
            if clean:
                cmd.append('--clean')
            
            subprocess.run(
                cmd, 
                check=True, 
                shell=True if allure_cmd.endswith('.bat') else False,
                encoding='utf-8',
                errors='replace'
            )
            print(f"[INFO] Allure 报告生成成功: {report_dir}/index.html")
        else:
            print(f"[WARN] allure 命令不可用，跳过报告生成")
            print(f"[WARN] 返回码: {result.returncode}")
            print(f"[WARN] 错误输出: {result.stderr}")
            print("[WARN] 安装方法: pip install allure-commandline 或配置 allure_cmd")

    except FileNotFoundError:
        print("[WARN] allure 命令未找到，跳过报告生成")
        print("[WARN] 安装方法: pip install allure-commandline 或配置 allure_cmd")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 生成报告失败: {e}")


def open_allure_report(config: ConfigLoader):
    """打开 Allure 报告
    
    Args:
        config: 配置加载器实例
    """
    report_dir = config.get('allure_report_dir', 'allure-report')
    report_path = Path(report_dir) / 'index.html'
    if report_path.exists():
        os.startfile(str(report_path))
        print(f"[INFO] 已打开报告: {report_path.absolute()}")
    else:
        print("[WARN] 报告文件不存在，请先生成报告")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Easy-App 移动端自动化测试框架',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                           # 运行所有测试
  python main.py -d data/test_data.json    # 指定数据文件
  python main.py -c config/settings.yaml   # 指定配置文件
  python main.py -m TC001                  # 运行指定用例
  python main.py --no-report               # 不生成报告
  python main.py --open-report             # 生成并打开报告
        """
    )

    parser.add_argument(
        '-d', '--data-file',
        default='data/test_data.json',
        help='测试数据文件路径 (JSON/Excel)，默认: data/test_data.json'
    )

    parser.add_argument(
        '-c', '--app-config',
        default='config/',
        help='配置文件路径（目录或文件），默认: config/'
    )

    parser.add_argument(
        '-m', '--marker',
        help='pytest 标记筛选 (如: smoke, regression)'
    )

    parser.add_argument(
        '-k', '--keyword',
        help='pytest 关键词筛选'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='不生成 Allure 报告'
    )

    parser.add_argument(
        '--open-report',
        action='store_true',
        help='生成并打开 Allure 报告'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='无头模式运行'
    )

    parser.add_argument(
        '--no-auto-server',
        action='store_true',
        help='不自动启动 Appium 服务（需要手动启动）'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 加载配置
    config = ConfigLoader(args.app_config)

    # 构建 pytest 参数
    pytest_args = [
        'tests/',
        f'--data-file={args.data_file}',
        f'--app-config={args.app_config}',
        f'--alluredir={config.get("allure_results_dir", "allure-results")}',
        '-v',
        '-s',
        '--tb=short'
    ]

    # 服务管理参数
    if args.no_auto_server:
        pytest_args.append('--no-auto-server')

    # 标记筛选
    if args.marker:
        pytest_args.append(f'-m={args.marker}')

    # 关键词筛选
    if args.keyword:
        pytest_args.append(f'-k={args.keyword}')

    # 详细输出
    if args.verbose:
        pytest_args.append('-vv')

    # 打印配置信息
    print("=" * 60)
    print("Easy-App 移动端自动化测试框架")
    print("=" * 60)
    print(f"测试数据: {args.data_file}")
    print(f"配置文件: {args.app_config}")
    print(f"Allure 结果: {config.get('allure_results_dir', 'allure-results')}/")
    auto_server = (
        "否（--no-auto-server）"
        if args.no_auto_server
        else "是（见 config/settings.yaml：appium_server_path，通常为 pkg/appium/...）"
    )
    print(f"自动启动 Appium: {auto_server}")
    print(f"配置文件: {args.app_config}（支持多文件：appium.yaml + device.yaml + test.yaml）")
    print("=" * 60)

    # 清理旧的测试结果
    results_dir = config.get('allure_results_dir', 'allure-results')
    allure_results_dir = Path(results_dir)
    if allure_results_dir.exists():
        shutil.rmtree(allure_results_dir)
    allure_results_dir.mkdir(exist_ok=True)

    # 运行 pytest
    print("\n[INFO] 开始运行测试...")
    import pytest
    exit_code = pytest.main(pytest_args)

    # 生成报告
    should_generate = not args.no_report and config.get('auto_generate_report', True)
    if should_generate:
        generate_allure_report(config)

        # 打开报告
        should_open = args.open_report or config.get('auto_open_report', False)
        if should_open:
            open_allure_report(config)

    # 返回退出码
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
