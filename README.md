# Easy-App 移动端自动化测试框架

> **Easy-App Appium Testing** — Appium + pytest + Allure mobile UI automation
> framework. Data-driven test cases in JSON/Excel, zero code changes for
> Android & iOS. 极简移动端自动化测试框架。

作者：孙文龙

## 项目特性

- **极简设计** - 核心代码少于 500 行，开箱即用
- **数据驱动** - JSON/Excel 编写用例，无需写代码
- **统一接口** - Abstract Base Class + 工厂模式
- **三级防御** - 原生操作 → 手势模拟 → 坐标操作
- **智能等待** - 内置显式等待 + 轮询机制
- **Allure 报告** - 步骤详情 + 失败截图 + 分类统计
- **跨平台** - Android/iOS 配置切换，零代码改动
- **服务自管理** - 自动启动/停止 Appium 服务，无需手动操作

## 环境要求

- Python 3.8+
- Node.js 18+ (运行 Appium 服务)
- Appium 3.x (`npm install -g appium` 或使用项目本地安装)
- Android SDK / platform-tools (Android 测试) 或 Xcode (iOS 测试)

## 安装

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Appium(二选一)

方式 A：全局安装（推荐，最简单）

```bash
npm install -g appium
appium --version
```

方式 B：项目本地安装

```bash
cd pkg/appium
npm install
```

> 说明：为避免仓库体积过大，`pkg/appium/node_modules`、`pkg/platform-tools`、`pkg/allurec` 等二进制目录未纳入版本库。

### 3. 安装 Android platform-tools（Android 测试需要）

`adb` 用于设备检测与应用安装，官方下载地址：

- https://developer.android.com/tools/releases/platform-tools

或者直接安装完整版 Android Studio SDK，并配置环境变量：

- `ANDROID_HOME` = SDK 根目录
- 将 `%ANDROID_HOME%\platform-tools` 加入 `PATH`

验证：`adb devices`

### 4. 安装 Allure（报告生成）

方式 A：通过 pip 安装命令行工具

```bash
pip install allure-commandline
```

方式 B：从官方仓库下载命令行工具

- https://github.com/allure-framework/allure2/releases
- 解压后将 `bin` 目录加入 `PATH`

验证：`allure --version`

### 环境变量速查（可选）

| 变量 | 用途 |
|------|------|
| `ANDROID_HOME` | Android SDK 根目录，框架会自动使用 |
| `ANDROID_SDK_ROOT` | 与 ANDROID_HOME 等效 |
| `PATH` | 需包含 appium、adb、allure 可执行目录 |

框架的查找优先级统一为：**配置文件指定路径 → 项目 `pkg/` 目录 → 系统 PATH**。因此即使不配置环境变量，只要命令在 PATH 中即可运行。

## 快速开始

### 1. 配置测试

编辑 `config/settings.yaml`（或拆分配置 config/ 目录）：

```yaml
platform: Android
device_name: emulator-5554
app_package: com.example.app
app_activity: .MainActivity
base_url: http://localhost:4723
auto_start_server: true   # 自动启动 Appium 服务
server_host: 127.0.0.1
server_port: 4723
```

### 3. 编写测试数据

JSON 格式 (`data/test_data.json`)：

```json
[
  {
    "id": "TC001",
    "name": "登录功能测试",
    "type": "workflow",
    "platform": "Android",
    "priority": "P0",
    "steps": [
      {
        "action": "input",
        "selector": "com.example.app:id/username",
        "by": "id",
        "value": "testuser"
      },
      {
        "action": "input",
        "selector": "com.example.app:id/password",
        "by": "id",
        "value": "123456"
      },
      {
        "action": "click",
        "selector": "com.example.app:id/login_btn",
        "by": "id"
      }
    ],
    "expected_type": "text",
    "expected_value": "欢迎"
  }
]
```

Excel 格式 (`data/test_data.xlsx`)：

使用 `create_excel_data.py` 生成示例：

```bash
python create_excel_data.py
```

