class ExcelObservation(object):
    """
    Auxiliary class for modeling the observations information retrieved from the Excel structure file.
    """

    def __init__(self, country_name, indicator_code, _value):
        self._country_name = country_name
        self._indicator_code = indicator_code
        self._value = _value

    @property
    def country_name(self):
        return self._country_name

    @property
    def indicator_code(self):
        return self._indicator_code

    @property
    def value(self):
        return self._value
