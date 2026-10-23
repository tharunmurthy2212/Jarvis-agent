from app.tools.datetime_tool import DateTimeTool


def test_get_current_datetime():
    data = DateTimeTool.get_current_datetime()
    assert "local_time" in data
    assert "local_date" in data
    assert "day_of_week" in data
    assert "unix_timestamp" in data
    assert data["unix_timestamp"] > 1700000000


def test_calculate_date_offset():
    res = DateTimeTool.calculate_date_offset(days=7, hours=2)
    assert "target_date" in res
    assert "target_day" in res
    assert res["offset_applied"] == "7 days, 2 hours, 0 minutes"
