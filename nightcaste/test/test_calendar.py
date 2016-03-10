from nightcaste.calendar import ExaltedCalendar


class TestExaltedCalendar:

    def test_get_year(self):
        cal = ExaltedCalendar()
        assert cal.get_year() == 0
        cal.time = ExaltedCalendar.S_YEAR
        assert cal.get_year() == 1
        cal.time = ExaltedCalendar.S_YEAR + ExaltedCalendar.S_YEAR // 2
        assert cal.get_year() == 1
        # last month is only 5 days, adding should result in a year change
        cal.time = 15 * 28 * ExaltedCalendar.S_DAY + 5 * ExaltedCalendar.S_DAY
        assert cal.get_year() == 1
        cal.time = 42 * ExaltedCalendar.S_YEAR
        assert cal.get_year() == 42

    def test_get_day_of_year(self):
        cal = ExaltedCalendar()
        assert cal.get_day_of_year() == 1
        cal.time = ExaltedCalendar.S_DAY
        assert cal.get_day_of_year() == 2
        cal.time = ExaltedCalendar.S_DAY + ExaltedCalendar.S_DAY // 2
        assert cal.get_day_of_year() == 2
        cal.time = ExaltedCalendar.S_YEAR
        assert cal.get_day_of_year() == 1
        cal.time = 15 * 28 * ExaltedCalendar.S_DAY + 5 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_year() == 1
        cal.time = ExaltedCalendar.S_YEAR + 41 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_year() == 42

    def test_get_month_of_year(self):
        cal = ExaltedCalendar()
        assert cal.get_month_of_year() == 1
        cal.time = 27 * ExaltedCalendar.S_DAY
        assert cal.get_month_of_year() == 1
        cal.time = 28 * ExaltedCalendar.S_DAY
        assert cal.get_month_of_year() == 2
        cal.time = ExaltedCalendar.S_YEAR
        assert cal.get_month_of_year() == 1
        cal.time = 15 * 28 * ExaltedCalendar.S_DAY
        assert cal.get_month_of_year() == 16
        cal.time = 15 * 28 * ExaltedCalendar.S_DAY + 5 * ExaltedCalendar.S_DAY
        assert cal.get_month_of_year() == 1

    def test_get_day_of_month(self):
        cal = ExaltedCalendar()
        assert cal.get_day_of_month() == 1
        cal.time = ExaltedCalendar.S_DAY
        assert cal.get_day_of_month() == 2
        cal.time = 27 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_month() == 28
        cal.time = 28 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_month() == 1
        cal.time = 28 * ExaltedCalendar.S_DAY + 27 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_month() == 28
        cal.time = 15 * 28 * ExaltedCalendar.S_DAY + 5 * ExaltedCalendar.S_DAY
        assert cal.get_day_of_month() == 1

    def test_get_hour(self):
        cal = ExaltedCalendar()
        assert cal.get_hour() == 0
        cal.time = ExaltedCalendar.S_DAY
        assert cal.get_hour() == 0
        cal.time = ExaltedCalendar.S_HOUR
        assert cal.get_hour() == 1
        cal.time = 23 * ExaltedCalendar.S_HOUR
        assert cal.get_hour() == 23
        cal.time = 24 * ExaltedCalendar.S_HOUR
        assert cal.get_hour() == 0
        cal.time = 9999 * ExaltedCalendar.S_DAY + 23 * ExaltedCalendar.S_HOUR
        assert cal.get_hour() == 23

    def test_get_minute(self):
        cal = ExaltedCalendar()
        assert cal.get_minute() == 0
        cal.time = ExaltedCalendar.S_HOUR
        assert cal.get_minute() == 0
        cal.time = ExaltedCalendar.S_MINUTE
        assert cal.get_minute() == 1
        cal.time = 59 * ExaltedCalendar.S_MINUTE
        assert cal.get_minute() == 59
        cal.time = 60 * ExaltedCalendar.S_MINUTE
        assert cal.get_minute() == 0
        cal.time = 9999 * ExaltedCalendar.S_HOUR + 59 * ExaltedCalendar.S_MINUTE
        assert cal.get_minute() == 59

    def test_get_second(self):
        cal = ExaltedCalendar()
        assert cal.get_second() == 0
        cal.time = ExaltedCalendar.S_MINUTE
        assert cal.get_second() == 0
        cal.time = 1
        assert cal.get_second() == 1
        cal.time = 59
        assert cal.get_second() == 59
        cal.time = 9999 * ExaltedCalendar.S_MINUTE + 42
        assert cal.get_second() == 42

    def test_display(self):
        cal = ExaltedCalendar()
        assert cal.display() == "00:00 h, 1. Ascending Air 0"
        cal.time = 90274556 * ExaltedCalendar.S_MINUTE
        assert cal.display() == "15:56 h, 20. Resplendent Earth 147"
