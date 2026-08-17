# AGENTS.md

作者：孙文龙
用途：为 AI 编码 / 测试 Agent 提供项目使用指南

## 项目概览

Easy-App 是基于 Appium + pytest + Allure 的移动端自动化测试框架。

核心特点：
- 数据驱动：测试用例写在 JSON/Excel 文件（`data/`），无需修改代码
- 分层架构：data -> drivers -> core -> tests -> utils
- 服务自管理：可自动启动/停止 Appium 服务

## 目录结构速览

```
config/      配置文件（appium.yaml / device.yaml / test.yaml）
core/        测试引擎（engine.py 抽象基类 + appium_engine.py 实现）
data/        测试数据（JSON/Excel 用例）
drivers/     数据加载器（JSON/Excel 解析、占位符替换）
tests/       pytest 入口（conftest.py：fixtures、路由分发、断言、失败截图）
utils/       配置加载与日志
main.py      CLI 入口
```

## 常用命令

```bash
pip install -r requirements.txt    # 安装 Python 依赖
npm install -g appium              # 安装 Appium（全局）
python main.py                     # 运行全部测试
python main.py -d data/test.json   # 指定数据文件
python main.py -k TC001            # 运行指定用例
python main.py -v                  # 详细日志
python main.py --no-auto-server    # 不自动启动 Appium（需手动启动）
python main.py --open-report       # 生成并打开 Allure 报告
pytest tests/ --data-file=data/test_data.json -v -s   # 直接使用 pytest
```

## 编写测试用例（Agent 常用）

在 `data/` 下新增或修改 JSON 用例。字段约定（详见 README.md）：

| 字段 | 说明 |
|------|------|
| id | 用例唯一标识，如 TC001 |
| type | click / input / swipe / tap / wait / back / home / keycode / workflow |
| by | id / xpath / accessibility_id / android_uiautomator / ios_predicate 等 |
| expected_type | text / element / value / screenshot / none |
| expected_value | 期望值 |

`workflow` 类型使用 `steps` 数组串联多个单步操作。`${var}` 占位符支持
`${device_name}`、`${platform}`、`${app_package}`。

## 排障指引（Agent 排查失败用例）

1. 读 `logs/EasyApp_YYYYMMDD.log` 定位失败操作
2. 查看 `screenshots/` 中对应截图
3. 用 Appium Inspector 校准元素定位器
4. 修改 data/ 用例后重跑 `python main.py -k <id>`

## 约定

- 禁止提交密钥：`.secrets/`、`*.token`、`*.key` 已列入 .gitignore
- pkg/ 下二进制目录不入库，安装方式：`cd pkg/appium && npm install`
- 配置查找优先级：配置指定路径 -> 项目 pkg/ 目录 -> 系统 PATH