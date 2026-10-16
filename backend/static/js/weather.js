
function formatWeatherValue(value, unit = "") {
    if (value === null || value === undefined) {
        return "자료 없음";
    }

    if (typeof value === "number") {
        return `${value}${unit}`;
    }

    return String(value);
}


function formatForecastTime(value) {
    if (!value || value.length !== 12) {
        return "자료 없음";
    }

    return (
        `${value.slice(0, 4)}-` +
        `${value.slice(4, 6)}-` +
        `${value.slice(6, 8)} ` +
        `${value.slice(8, 10)}:` +
        `${value.slice(10, 12)}`
    );
}


function createWeatherInfo(weather, risk = null) {
    const box = document.createElement("div");
    box.className = "weather-info";

    const title = document.createElement("h4");

    title.textContent = risk
        ? `기상 위험도: ${risk.label}`
        : "기상정보";

    box.appendChild(title);

    const rows = [
        ["기온", formatWeatherValue(
            weather.temperature, "℃"
        )],
        ["풍속", formatWeatherValue(
            weather.wind_speed, "m/s"
        )],
        ["풍향", formatWeatherValue(
            weather.wind_direction, "°"
        )],
        ["강수량", formatWeatherValue(
            weather.precipitation, "mm"
        )],
        ["강수확률", formatWeatherValue(
            weather.precipitation_probability, "%"
        )],
        ["적설량", formatWeatherValue(
            weather.snowfall, "cm"
        )],
    ];

    if (risk && risk.reasons.length > 0) {
        rows.push([
            "위험 요인",
            risk.reasons.join(", "),
        ]);
    }

    rows.push(
        [
            "관측 기준",
            weather.observation_time || "-",
        ],
        [
            "강수확률 예보",
            formatForecastTime(
                weather.forecast_time
            ),
        ],
        [
            "적설 예보",
            formatForecastTime(
                weather.snowfall_forecast_time
            ),
        ]
    );

    rows.forEach(([label, value]) => {
        const row = document.createElement("div");
        row.className = "weather-row";
        row.textContent = `${label}: ${value}`;
        box.appendChild(row);
    });

    const note = document.createElement("div");
    note.className = "weather-note";
    note.textContent =
        "관측과 예보의 기준 시각이 다를 수 있습니다.";

    box.appendChild(note);

    return box;
}


async function fetchWeatherAt(lat, lon) {
    const params = new URLSearchParams({
        lat: lat,
        lon: lon,
    });

    const response = await fetch(
        `/api/weather?${params}`
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "기상정보 조회 실패"
        );
    }

    return data;
}
