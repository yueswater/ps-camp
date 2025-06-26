from datetime import datetime, timezone

import requests


def get_latest_weather_summary(location="大安區"):
    dataid = "F-D0047-061"
    format = "JSON"
    url = f"https://ps-camp.sungpinyue.workers.dev/fileapi/v1/opendataapi/{dataid}?format={format}"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    locations = data["cwaopendata"]["Dataset"]["Locations"]["Location"]
    loc = next((l for l in locations if l["LocationName"] == location), None)
    if not loc:
        raise ValueError(f"{location} 資料不存在")

    def extract_element(name):
        return next(el for el in loc["WeatherElement"] if el["ElementName"] == name)

    temp_data = extract_element("溫度")["Time"]
    rain_data = extract_element("3小時降雨機率")["Time"]
    weather_data = extract_element("天氣現象")["Time"]

    records = {}

    for t in temp_data:
        time = t["DataTime"]
        records[time] = {"時間": time, "溫度": t["ElementValue"]["Temperature"]}

    for r in rain_data:
        time = r["StartTime"]
        records.setdefault(time, {"時間": time})["降雨機率"] = r["ElementValue"][
            "ProbabilityOfPrecipitation"
        ]

    for w in weather_data:
        time = w["StartTime"]
        records.setdefault(time, {"時間": time})["天氣現象"] = w["ElementValue"].get(
            "Weather", ""
        )

    now = datetime.now(timezone.utc).astimezone()
    sorted_times = sorted(
        records.keys(), key=lambda t: abs(datetime.fromisoformat(t) - now)
    )

    for time in sorted_times:
        base = records[time]
        temp = base.get("溫度")
        rain = base.get("降雨機率")
        wx = base.get("天氣現象")

        if temp and rain and wx:
            return {"時間": time, "溫度": temp, "降雨機率": rain, "天氣現象": wx}

        for t2 in sorted_times:
            temp = temp or records[t2].get("溫度")
            rain = rain or records[t2].get("降雨機率")
            wx = wx or records[t2].get("天氣現象")
            if temp and rain and wx:
                return {"時間": time, "溫度": temp, "降雨機率": rain, "天氣現象": wx}

    return {"時間": now.isoformat(), "溫度": "", "降雨機率": "", "天氣現象": ""}
