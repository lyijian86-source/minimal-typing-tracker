# TypeLedger

**简体中文** | [English](./README.md)

TypeLedger 是一个注重隐私的 Windows 桌面输入统计工具。它帮助你理解每天的输入产出、会话节奏、小时分布和周效率，同时不会保存你输入的具体内容。

它适合写作者、开发者、研究者、学生，以及希望长期观察自己输入节奏的知识工作者。

> GitHub 仓库：`Yijian6/type-ledger`
> 数据兼容性：内部数据路径仍然保留 `TypeRecord`

## 为什么使用它

TypeLedger 主要帮你回答这些问题：

- 我今天到底有没有真正写东西？
- 这一周比上一周更高效吗？
- 产出变多是因为工作更久，还是因为效率更高？
- 我通常在一天中的哪个时间段输入最多？
- 我的写作或编码节奏有没有变得更稳定？

## 隐私说明

TypeLedger 只保存汇总数字。

它会记录输入字符数、粘贴字符数、退格次数、会话时长、小时统计和周汇总等指标。它不会保存原始输入文本、剪贴板内容、窗口标题、网站地址、文件名、截图或按键序列。

应用在你的 Windows 本机运行，不需要云账号。

## 下载和使用

绿色版 Windows 发布包是：

```text
TypeLedger-windows-portable.zip
```

使用方式：

1. 从 GitHub Releases 下载压缩包。
2. 解压到你信任的文件夹。
3. 运行 `TypeLedger.exe`。
4. 如果主窗口启动后隐藏了，请在系统托盘里找到图标。

当前版本还没有代码签名。Windows SmartScreen 或安全软件可能会提示风险，因为这个应用需要使用全局键盘钩子来统计按键数量。这是本地输入统计工具常见的情况。TypeLedger 不会保存你输入的具体内容。

## 功能

| 模块 | 能力 |
| --- | --- |
| 每日统计 | 净字符数、键盘输入、粘贴字符、退格次数、准确率估算 |
| 会话节奏 | 当前会话、上一会话、会话时长、最近活跃情况 |
| 速度估算 | 基于最近键盘输入估算 CPM 和 WPM |
| 周效率 | 周产出、活跃时长、活跃效率、较上周和目标的对比 |
| 历史记录 | 每日记录、近 30 天趋势、小时分布、CSV 导出 |
| 系统托盘 | 后台运行，支持托盘菜单操作 |
| 本地化 | 支持英文和简体中文界面 |

## 数据位置

TypeLedger 的本地数据保存在：

```text
%APPDATA%\TypeRecord\
```

文件夹名称继续使用 `TypeRecord`，是为了兼容早期版本的数据。

主要文件：

- `data\daily_counts.json`
- `config\settings.json`
- `data\logs\type_record.log`

## 从源码运行

要求：

- Windows
- Python 3.11+

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## 打包 Windows 绿色版

安装开发依赖：

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
```

执行打包：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

输出文件：

```text
dist\TypeLedger\TypeLedger.exe
dist\TypeLedger-windows-portable.zip
```

## 开发检查

运行测试：

```powershell
python -m pytest
```

需要时运行代码检查：

```powershell
ruff check .
```

## 给用户的发布说明

- 这是一个本地 Windows 桌面应用。
- 它只统计汇总输入活动。
- 它不会保存你输入的具体内容。
- 当前绿色版还没有代码签名。
- 因为统计输入需要全局键盘钩子，部分安全软件可能会提示风险。

## 许可证

当前还没有声明许可证。如果要更大范围发布或接受外部贡献，建议先补充许可证。
