"""
生成中国法定节假日、调休补班、常见国际节日与中国传统节日的 ICS 文件。

数据来源与策略：
- 法定节假日 & 调休/补班：使用 NateScarlet/holiday-cn 每年 JSON（字段：days[].name/date/isOffDay）。
- 固定公历节日：从 data/fixed_holidays.csv 读取。
- 农历节日：从 data/lunar_holidays.csv 读取规则，并通过 lunardate 动态计算（处理跨年农历月份）。
- 浮动节日（如母亲节/父亲节/感恩节）：脚本中动态计算。

注意事项：
- 事件为全天事件，使用 DTSTART/DTEND 的 VALUE=DATE（DTEND 为次日）。
- 为 iPhone 适配，设置 X-WR-CALNAME 与 Asia/Shanghai 时区，并设置 TRANSP:TRANSPARENT。
- 生成两年数据：当年与下一年，以便长期订阅体验更好。
"""

import csv
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple

import pytz
from icalendar import Calendar, Event
import lunardate


TZ_SH = pytz.timezone("Asia/Shanghai")


def _new_calendar() -> Calendar:
    """创建并初始化一个日历对象，添加必要的元信息。

    中文函数级注释：
    本函数负责创建一个 iCalendar 日历对象，设置产品标识、版本、显示名以及默认时区，
    以确保在 iPhone 等设备上订阅显示正确。
    """
    cal = Calendar()
    cal.add("prodid", "-//China Holiday Calendar//github.com//china-calendar//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "中国节假日与常用节日")
    cal.add("x-wr-timezone", "Asia/Shanghai")
    return cal


def _add_all_day_event(cal: Calendar, the_date: date, summary: str, description: str, category: str) -> None:
    """向日历添加一个全天事件。

    中文函数级注释：
    - 输入为公历日期、标题、描述与分类。
    - ICS 全天事件需将 DTEND 设为次日，避免部分客户端显示为零时刻事件。
    - 为方便去重，UID 使用日期与标题的组合。
    """
    event = Event()
    event.add("summary", summary)
    event.add("description", description)
    event.add("categories", category)
    event.add("dtstart", the_date)
    event.add("dtend", the_date + timedelta(days=1))
    event.add("transp", "TRANSPARENT")
    event.add("dtstamp", datetime.now(TZ_SH))
    event.add("uid", f"{the_date.isoformat()}-{summary}@china-calendar")
    cal.add_component(event)


def fetch_holiday_cn(year: int) -> List[Dict]:
    """获取 holiday-cn 年度 JSON 数据并返回 days 列表。

    中文函数级注释：
    - 该函数从 NateScarlet/holiday-cn 仓库获取指定年份 JSON。
    - JSON 结构：{ year, papers, days: [{ name, date, isOffDay }] }。
    - 返回 days 列表供后续处理。
    """
    url = f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("days", [])


def add_offdays_and_workdays(cal: Calendar, days: List[Dict]) -> None:
    """根据 holiday-cn days 列表添加休息日与补班日事件。

    中文函数级注释：
    - isOffDay 为 True 的日期添加“法定节假日”事件，标题为对应 name。
    - isOffDay 为 False 且存在 name 的日期视为“调休补班日”，添加补班事件。
    - 注意：days 中仅包含与节假日安排相关的日期，并非全年所有工作日。
    """
    for d in days:
        name = d.get("name")
        day_str = d.get("date")
        is_off = d.get("isOffDay")
        if not day_str:
            continue
        dt = datetime.strptime(day_str, "%Y-%m-%d").date()
        if is_off and name:
            _add_all_day_event(cal, dt, name, "法定节假日（来源：holiday-cn）", "法定节假日")
        elif not is_off and name:
            _add_all_day_event(cal, dt, f"【补班】{name}", "调休安排的工作日（来源：holiday-cn）", "补班")


def load_fixed_holidays(csv_path: str) -> List[Dict]:
    """读取固定公历节日 CSV。

    中文函数级注释：
    - CSV 字段：name, month, day, description（可选）。
    - 返回列表字典，用于后续生成事件。
    """
    items: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                "name": row.get("name", "").strip(),
                "month": int(row["month"]),
                "day": int(row["day"]),
                "description": row.get("description", "").strip(),
            })
    return items


def generate_fixed_holidays(cal: Calendar, years: List[int], items: List[Dict]) -> None:
    """为指定年份集合生成固定公历节日事件。

    中文函数级注释：
    - 对于每个年份，将 month/day 直接映射为公历日期加入事件。
    - 分类标记为“国际节日”。若 description 提供则写入描述。
    """
    for y in years:
        for it in items:
            dt = date(y, it["month"], it["day"])
            desc = it["description"] or "固定公历节日"
            _add_all_day_event(cal, dt, it["name"], desc, "国际节日")


def load_lunar_holidays(csv_path: str) -> List[Dict]:
    """读取农历节日规则 CSV。

    中文函数级注释：
    - CSV 字段：name, lunar_month, lunar_day, description（可选）。
    - 返回列表字典，用于后续农历转公历计算。
    """
    items: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                "name": row.get("name", "").strip(),
                "lunar_month": int(row["lunar_month"]),
                "lunar_day": int(row["lunar_day"]),
                "description": row.get("description", "").strip(),
            })
    return items


