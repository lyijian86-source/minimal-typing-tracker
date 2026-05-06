# TypeLedger

[English](./README.md) | **简体中文**

TypeLedger 是一个面向 Windows 的、注重隐私的桌面输入统计工具。它适合希望长期记录每日输入量、会话节奏、小时分布和周效率的用户。

它会在后台运行，常驻系统托盘，只保存汇总指标，不保存你输入的原始文本。

> 当前代码与界面中的产品名仍然是 `Type Record`  
> 我推荐的 GitHub 仓库公开名称是 `type-ledger`

## 快速开始

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

启动后，它可以常驻托盘，在后台持续统计。

## 为什么推荐这个名字

我更推荐把仓库名改成 `TypeLedger`，原因很直接：

- 比泛泛的 `tracker` 更容易记住
- 比抽象名字更容易被搜索到
- 气质更稳，更像“可信的个人数据账本”
- 以后扩展分析能力时也不会显得局限

另外几个也不错的备选：

- `type-pulse`
- `key-ledger`
- `typing-ledger`

## 这个产品解决什么问题

TypeLedger 想帮你回答几类很实际的问题：

- 我今天到底有没有真正写东西？
- 我这周是高产，还是只是看起来很忙？
- 我的产出变化是来自工作更久，还是效率更高？
- 我通常在一天里的哪个时段输入最多？

它是一个长期运行的本地工具，不是文本采集器。

## 适合谁用

- 想记录每日写作节奏的写作者
- 关心输入效率的知识工作者
- 同时使用中英文输入的用户
- 在意隐私、不想把数据上传云端的用户

## 当前能力

| 模块 | 能力 |
| --- | --- |
| 每日统计 | 净字符数、键盘输入、粘贴量、退格次数、准确率估算 |
| 会话分析 | 会话时长、会话输入量、实时速度、最近活跃情况 |
| 趋势视图 | 近 30 天趋势、小时分布、完整历史弹窗 |
| 周效率 | 周产出、活跃时长、活跃效率、周对比视图 |
| 交互体验 | 托盘常驻、中英文界面、可滚动首页、可滚动设置页 |
| 稳定性 | 备份恢复、坏数据清洗、健康报告输出 |
| 隐私 | 只保存聚合数据，不保存原文 |

## 隐私模型

TypeLedger 会保存：

- 计数结果
- 时间戳
- 会话时长
- 小时级总量
- 周级汇总指标

TypeLedger 不会保存：

- 原始输入文本
- 剪贴板文本内容
- 文档内容
- 应用内容

粘贴行为会影响统计结果，但粘贴的具体文字不会被写入磁盘。

## 指标定义

| 指标 | 含义 |
| --- | --- |
| 净字符数 | 首页主计数。包含输入和粘贴，是否扣减退格取决于设置。 |
| 键盘输入 | 只统计直接键盘输入，不含粘贴。 |
| 粘贴量 | 由粘贴行为推断出的输入体量。 |
| 准确率 | 根据保留输入与修正行为估算出的指标。 |
| 当前速度 | 最近 60 秒内的键盘输入字符数。 |
| 峰值 WPM | 按 `5 个字符 = 1 个词` 估算出的峰值速度。 |
| 周效率 | 周总产出除以活跃会话分钟数。 |

## 准确性说明

这个项目使用的是全局键盘钩子，所以它最可靠的信号是**输入行为本身**，而不是“在所有软件里最终落下了多少字符”。

需要明确的限制：

- 中文拼音输入法这类 IME 流程可以稳定记录按键行为，但不一定和最终上屏字符完全相同。
- 退格并不总是之前输入的完美逆操作，尤其是在选区、替换、不同编辑器场景下。
- 管理员权限程序中的输入，普通权限进程可能只能部分感知。

这个产品的取舍很明确：优先保证聚合统计稳定，而不是试图还原精确文本。

## README 建议配图

后续建议补这些截图：

1. 主界面首页
2. 周效率详情弹窗
3. 小时分布弹窗
4. 托盘右键菜单
5. 设置页

建议资源目录：

```text
assets/readme/
```

建议文件名：

- `dashboard-en.png`
- `dashboard-zh.png`
- `weekly-efficiency.png`
- `hourly-view.png`
- `tray-menu.png`
- `settings-dialog.png`

## 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 运行

```powershell
python app.py
```

## 发布状态

当前状态：

- 源码版已经可以正常使用
- 托盘工作流已经完成
- 首页、周效率、历史记录、设置页都可用
- 测试已覆盖存储、指标、托盘文案和关键 UI 烟测
- Windows 打包发布流程还没有最终定稿

## 开发

安装开发依赖：

```powershell
pip install -r requirements-dev.txt
```

运行测试：

```powershell
python -m pytest
```

可选的语法烟测：

```powershell
python -m compileall type_record tests
```

## 数据存储

默认路径：

```text
%APPDATA%\TypeRecord\data\daily_counts.json
%APPDATA%\TypeRecord\config\settings.json
```

当 `%APPDATA%` 不可写时，回退到：

```text
<project>\data\
```

相关耐久性文件：

- `daily_counts.json.bak`
- `health_report.json`

## 稳定性设计

- 备份 JSON 回退
- 坏记录过滤
- 非法日期 / 小时 / 时间戳清洗
- 健康报告输出
- 会话超时与退出时落盘
- 关键窗口流程烟测

## 项目结构

```text
app.py
requirements.txt
requirements-dev.txt
type_record/
  app.py
  config.py
  counter.py
  charting.py
  metrics.py
  storage.py
  tray.py
  ui/
    dialogs.py
    formatting.py
    theme.py
    widgets.py
    window.py
tests/
```

## 路线图

近期优先项：

1. 继续打磨交互一致性与稳定性
2. 补充高质量截图和对外展示素材
3. 准备打包与分发流程
4. 优化新用户理解成本和指标解释

后续可以继续增强的方向：

- Windows 可执行版本
- 更丰富的周对比视图
- 更好的会话回顾能力
- 更清晰的 IME 指标解释层

## 常见问题

### 会保存我输入的具体内容吗？

不会。它只保存计数、时间戳、时长和聚合指标。

### 对中文输入法准确吗？

它对按键行为的统计是稳定的，但不保证在所有输入法流程下都和最终上屏字符完全一致。

### 粘贴会计数吗？

会。粘贴会影响总量指标，但粘贴的文字内容不会被保存。

### 它能当成精确的成文统计器吗？

不能完全等同。它更适合作为稳定的输入行为追踪器，而不是最终成文字符的精确还原器。

## 当前状态

这个产品已经不是最初的简单计数器了，已经具备了真实的桌面工作流和分析能力，但在 UX、打包、截图和公开展示层面还在持续打磨中。
