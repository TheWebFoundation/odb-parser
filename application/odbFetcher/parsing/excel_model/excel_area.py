class ExcelArea(object):
    """
    Auxiliary class for modeling the area information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, iso2, iso3, name, region, income=None, hdi_rank=None, g20=None, g7=None, iodch=None, oecd=None):
        self._g20 = g20
        self._g7 = g7
        self._hdi_rank = hdi_rank
        self._income = income
        self._iodch = iodch
        self._iso2 = iso2
        self._iso3 = iso3
        self._name = name
        self._oecd = oecd
        self._region = region

    @property
    def iso2(self):
        return self._iso2

    @property
    def iso3(self):
        return self._iso3

    @property
    def name(self):
        return self._name

    @property
    def region(self):
        return self._region

    @property
    def g20(self):
        return self._g20

    @property
    def g7(self):
        return self._g7

    @property
    def hdi_rank(self):
        return self._hdi_rank

    @property
    def income(self):
        return self._income

    @property
    def iodch(self):
        return self._iodch

    @property
    def oecd(self):
        return self._oecd

    def __str__(self):
        return "%s-%s %s %s" % (self.iso2, self.iso3, self.name, self.region)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)