### 4. 运行测试

```bash
# 运行所有测试（自动启动 Appium）
python main.py

# 指定数据文件
python main.py -d data/test_data.json

# 指定配置文件
python main.py -c config/settings.yaml

# 运行指定用例
python main.py -k TC001

# 生成并打开报告
python main.py --open-report

# 不自动启动 Appium（需手动启动）
python main.py --no-auto-server
```

### 5. 查看报告

```bash
# 生成并打开 Allure 报告
python main.py --open-report

# 仅生成报告
allure generate allure-results -o allure-report --clean

# 实时查看报告
allure serve allure-results
```

## 项目结构

```
Easy-app/
├── config/
│   ├── settings.yaml          # 主配置（旧版单文件，向后兼容）
│   ├── appium.yaml            # Appium 服务配置
│   ├── device.yaml            # 设备配置
│   └── test.yaml              # 测试配置
├── core/
│   ├── engine.py              # 抽象引擎基类
│   ├── appium_engine.py       # Appium 引擎实现
│   └── appium_server_manager.py  # Appium 服务管理器
├── data/
│   ├── test_data.json         # JSON 测试数据
│   └── test_data.xlsx         # Excel 测试数据
├── drivers/
│   └── data_driver.py         # 数据加载器
├── utils/
│   ├── config_loader.py       # 配置加载器
│   └── logger.py              # 日志管理器
├── tests/
│   ├── conftest.py            # Pytest fixtures & 路由
│   └── test_example.py        # 通用数据驱动测试
├── pkg/
│   ├── appium/                # 本地 Appium（node_modules 不入库）
│   └── ...
├── pkg/appium/package.json    # 本地 npm 清单
├── screenshots/               # 失败截图
├── logs/                      # 日志文件
├── allure-results/            # Allure 原始数据
├── allure-report/             # Allure HTML 报告
├── main.py                    # 入口文件
└── requirements.txt           # 依赖列表
```

## 测试数据格式

### 标准字段

| 字段 | 必填 | 说明 |
|------|------|------|
| id | 是 | 用例唯一标识 (TC001) |
| name | 是 | 用例名称 |
| type | 是 | 操作类型 |
| platform | 否 | 适用平台 (Android/iOS/All) |
| selector | 否 | 元素定位器 |
| by | 否 | 定位方式 (id/xpath/accessibility_id) |
| value | 否 | 输入值 |
| direction | 否 | 滑动方向 (up/down/left/right) |
| duration | 否 | 操作时长（毫秒） |
| steps | 否 | 多步骤工作流数组 |
| expected_type | 是 | 验证类型 |
| expected_value | 是 | 期望值 |
| priority | 否 | 优先级 (P0/P1/P2) |
| description | 否 | 用例描述 |

### 支持的操作类型

| 类型 | 说明 | 示例 |
|------|------|------|
| click | 点击元素 | {"action": "click", "selector": "...", "by": "id"} |
| input | 输入文本 | {"action": "input", "selector": "...", "value": "文本"} |
| long_click | 长按元素 | {"action": "long_click", "duration": 2000} |
| swipe | 滑动操作 | {"action": "swipe", "direction": "up"} |
| scroll | 滚动到元素 | {"action": "scroll", "selector": "..."} |
| tap | 坐标点击 | {"action": "tap", "x": 500, "y": 1000} |
| wait | 等待元素 | {"action": "wait", "selector": "...", "timeout": 10} |
| back | 返回键 | {"action": "back"} |
| home | Home 键 | {"action": "home"} |
| keycode | 按键码 | {"action": "keycode", "keycode": 66} |
| screenshot | 截图 | {"action": "screenshot", "filepath": "..."} |
| workflow | 多步骤工作流 | {"steps": [...]} |

### 支持的验证类型

| 类型 | 说明 |
|------|------|
| text | 验证元素文本包含期望值 |
| element / presence | 验证元素存在 |
| value | 验证元素 value 属性 |
| screenshot | 截图验证 |

## 架构设计

