class ExcelObservation(object):
    """
    Auxiliary class for modeling the observations information retrieved from the Excel structure file.
    """

    def __init__(self, iso3=None, indicator_code=None, value=None, year=None, ranking=None):
        self._iso3 = iso3
        self._indicator_code = indicator_code
        self._value = value
        self._ranking = ranking
        self._year = year

    def __str__(self):
        return "%s - %s(%s): %s [%s]" % (self.iso3, self.indicator_code, self.year, self.value, self.ranking)

    @property
    def iso3(self):
        return self._iso3

    @property
    def indicator_code(self):
        return self._indicator_code

    @property
    def value(self):
        return self._value

    @property
    def ranking(self):
        return self._ranking

    @ranking.setter
    def ranking(self, ranking):
        self._ranking = ranking

    @property
    def year(self):
        return self._year
