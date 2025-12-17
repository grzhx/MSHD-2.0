"""Temporary in-memory dictionaries for codes and names."""

# Source codes: category -> sub-code -> name
SOURCE_DICT = {
    "1": {
        "00": "前方地震应急指挥部",
        "01": "后方地震应急指挥部",
        "20": "应急指挥技术系统",
        "21": "社会服务工程应急救援系统",
        "40": "危险区预评估工作组",
        "41": "地震应急指挥技术协调组",
        "42": "震后政府信息支持工作项目组",
        "80": "灾情快速上报接收处理系统",
        "81": "地方地震局应急信息服务相关技术系统",
        "99": "其他",
    },
    "2": {
        "00": "互联网感知",
        "01": "通信网感知",
        "02": "舆情网感知",
        "03": "电力系统感知",
        "04": "交通系统感知",
        "05": "其他",
    },
    "3": {
        "00": "其他数据",
    },
}

CARRIER_DICT = {
    "0": "文字",
    "1": "图像",
    "2": "音频",
    "3": "视频",
    "4": "其他",
}

# Disaster categories and subcategories
DISASTER_CATEGORY_DICT = {
    "2": {
        "01": "死亡",
        "02": "受伤",
        "03": "失踪",
    },
    "3": {
        "01": "土木",
        "02": "砖木",
        "03": "砖混",
        "04": "框架",
        "05": "其他",
    },
    "4": {
        "01": "交通",
        "02": "供水",
        "03": "输油",
        "04": "燃气",
        "05": "电力",
        "06": "通信",
        "07": "水利",
    },
    "5": {
        "01": "崩塌",
        "02": "滑坡",
        "03": "泥石流",
        "04": "岩溶塌陷",
        "05": "海啸",
        "06": "台风",
        "07": "地震",
        "08": "其他",
    },
}

# Indicators per disaster domain
HOUSE_DAMAGE_INDICATORS = {
    "001": "一般损坏面积",
    "002": "严重损坏面积",
    "003": "受灾程度",
}

LIFELINE_INDICATORS = {
    "001": "受灾设施数",
    "002": "受灾范围",
    "003": "受灾程度",
}

SECONDARY_INDICATORS = {
    "001": "灾害损失",
    "002": "灾害范围",
    "003": "受灾程度",
}

DISASTER_INDICATOR_DICT = {
    "1": {
        "01": {
            "001": "地理位置",
            "002": "时间",
            "003": "震级",
            "004": "震源深度",
            "005": "烈度",
        }
    },
    "2": {
        "01": {"001": "受灾人数", "002": "受灾程度"},
        "02": {"001": "受灾人数", "002": "受灾程度"},
        "03": {"001": "受灾人数", "002": "受灾程度"},
    },
    "3": {
        "01": HOUSE_DAMAGE_INDICATORS,
        "02": HOUSE_DAMAGE_INDICATORS,
        "03": HOUSE_DAMAGE_INDICATORS,
        "04": HOUSE_DAMAGE_INDICATORS,
        "05": HOUSE_DAMAGE_INDICATORS,
    },
    "4": {
        "01": LIFELINE_INDICATORS,
        "02": LIFELINE_INDICATORS,
        "03": LIFELINE_INDICATORS,
        "04": LIFELINE_INDICATORS,
        "05": LIFELINE_INDICATORS,
        "06": LIFELINE_INDICATORS,
        "07": LIFELINE_INDICATORS,
    },
    "5": {
        "01": SECONDARY_INDICATORS,
        "02": SECONDARY_INDICATORS,
        "03": SECONDARY_INDICATORS,
        "04": SECONDARY_INDICATORS,
        "05": SECONDARY_INDICATORS,
        "06": SECONDARY_INDICATORS,
        "07": SECONDARY_INDICATORS,
    },
}


def get_source_name(code: str) -> str:
    if len(code) != 3 or not code.isdigit():
        raise ValueError("source code must be 3 digits")
    cat, sub = code[0], code[1:]
    return SOURCE_DICT.get(cat, {}).get(sub)


def get_carrier_name(code: str) -> str:
    return CARRIER_DICT.get(code)


def get_disaster_names(category: str, sub_category: str, indicator: str) -> dict:
    cat_name = DISASTER_CATEGORY_DICT.get(category, {}).get(sub_category)
    indicator_name = DISASTER_INDICATOR_DICT.get(category, {}).get(sub_category, {}).get(indicator)
    return {
        "category": cat_name,
        "sub_category": cat_name,  # sub_category shares the name with category mapping
        "indicator": indicator_name,
    }


def validate_source(code: str) -> None:
    if get_source_name(code) is None:
        raise ValueError(f"unknown source code: {code}")


def validate_carrier(code: str) -> None:
    if get_carrier_name(code) is None:
        raise ValueError(f"unknown carrier code: {code}")


def validate_disaster(category: str, sub_category: str, indicator: str) -> None:
    names = get_disaster_names(category, sub_category, indicator)
    if names["category"] is None or names["indicator"] is None:
        raise ValueError(
            f"unknown disaster code combination: {category}{sub_category}{indicator}"
        )


def list_domain(domain: str):
    if domain == "source":
        return SOURCE_DICT
    if domain == "carrier":
        return CARRIER_DICT
    if domain == "disaster":
        return DISASTER_CATEGORY_DICT
    if domain == "indicator":
        return DISASTER_INDICATOR_DICT
    raise ValueError("unknown domain")
