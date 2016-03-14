class ExcelDatasetObservation(object):
    """
    Auxiliary class for modeling the dataset observation retrieved from the Excel datasets sheet. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, indicator_code, dataset_indicator_code, year, iso3, value):
        self._iso3 = iso3
        self._indicator_code = indicator_code
        self._dataset_indicator_code = dataset_indicator_code
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

    @property
    def dataset_indicator_code(self):
        return self._dataset_indicator_code