### 分层架构

```
测试数据层 (data/)
    ↓
数据驱动层 (drivers/)
    ↓
核心引擎层 (core/)
    ↓
测试执行层 (tests/)
    ↓
工具层 (utils/)
```

### 核心模块

#### 1. 抽象引擎基类 (core/engine.py)

定义移动端自动化操作的统一接口，包括：
- 生命周期管理：start(), quit()
- 应用管理：open_app(), close_app(), background_app()
- 元素定位：find_element(), find_elements(), is_element_present()
- 等待机制：wait_for_element(), wait_for_element_disappear()
- 基础操作：click(), long_click(), input(), clear(), get_text()
- 手势操作：swipe(), tap(), scroll_to(), pinch(), zoom()
- 设备操作：press_keycode(), back(), home(), screenshot()
- 鲁棒性：robust_click(), robust_input() (三级防御链)

#### 2. Appium 引擎实现 (core/appium_engine.py)

继承 BaseEngine，支持：
- Android (UiAutomator2) 和 iOS (XCUITest)
- 8 种元素定位方式映射
- 智能等待机制 (WebDriverWait)
- 三级防御链实现
- TouchAction 手势操作

By 映射：
- id → AppiumBy.ID
- xpath → AppiumBy.XPATH
- accessibility_id → AppiumBy.ACCESSIBILITY_ID
- class_name → AppiumBy.CLASS_NAME
- android_uiautomator → AppiumBy.ANDROID_UIAUTOMATOR
- ios_predicate → AppiumBy.IOS_PREDICATE
- ios_class_chain → AppiumBy.IOS_CLASS_CHAIN
- name → AppiumBy.NAME

#### 3. 数据加载器 (drivers/data_driver.py)

加载并解析 JSON/Excel 测试数据：
- load(): 自动识别格式并加载
- _load_json(): JSON 数据解析
- _load_excel(): Excel 数据解析（支持多 Sheet）
- replace_placeholders(): 占位符替换 (${var})

#### 4. Pytest 配置 (tests/conftest.py)

核心功能：
- Fixtures: config (会话级), driver (函数级)
- 路由分发器: execute_test_case() 根据 type 字段分发执行
- 断言引擎: assert_test_result() 根据 expected_type 执行断言
- 失败截图 Hook: pytest_runtest_makereport() 自动截图并附加到 Allure

#### 5. Appium 服务管理器 (core/appium_server_manager.py)

单例模式，管理 Appium 服务生命周期：
- start(): 启动 Appium 服务
- stop(): 停止 Appium 服务
- is_running(): 检查服务状态

服务路径优先级：
1. 配置中的 appium_server_path（config/appium.yaml）
2. pkg/appium/node_modules/.bin/appium.cmd (项目本地，需先执行 `cd pkg/appium && npm install`)
3. 系统 PATH 中的 appium

特性：
- 自动检测服务是否已运行
- 智能等待服务就绪 (最多 30 秒)
- 跨平台支持 (Windows/Unix)
- 进程树管理 (正确终止子进程)

#### 6. 配置加载器 (utils/config_loader.py)

支持 YAML/JSON 格式，提供默认配置：
- platform: Android
- device_name: emulator-5554
- automation_name: UiAutomator2
- base_url: http://localhost:4723
- timeout: 10
- robust_mode: True

#### 7. 日志管理器 (utils/logger.py)

单例模式，提供：
- 文件日志 (RotatingFileHandler, 10MB, 5 备份)
- 控制台日志
- 统一格式: [时间] [级别] [名称] 消息
- 日志文件: logs/EasyApp_YYYYMMDD.log

## 高级功能

### 三级防御链

启用 robust_mode: true 后，框架会自动使用三级防御策略：

Click 防御链：
1. Level 1: 原生 click()
2. Level 2: 坐标点击 tap(x, y)
3. Level 3: ActionChains 手势操作

Input 防御链：
1. Level 1: 原生 input()
2. Level 2: 清空后逐字符 send_keys()
3. Level 3: Clipboard 粘贴方式

