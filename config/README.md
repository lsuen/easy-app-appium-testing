# 配置说明

## 配置文件结构

Easy-App 现在使用**多配置文件**架构，按功能拆分：

```
config/
├── appium.yaml # Appium 服务配置（路径、端口、启动模式等）
├── device.yaml # 设备与应用配置（平台、设备名、应用信息等）
└── test.yaml # 测试运行配置（超时、日志级别、鲁棒模式等）
```

## 配置加载方式

### 1. 默认加载（推荐）

不指定配置文件时，自动加载 `config/` 目录下的所有配置文件：

```bash
python main.py
# 自动加载: config/appium.yaml + config/device.yaml + config/test.yaml
```

### 2. 指定目录

```bash
python main.py -c config/
# 加载 config/ 目录下的所有配置文件
```

### 3. 指定单个文件（向后兼容）

```bash
python main.py -c config/settings.yaml
# 只加载单个配置文件（兼容旧版本）
```

### 4. 代码中使用

```python
from utils.config_loader import ConfigLoader

# 默认加载 config/ 目录
config = ConfigLoader()

# 加载指定目录
config = ConfigLoader('config/')

# 加载单个文件
config = ConfigLoader('config/appium.yaml')

# 加载多个文件
config = ConfigLoader([
 'config/appium.yaml',
 'config/device.yaml'
])
```

## 配置文件详解

### appium.yaml - Appium 服务配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `appium_server_path` | string | `pkg/appium/...` | Appium 可执行文件路径 |
| `server_host` | string | `127.0.0.1` | Appium 服务主机 |
| `server_port` | int | `4723` | Appium 服务端口 |
| `base_url` | string | `http://localhost:4723` | Appium 连接地址 |
| `start_mode` | string | `window` | **启动模式**：`window`（独立窗口）或 `background`（后台线程） |
| `auto_start_server` | boolean | `true` | 是否自动启动 Appium |
| `start_timeout` | int | `40` | 启动等待超时时间（秒） |
| `command_timeout` | int | `300` | Appium newCommandTimeout（秒） |
| `session_http_timeout` | int | `180` | HTTP 读超时（秒） |
| `wait_activity_timeout` | int | `10` | 等待 Activity 超时（秒） |
| `log_level` | string | `INFO` | Appium 日志级别 |
| `android_home` | string | `pkg` | Android SDK 路径 |

### device.yaml - 设备与应用配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `platform` | string | `Android` | 平台类型：`Android` / `iOS` |
| `device_name` | string | `emulator-5554` | 设备名称或 ID |
| `automation_name` | string | `UiAutomator2` | 自动化引擎 |
| `app_package` | string | - | Android 包名 |
| `app_activity` | string | - | Android 启动 Activity |
| `no_reset` | boolean | `false` | 不重置应用状态 |
| `unicode_keyboard` | boolean | `true` | 启用 Unicode 输入法 |
| `reset_keyboard` | boolean | `true` | 测试后重置输入法 |

### test.yaml - 测试运行配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `timeout` | int | `10` | 元素查找超时时间（秒） |
| `headless` | boolean | `false` | 无头模式 |
| `log_level` | string | `INFO` | 日志级别 |
| `robust_mode` | boolean | `true` | 启用鲁棒模式 |

## Appium 启动模式

### 模式 1: window（独立窗口，推荐）

**特点**：
- 打开独立 cmd 窗口，可见 Appium 实时日志
- 不阻塞主进程，性能稳定
- 方便调试，可以看到完整日志
- 测试结束后自动关闭窗口

**配置**：
```yaml
# config/appium.yaml
start_mode: window
```

**使用场景**：
- 日常开发和调试
- 需要查看 Appium 日志
- 推荐大多数用户使用

### 模式 2: background（后台线程）

**特点**：
- 无窗口，后台运行
- 使用线程消费 stdout/stderr，避免缓冲区阻塞
- 日志记录到文件
-  无法实时查看 Appium 输出

**配置**：
```yaml
# config/appium.yaml
start_mode: background
```

**使用场景**：
- CI/CD 环境
- 不需要实时查看日志
- 需要保持终端干净

## 迁移指南

### 从旧版本迁移

旧版本使用单个 `settings.yaml`，新版本自动拆分：

1. **保留旧配置**：`config/settings.yaml` 已备份，可继续使用
2. **使用新配置**：删除 `--app-config` 参数，自动使用新结构
3. **混合使用**：可以指定旧文件 `python main.py -c config/settings.yaml`

### 配置优先级

当多个配置文件存在时，后加载的配置会覆盖先加载的：

```
默认配置 < appium.yaml < device.yaml < test.yaml
```

## 注意事项

1. **配置文件顺序**：按 `appium.yaml → device.yaml → test.yaml` 顺序加载
2. **配置合并**：同名配置项，后面的文件会覆盖前面的
3. **向后兼容**：仍支持单个 `settings.yaml` 文件
4. **路径配置**：`android_home` 等路径支持相对路径（相对项目根目录）

## 示例

### 示例 1: 使用默认配置

```bash
python main.py
```

### 示例 2: 使用自定义配置目录

```bash
python main.py -c my_config/
```

### 示例 3: 使用旧版单文件配置

```bash
python main.py -c config/settings.yaml
```

### 示例 4: 切换 Appium 启动模式

```yaml
# config/appium.yaml
start_mode: background # 切换到后台模式
```

```bash
python main.py
```
