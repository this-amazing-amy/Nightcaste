class Calendar(object):
    pass


class ExaltedCalendar(Calendar):
    """Calculates specific fields of a Exalted calendar.

        Args:
            time (long): The time in seconds passed since 1. Ascending Air 0.
    """
    # usefil second constants
    S_MINUTE = 60
    S_HOUR = 60 * S_MINUTE
    S_DAY = 24 * S_HOUR
    S_YEAR = 425 * S_DAY

    # Months
    ASCENDING_AIR = 1
    RESPLENDENT_AIR = 2
    DESCENDING_AIR = 3
    ASCENDING_WATER = 4
    RESPLENDENT_WATER = 5
    DESCENDING_WATER = 6
    ASCENDING_EARTH = 7
    RESPLENDENT_EARTH = 8
    DESCENDING_EARTH = 9
    ASCENDING_WOOD = 10
    RESPLENDENT_WOOD = 11
    DESCENDING_WOOD = 12
    ASCENDING_FIRE = 13
    RESPLENDENT_FIRE = 14
    DESCENDING_FIRE = 15
    CALIBRATION = 16

    # Week Days
    MONDAY = 1
    TUESDAY = 2
    WENDSDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    # display_names
    month_names = {
        ASCENDING_AIR: 'Ascending Air',
        RESPLENDENT_AIR: 'Resplendent Air',
        DESCENDING_AIR: 'Descending Air',
        ASCENDING_WATER: 'Ascending Water',
        RESPLENDENT_WATER: 'Resplendent Water',
        DESCENDING_WATER: 'Descending Water',
        ASCENDING_EARTH: 'Ascending Earth',
        RESPLENDENT_EARTH: 'Resplendent Earth',
        DESCENDING_EARTH: 'Descending Earth',
        ASCENDING_WOOD: 'Ascending Wood',
        RESPLENDENT_WOOD: 'Resplendent Wood',
        DESCENDING_WOOD: 'Descending Wood',
        ASCENDING_FIRE: 'Ascending Fire',
        RESPLENDENT_FIRE: 'Resplendent Fire',
        DESCENDING_FIRE: 'Descending Fire',
        CALIBRATION: 'Calibration'
    }

    def __init__(self, time=0):
        self.time = time

    def get_year(self):
        return self.time // self.S_YEAR

    def get_day_of_year(self):
        return ((self.time // self.S_DAY) % 425) + 1

    def get_month_of_year(self):
        return (((self.time // self.S_DAY) % 425) // 28) + 1

    def get_day_of_month(self):
        return (((self.time // self.S_DAY) % 425) % 28) + 1

    def get_hour(self):
        return (self.time // self.S_HOUR) % 24

    def get_minute(self):
        return (self.time // self.S_MINUTE) % 60

    def get_second(self):
        return self.time % 60

    def display(self):
        # TODO implement user defined formatting
        return '%02d:%02d h, %d. %s %d' % (
            self.get_hour(),
            self.get_minute(),
            self.get_day_of_month(),
            self.month_names[self.get_month_of_year()],
            self.get_year())

    def __str__(self):
        return self.display()
