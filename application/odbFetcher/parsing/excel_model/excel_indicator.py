class ExcelIndicator(object):
    """
    Auxiliary class for modeling the indicators information retrieved from the Excel structure file. Each field
    corresponds with the columns in the file.
    """

    def __init__(self, index=None, code=None, name=None, _type=None, subindex=None, component=None,
                 description=None, source_name=None, provider_name=None, tags=None, weight=None, _range=None,
                 source_url=None, provider_url=None, units=None, format_notes=None, _license=None, source_data=None):
        self._code = code
        self._component = component
        self._description = description
        self._format_notes = format_notes
        self._index = index
        self._license = _license
        self._name = name
        self._provider_name = provider_name
        self._provider_url = provider_url
        self._range = _range
        self._source_data = source_data
        self._source_name = source_name
        self._source_url = source_url
        self._subindex = subindex
        self._tags = tags
        self._type = _type
        self._units = units
        self._weight = weight

    def is_index(self):
        return self._type == "INDEX"

    @property
    def code(self):
        return self._code

    @property
    def index(self):
        return self._index

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
    def subindex(self):
        return self._subindex

    @property
    def component(self):
        return self._component

    @property
    def source_name(self):
        return self._source_name

    @property
    def source_data(self):
        return self._source_data

    @property
    def source_url(self):
        return self._source_url

    @property
    def provider_name(self):
        return self._provider_name

    @property
    def provider_url(self):
        return self._provider_url

    @property
    def units(self):
        return self._units

    @property
    def range(self):
        return self._range

    @property
    def format_notes(self):
        return self._format_notes

    @property
    def license(self):
        return self._license

    @property
    def tags(self):
        return self._tags

    @property
    def weight(self):
        return self._weight
