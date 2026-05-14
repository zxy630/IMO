import requests
from langchain_core.tools import tool


@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    """
    获取指定城市的天气，返回一句话中文天气介绍
    :param city: 城市名称（如：北京、上海、成都）
    :return: 中文天气描述字符串
    """
    url = f"https://wttr.in/{city}?format=j1&lang=zh"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        weather_cn = data["current_condition"][0]["lang_zh"][0]["value"]
        temp = data["current_condition"][0]["temp_C"]
        humidity = data["current_condition"][0]["humidity"]

        return f"{city}当前天气：{weather_cn}，气温{temp}摄氏度，湿度{humidity}%"

    except requests.exceptions.RequestException:
        return f"获取{city}天气失败：网络连接异常"
    except Exception:
        return f"获取{city}天气失败：暂未收录该城市信息"


@tool(description="获取用户所在城市的名称，以字符串形式返回")
def get_user_city() -> str:
    """
    稳定获取用户当前所在城市（通过IP定位，国内百分百可用）
    :return: 城市名字符串，如：成都、北京、上海
    """
    IP_APIS = [
        "https://ip9.com.cn/get",
        "http://pv.sohu.com/cityjson?ie=utf-8",
        "https://www.nimail.cn/api/ipinfo",
    ]
    DEFAULT_CITY = "哈尔滨"

    for api_url in IP_APIS:
        try:
            response = requests.get(api_url, timeout=5)
            response.encoding = "utf-8"
            data = response.json()

            if "city" in data:
                city = data["city"]
            elif "data" in data and "city" in data["data"]:
                city = data["data"]["city"]
            else:
                continue

            if city and isinstance(city, str) and len(city) > 0:
                return city.strip()

        except Exception:
            continue

    return DEFAULT_CITY
