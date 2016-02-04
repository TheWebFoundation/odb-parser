class ExcelObservation(object):
    """
    Auxiliary class for modeling the observations information retrieved from the Excel structure file.
    """

    def __init__(self, iso3=None, indicator_code=None, value=None, year=None, rank=None, rank_change=None, scaled=None):
        self._iso3 = iso3
        self._indicator_code = indicator_code
        self._value = value
        self._rank = rank
        self._year = year
        self._scaled = scaled
        self._rank_change = rank_change

    def __str__(self):
        return "%s - %s(%s): %s - %s scaled [%s]" % (
            self.iso3, self.indicator_code, self.year, self.value, self.scaled, self.rank)

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
    def rank_change(self):
        return self._rank_change

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, rank):
        self._rank = rank

    @property
    def year(self):
        return self._year

    @property
    def scaled(self):
        return self._scaled
