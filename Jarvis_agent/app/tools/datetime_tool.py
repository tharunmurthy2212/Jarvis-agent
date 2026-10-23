from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import zoneinfo


class DateTimeTool:
    """Provides verified real-time clock telemetry and date arithmetic from the local host."""

    @staticmethod
    def get_current_datetime(tz_name: Optional[str] = None) -> Dict[str, Any]:
        """Get live system time, date, day of week, and ISO format."""
        try:
            if tz_name:
                tz = zoneinfo.ZoneInfo(tz_name)
                now = datetime.now(tz)
            else:
                # System local time
                now = datetime.now().astimezone()

            utc_now = datetime.now(timezone.utc)

            return {
                "local_time": now.strftime("%I:%M:%S %p"),
                "local_date": now.strftime("%A, %d %B %Y"),
                "iso": now.isoformat(),
                "day_of_week": now.strftime("%A"),
                "timezone": str(now.tzinfo),
                "utc_iso": utc_now.isoformat(),
                "unix_timestamp": int(now.timestamp()),
            }
        except Exception as e:
            return {"error": f"Failed to get datetime: {str(e)}"}

    @staticmethod
    def calculate_date_offset(
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        base_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate target date by adding or subtracting time offset."""
        try:
            if base_iso:
                base = datetime.fromisoformat(base_iso)
            else:
                base = datetime.now().astimezone()

            delta = timedelta(days=days, hours=hours, minutes=minutes)
            target = base + delta

            return {
                "base_date": base.strftime("%Y-%m-%d %H:%M:%S"),
                "target_date": target.strftime("%Y-%m-%d %H:%M:%S"),
                "target_day": target.strftime("%A"),
                "target_iso": target.isoformat(),
                "offset_applied": f"{days} days, {hours} hours, {minutes} minutes"
            }
        except Exception as e:
            return {"error": f"Date calculation error: {str(e)}"}