### 占位符替换

在测试数据中使用 ${变量名} 占位符：

```json
{
  "selector": "${app_package}:id/username"
}
```

支持的变量：${device_name}, ${platform}, ${app_package}

### 智能选择器识别

自动识别选择器类型：
- //... → xpath
- id=... → id
- android=... → android_uiautomator
- 其他 → id (默认)

### 失败自动截图

测试失败时自动截图并附加到 Allure 报告，截图保存在 screenshots/ 目录。

## Appium 服务管理

### 配置选项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| auto_start_server | boolean | false | 是否自动启动 Appium 服务 |
| appium_server_path | string | null | 自定义 Appium 路径 |
| server_host | string | 127.0.0.1 | Appium 服务主机 |
| server_port | int | 4723 | Appium 服务端口 |
| base_url | string | http://localhost:4723 | Appium 连接地址 |

### 使用场景

场景 1: 使用内置 Appium (推荐)

```yaml
auto_start_server: true
```

```bash
python main.py
# 自动启动 pkg/appium/node_modules/.bin/appium.cmd（需先本地安装）
# 测试结束后自动停止
```

场景 2: 使用自定义 Appium 版本

```yaml
auto_start_server: true
appium_server_path: /path/to/custom/appium
```

场景 3: 手动管理服务

```yaml
auto_start_server: false
```

```bash
# 手动启动 Appium
appium --address 127.0.0.1 --port 4723

# 运行测试 (不自动启动)
python main.py --no-auto-server
```

### 故障排查

问题 1: 服务启动超时

原因: Appium 启动缓慢或端口被占用

解决:
```bash
# 检查端口占用
netstat -ano | findstr :4723

# 手动启动查看错误
appium --address 127.0.0.1 --port 4723
```

问题 2: 找不到 Appium

原因: 未安装或未加入 PATH

解决:
```bash
# 方式 1: 全局安装
npm install -g appium

# 方式 2: 项目本地安装
cd pkg/appium
npm install

# 验证
appium --version
```

问题 3: 服务未停止

原因: 进程异常退出

解决:
```bash
# Windows 强制终止
taskkill /F /IM node.exe /T
```

## 调试技巧

### 查看详细日志

```bash
python main.py -v
```

日志文件位置: logs/EasyApp_YYYYMMDD.log

### 运行单个用例

```bash
python main.py -k TC001
```

### 使用 pytest 直接运行

```bash
pytest tests/ --data-file=data/test_data.json -v -s
```

### 元素定位调试

使用 Appium Inspector 获取准确的元素定位器：

```bash
# 安装 Appium Inspector
npm install -g appium-inspector

# 启动
appium-inspector
```

### 获取设备信息

```bash
# Android 设备列表
adb devices

# 查看应用包名
adb shell pm list packages | grep your_app
```

## 常见问题

Q: Appium 连接失败？

A: 检查 Appium 服务是否启动，端口是否为 4723

Q: 找不到元素？

A: 使用 Appium Inspector 检查元素定位器是否正确

Q: 测试超时？

A: 增加 config/settings.yaml 中的 timeout 值

Q: 中文输入失败？

A: 确保配置了 unicode_keyboard: true 和 reset_keyboard: true

## AI Agent 集成

Easy-App 采用数据驱动 + 分层架构设计，天然适合 AI 编码 / 测试 Agent 接入：

### 1. 让 Agent 编写测试用例

测试用例就是 JSON/Excel 数据，无需修改框架代码。可直接让 Agent 生成 `data/` 下的用例文件，
框架的 `tests/conftest.py` 会自动参数化运行。示例提示词：

```
请根据 config/device.yaml 中的应用信息，为登录页面编写一组 JSON 测试用例，
写入 data/test_data.json，需要覆盖：正常登录、密码错误、空账号。
字段格式参照 README.md 的操作类型和验证类型。
```

### 2. 让 Agent 运行测试并读取结果

Agent 可以执行以下命令并解析输出：

