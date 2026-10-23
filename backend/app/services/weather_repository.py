"""Weather forecast lookup via SQLAlchemy bound parameters."""
from sqlalchemy import text
from app.core.database import get_session

# Native Oracle FETCH FIRST preserves the original forecast selection semantics.
_WEATHER_QUERY = text("""
    SELECT FORECAST_AT, TEMPERATURE_C, WIND_SPEED_MS,
           PTY_RAW, PCP_RAW, PTY_STATUS, PCP_STATUS
    FROM DRONE_APP.WEATHER_NATIONAL_FORECAST_V2
    WHERE NX = :nx AND NY = :ny
      AND FORECAST_AT >= CURRENT_TIMESTAMP
    ORDER BY FORECAST_AT ASC
    FETCH FIRST 1 ROW ONLY
""")


def get_weather(nx, ny):
    with get_session() as session:
        row = session.execute(_WEATHER_QUERY, {"nx": nx, "ny": ny}).first()
        if row is None:
            return None
        return {
            "forecast_at": row[0],
            "temperature": row[1],
            "wind_speed": row[2],
            "pty_raw": row[3],
            "pcp_raw": row[4],
            "pty_status": row[5],
            "pcp_status": row[6],
        }
