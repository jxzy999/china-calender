# 📅 中国节假日 & 传统节日日历订阅（iPhone 兼容）

本项目提供包含以下内容的 ICS 订阅：
- 中国法定节假日（含国务院最新调休安排）
- 传统节日（腊八/小年/中元节/元宵/重阳/七夕等）
- 国际节日（情人节/圣诞节/母亲节/父亲节/感恩节等）

数据每 7 天自动刷新（GitHub Actions），用户无需手动更新。

## 📁 项目结构

```
your-repo/
├── .github/workflows/
│   └── update-ics.yml          # 每 7 天自动生成并提交 holidays.ics
├── scripts/
│   └── generate_ics.py         # 核心脚本：生成 ICS
├── data/
│   ├── fixed_holidays.csv      # 固定公历节日（情人节/圣诞节/教师节等）
│   ├── lunar_holidays.csv      # 农历节日规则（腊八/小年/中元/元宵/重阳/七夕等）
│   └── ics_template.ics        # ICS 模板（参考）
├── holidays.ics                # 输出文件（订阅此文件）
├── requirements.txt            # Python 依赖
└── README.md                   # 项目说明与使用指南
```

## 📱 iPhone 导入步骤

1. 复制订阅链接（Raw 文件 URL）：
   `https://raw.githubusercontent.com/<yourname>/<repo>/main/holidays.ics`
2. 打开 iPhone「设置」→「日历」→「账户」→「添加账户」→「其他」
3. 选择「添加已订阅的日历」
4. 粘贴链接 → 点击「下一步」→ 完成

提示：首次导入后，iOS 会在后台自动同步更新；如遇当年节假日调整，等待下一次自动刷新即可。

## 🔍 数据来源与真实性保障

- 法定节假日 & 调休/补班：
  - 来源：[NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)（每年国务院文件发布后更新）
  - 使用仓库公开 JSON（字段包含 `name`/`date`/`isOffDay`），将 `isOffDay=true` 视为休息日，将 `isOffDay=false` 且存在 `name` 视为调休补班。
- 传统节日（农历）：
  - 使用 `lunardate` 将 `lunar_holidays.csv` 中的农历月日转换为公历，处理跨年（腊月）情况。
- 国际与固定节日：
  - 由 `fixed_holidays.csv` 提供（如情人节/圣诞节/教师节/万圣节等）。
- 浮动节日：
  - 脚本中动态计算（母亲节/父亲节/感恩节等）。

## 🛠 使用（本地生成）

不运行 iOS 代码，仅生成 ICS 文件：

1. 安装依赖：
   `pip install -r requirements.txt`
2. 生成文件：
   `python scripts/generate_ics.py`
3. 生成结果：仓库根目录产生 `holidays.ics`。

> 若你需要在 GitHub 自动生成，请直接使用已配置的 Actions，无需本地执行。

## 🤝 贡献与扩展

- 如需新增节日，请在 `data/fixed_holidays.csv` 或 `data/lunar_holidays.csv` 增加条目，并提交 PR。
- 法定节假日数据以 `holiday-cn` 为准，脚本会自动合并与去重。

## ⚠️ 注意

- iPhone 导入使用 Raw 链接；若你的仓库默认分支不是 `main`，请替换为正确分支名。
- GitHub 的 `cron: '0 0 */7 * *'` 为“每 7 天”规则，可能受月份天数影响并非精确 168 小时间隔，但能满足每周更新的需求。

## 📚 依赖

- 法定节假日: [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)
- 农历计算: [lunardate](https://pypi.org/project/lunardate/)
- ICS 生成: [icalendar](https://pypi.org/project/icalendar/)


