class ExcelAreaInfo(object):
    """
    Auxiliary class for modeling the area information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, iso3, indicator_code, value, year):
        self._iso3 = iso3
        self._indicator_code = indicator_code
        self._value = value
        self._year = year

    @property
    def indicator_code(self):
        return self._indicator_code

    @property
    def iso3(self):
        return self._iso3

    @property
    def value(self):
        return self._value

    @property
    def year(self):
        return self._year
