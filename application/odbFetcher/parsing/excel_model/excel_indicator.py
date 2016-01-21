__author__ = 'Rodrigo'


class ExcelIndicator(object):
    """
    Auxiliary class for modeling the indicators information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, index_code, code, name, _type, subindex_code, component_code, description, source_name,
                 provider_name, tags, weight):
        self._code = code
        self._name = name
        self._type = _type
        self._index_code = index_code
        self._component_code = component_code
        self._subindex_code = subindex_code
        self._description = description
        self._source_name = source_name
        self._provider_name = provider_name
        self._tags = tags
        self._weight = weight

    @property
    def code(self):
        return self._code

    @property
    def index_code(self):
        return self._index_code

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def description(self):
        return self._description

    @property
    def subindex_code(self):
        return self._subindex_code

    @property
    def component_code(self):
        return self._component_code

    @property
    def source_name(self):
        return self._source_name

    @property
    def provider_name(self):
        return self._provider_name

    @property
    def tags(self):
        return self._tags

    @property
    def weight(self):
        return self._weight
