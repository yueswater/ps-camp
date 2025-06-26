import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# 載入 .env 檔案的 API 金鑰
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_latest_weather_summary(location="大安區"):
    dataid = "F-D0047-061"
    apikey = os.getenv("CWB_API_KEY")
    format = "JSON"
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{dataid}?Authorization={apikey}&format={format}"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # 取得指定地區的資料（如：松山區、大安區）
    locations = data["cwaopendata"]["Dataset"]["Locations"]["Location"]
    loc = next((l for l in locations if l["LocationName"] == location), None)
    if not loc:
        raise ValueError(f"{location} 資料不存在")

    # 抽出各項欄位
    def extract_element(name):
        return next(el for el in loc["WeatherElement"] if el["ElementName"] == name)

    temp_data = extract_element("溫度")["Time"]
    rain_data = extract_element("3小時降雨機率")["Time"]
    weather_data = extract_element("天氣現象")["Time"]

    # 組成時間對應的 records
    records = {}

    for t in temp_data:
        time = t["DataTime"]
        records[time] = {"時間": time, "溫度": t["ElementValue"]["Temperature"]}

    for r in rain_data:
        time = r["StartTime"]
        if time not in records:
            records[time] = {"時間": time}
        records[time]["降雨機率"] = r["ElementValue"]["ProbabilityOfPrecipitation"]

    for w in weather_data:
        time = w["StartTime"]
        if time not in records:
            records[time] = {"時間": time}
        weather = w["ElementValue"].get("Weather") or ""
        records[time]["天氣現象"] = weather

    # 依時間距離現在排序，找出最近時間點
    now = datetime.now(timezone.utc).astimezone()
    sorted_times = sorted(
        records.keys(), key=lambda t: abs(datetime.fromisoformat(t) - now)
    )

    # 逐筆搜尋最完整的資料（最少缺欄位），並回填 fallback
    for time in sorted_times:
        base = records[time]
        temp = base.get("溫度")
        rain = base.get("降雨機率")
        wx = base.get("天氣現象")

        if temp and rain and wx:
            return {
                "時間": time,
                "溫度": temp,
                "降雨機率": rain,
                "天氣現象": wx,
            }

        # 往前找 fallback
        for t2 in sorted_times:
            temp = temp or records[t2].get("溫度")
            rain = rain or records[t2].get("降雨機率")
            wx = wx or records[t2].get("天氣現象")
            if temp and rain and wx:
                return {
                    "時間": time,
                    "溫度": temp,
                    "降雨機率": rain,
                    "天氣現象": wx,
                }

    # 全部都缺資料的最壞情況（保底）
    return {
        "時間": now.isoformat(),
        "溫度": "",
        "降雨機率": "",
        "天氣現象": "",
    }