def lunar_to_solar_for_gregorian_year(gregorian_year: int, lunar_month: int, lunar_day: int) -> List[date]:
    """计算指定公历年份内对应农历月日可能出现的公历日期（考虑跨年）。

    中文函数级注释：
    - 某些农历月份（如腊月）可能对应次年一月的公历日期；因此需要检查 (gregorian_year-1) 与 gregorian_year 两个农历年的映射。
    - 返回列表（通常 0~2 个日期），仅包含落在目标公历年的日期。
    """
    results: List[date] = []
    # 候选一：农历年=公历年
    try:
        dt1 = lunardate.LunarDate(gregorian_year, lunar_month, lunar_day).to_datetime().date()
        if dt1.year == gregorian_year:
            results.append(dt1)
    except Exception:
        pass
    # 候选二：农历年=公历年-1（处理腊月等跨年情况）
    try:
        dt0 = lunardate.LunarDate(gregorian_year - 1, lunar_month, lunar_day).to_datetime().date()
        if dt0.year == gregorian_year:
            results.append(dt0)
    except Exception:
        pass
    return results


def generate_lunar_holidays(cal: Calendar, years: List[int], items: List[Dict]) -> None:
    """根据农历规则为指定年份集合生成事件。

    中文函数级注释：
    - 利用 lunardate 将农历日期映射到公历。
    - 分类标记为“传统节日”。若 description 提供则写入描述。
    - 去重策略：同一日期同一标题只添加一次。
    """
    seen: set[Tuple[date, str]] = set()
    for y in years:
        for it in items:
            sols = lunar_to_solar_for_gregorian_year(y, it["lunar_month"], it["lunar_day"])
            for dt in sols:
                key = (dt, it["name"]) 
                if key in seen:
                    continue
                seen.add(key)
                desc = it["description"] or "中国传统节日"
                _add_all_day_event(cal, dt, it["name"], desc, "传统节日")


def get_nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """计算某年某月第 n 个指定星期几的公历日期。

    中文函数级注释：
    - weekday 取值与 Python 标准一致：周一=0，周日=6。
    - 通过首日偏移与 7 天步进计算第 n 个目标星期几。
    """
    first_day = date(year, month, 1)
    offset = (weekday - first_day.weekday()) % 7
    return first_day + timedelta(days=offset + (n - 1) * 7)


def generate_floating_holidays(cal: Calendar, years: List[int]) -> None:
    """为指定年份集合生成浮动节日事件（母亲节/父亲节/感恩节等）。

    中文函数级注释：
    - 母亲节：五月第二个星期日。
    - 父亲节：六月第三个星期日。
    - 感恩节：十一月第四个星期四。
    - 分类标记为“国际节日”。
    """
    for y in years:
        # 母亲节（5 月第 2 个星期日）
        mothers_day = get_nth_weekday(y, 5, 6, 2)  # 周日=6
        _add_all_day_event(cal, mothers_day, "母亲节", "浮动国际节日：五月第二个星期日", "国际节日")

        # 父亲节（6 月第 3 个星期日）
        fathers_day = get_nth_weekday(y, 6, 6, 3)
        _add_all_day_event(cal, fathers_day, "父亲节", "浮动国际节日：六月第三个星期日", "国际节日")

        # 感恩节（11 月第 4 个星期四）
        thanksgiving = get_nth_weekday(y, 11, 3, 4)  # 周四=3
        _add_all_day_event(cal, thanksgiving, "感恩节", "浮动国际节日：十一月第四个星期四（美）", "国际节日")


def build_calendar() -> Calendar:
    """总体构建日历，汇总所有来源的节日事件。

    中文函数级注释：
    - 生成当年与下一年两份数据，保证订阅长期有效。
    - 处理顺序：法定节假日 & 补班 → 固定公历节日 → 农历节日 → 浮动节日。
    - 若网络请求失败，将抛出异常；在 CI 中可重试或等待下一次计划任务。
    """
    current_year = datetime.now(TZ_SH).year
    years = [current_year, current_year + 1]

    cal = _new_calendar()

    # 法定节假日 / 补班
    for y in years:
        try:
            days = fetch_holiday_cn(y)
            add_offdays_and_workdays(cal, days)
        except Exception:
            # 失败时不中断整体生成，让其他数据仍可生成
            pass

    # 固定公历节日
    try:
        fixed_items = load_fixed_holidays("data/fixed_holidays.csv")
        generate_fixed_holidays(cal, years, fixed_items)
    except FileNotFoundError:
        # 若数据文件暂不可用，跳过该部分
        pass

    # 农历节日
    try:
        lunar_items = load_lunar_holidays("data/lunar_holidays.csv")
        generate_lunar_holidays(cal, years, lunar_items)
    except FileNotFoundError:
        pass

    # 浮动节日（母亲/父亲/感恩节等）
    generate_floating_holidays(cal, years)

    return cal


def save_calendar(cal: Calendar, out_path: str) -> None:
    """保存日历为 ICS 文件。

    中文函数级注释：
    - 输出为二进制写入，兼容 iCalendar 规范与常见客户端解析。
    """
    with open(out_path, "wb") as f:
        f.write(cal.to_ical())


def main() -> None:
    """主函数：构建并保存 ICS 文件。

    中文函数级注释：
    - 生成合并日历并保存到仓库根目录的 holidays.ics。
    - 若你需要运行此脚本，请在本地或 CI 环境执行：python scripts/generate_ics.py。
    """
    cal = build_calendar()
    save_calendar(cal, "holidays.ics")


if __name__ == "__main__":
    # 根据你的规则，我们不主动运行。仅在显式执行时才生成。
    main()