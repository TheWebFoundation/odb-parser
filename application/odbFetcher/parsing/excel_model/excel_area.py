class ExcelArea(object):
    """
    Auxiliary class for modeling the area information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, iso2, iso3, name, region):
        self._iso2 = iso2
        self._iso3 = iso3
        self._name = name
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

    def __str__(self):
        return "%s-%s %s %s" % (self.iso2, self.iso3, self.name, self.region)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)
