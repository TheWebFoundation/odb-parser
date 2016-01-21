__author__ = 'Rodrigo'


class ExcelIndicator(object):
    """
    Auxiliary class for modeling the indicators information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, code, name, _type, subindex_code, provider_name, provider_url, republishable, is_percentage,
                 scale):
        self._code = code
        self._name = name
        self._type = _type
        self._subindex_code = subindex_code
        self._provider_name = provider_name
        self._provider_url = provider_url
        self._republishable = republishable
        self._is_percentage = is_percentage
        self._scale = scale

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def subindex_code(self):
        return self._subindex_code

    @property
    def provider_name(self):
        return self._provider_name

    @property
    def provider_url(self):
        return self._provider_url

    @property
    def republishable(self):
        return self._republishable

    @property
    def is_percentage(self):
        return self._is_percentage

    @property
    def scale(self):
        return self._scale