```bash
# 运行测试
python main.py -d data/test_data.json

# 仅运行某一个用例
python main.py -k TC001

# 详细日志（供排障）
python main.py -v
```

运行产物（Agent 可读取）：
- `logs/EasyApp_YYYYMMDD.log` - 全量运行日志
- `allure-results/` - Allure 原始结果（JSON）
- `screenshots/` - 失败截图（PNG）

### 3. 让 Agent 排查失败用例

框架在失败时自动截图并写入日志，Agent 可通过以下流程定位问题：

1. 读取 `logs/` 中最近日志，定位报错的操作类型和元素定位器
2. 查看 `screenshots/` 对应时段的截图
3. 用 Appium Inspector 修正定位器，更新 `data/` 中的用例，重新运行

### 4. 接入 Cursor / Claude Code / 其他 Agent

项目根目录已提供 `AGENTS.md`，这些工具会自动读取该文件了解项目结构与约定。
如需为 Agent 配置额外的 API Key（Appium 无需 Key），建议通过环境变量注入或放置在
`config/` 下单独的文件中，切勿提交密钥入库（仓库已通过 .gitignore 排除 .secrets）。

## 注意事项

1. **Appium 服务**: 运行测试前确保 Appium 服务已启动（或设置 auto_start_server: true）
2. **设备连接**: 确保设备已连接或模拟器已启动
3. **应用安装**: 确保测试应用已安装到设备上
4. **元素定位**: 使用 Appium Inspector 获取准确的元素定位器
5. **等待时间**: 合理设置超时时间，避免测试过慢或过快
6. **端口占用**: 确保 4723 端口未被占用
7. **Node.js**: Appium 需要 Node.js 环境
8. **权限**: Windows 可能需要管理员权限终止进程

## 更新日志

### [2.1.0] - 2026-08-17

开源整理
- 移除版本库中大体积二进制（pkg/appium/node_modules、pkg/allurec、pkg/appuicheck、pkg/platform-tools）
- 补充官方安装指引：Appium / platform-tools / Allure 下载地址与环境变量说明
- 配置默认改为自动查找系统 PATH，保证克隆后开箱即用
- 新增 AI Agent 集成章节与 AGENTS.md
- 新增 .gitignore 安全规则，排除密钥与本地工具目录

### [2.0.0] - 2026-04-29

新增功能：

Appium 服务管理
- 内置 Appium 3.3.1 到 pkg/appium 目录（package.json + package-lock.json）
- 新增 AppiumServerManager 单例类，管理服务生命周期
- 支持自动启动/停止 Appium 服务
- 智能路径查找：配置路径 → pkg 目录 → 系统 PATH
- 跨平台支持 (Windows/Unix)
- 进程树管理，正确终止子进程

配置增强
- 新增 auto_start_server: 自动启动 Appium 服务
- 新增 appium_server_path: 自定义 Appium 路径
- 新增 server_host: Appium 服务主机
- 新增 server_port: Appium 服务端口

CLI 参数
- 新增 --no-auto-server: 不自动启动 Appium 服务

技术改进
- 服务启动智能等待（最多 30 秒）
- 端口占用检测
- 优雅终止服务（支持 SIGTERM 和强制终止）
- 日志集成到统一日志系统

依赖
- 新增: appium@3.3.1 (内置在 pkg 目录)

### [1.0.0] - 2026-04-28

初始版本
- 基于 Appium + pytest + allure 的移动端自动化测试框架
- 数据驱动测试（JSON/Excel）
- 三级防御链提高稳定性
- 智能等待机制
- 跨平台支持（Android/iOS）
- Allure 企业级报告集成

## 扩展方向

- 多设备并行执行
- 测试用例标签管理 (smoke/regression)
- 测试数据加密
- 截图对比验证
- 性能数据收集
- CI/CD 集成
- 移动端截图/录屏
- 分布式执行 (Appium Grid)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 致谢

参考了 Easy-Web 项目的架构设计哲学。
