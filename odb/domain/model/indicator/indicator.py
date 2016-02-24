import uuid
from abc import ABCMeta

from odb.domain.model.entity import Entity
from odb.domain.model.events import DomainEvent
from odb.domain.model.events import publish
from utility.mutators import when, mutate


# =======================================================================================
# Indicator aggregate root entity
# =======================================================================================
class Indicator(Entity):
    """
    Indicator aggregate root entity

    Attributes:
        id (str): Id for the indicator
        index (str): Index to which this indicator belongs to
        indicator (str): Indicator name, this is used to reference from other indicators
        name (str): Indicator name, this is used as the long name so it could be longer and more complex than indicator
        parent (str): Indicator name of the parent, this must reference indicator attribute of the parent indicator
        provider_url (str): URL where data have been obtained
        description (str): Description of the indicator
        uri (str): URI that identifies this unique resource, normally composed depending on deployment address
        subindex (str): Indicator name of the subindex that this indicator belongs to
        component (str): Indicator name of the component that this indicator belongs to
        type (str): Type of the indicator, normally one of: Index, SubIndex, Component, Primary or Secondary
        children (list of Indicator): Children that have this indicator as its parent
        source_name (str): Name of the source where data have been obtained
        provider_name (str): Name of the provider where data have been obtained
        republish (bool): If republish of this indicator data are allowed or not
        is_percentage (bool): If the value is a percentage or not
        weight (float): The weight of the indicator
        tags (str): Tags for the indicator
    """

    class Created(Entity.Created):
        pass

    class Discarded(Entity.Discarded):
        pass

    class OrganizationAdded(DomainEvent):
        pass

    def __init__(self, event):
        """
        Constructor for Indicator, creation of new objects should be done by create_indicator factory function

        Note:
            New indicators should be created by create_indicator function

        Args:
            event: The event with the required attributes
        """
        super(Indicator, self).__init__(event.originator_id, event.originator_version)
        self._children = event.children
        self._component = event.component
        self._description = event.description
        self._format_notes = event.format_notes
        self._id = event.id
        self._index = event.index
        self._indicator = event.indicator
        self._license = event.license
        self._name = event.name
        self._parent = event.parent
        self._provider_name = event.provider_name
        self._provider_url = event.provider_url
        self._provider_url = event.provider_url
        self._range = event.range
        self._short_name = event.short_name
        self._source_data = event.source_data
        self._source_name = event.source_name
        self._source_url = event.source_url
        self._subindex = event.subindex
        self._tags = event.tags
        self._type = event.type
        self._units = event.units
        self._uri = event.uri
        self._weight = event.weight

    # TODO: This could be greatly simplified using reflection
    def to_dict(self):
        """
        Converts self object to dictionary

        Returns:
            dict: Dictionary representation of self object
        """
        return {
            'index': self.index, 'indicator': self.indicator, 'name': self.name, 'parent': self.parent,
            'provider_url': self.provider_url, 'description': self.description, 'uri': self.uri,
            'component': self.component, 'subindex': self.subindex, 'id': self.id, 'type': self.type,
            'children': [child.to_dict() for child in self.children], 'provider_name': self.provider_name,
            'short_name': self.short_name, 'source_name': self.source_name, 'source_url': self.source_url,
            'source_data': self.source_data, 'units': self.units, 'format_notes': self.format_notes,
            'license': self.license, 'range': self.range, 'tags': self.tags, 'weight': self.weight}

    # TODO: Enforce rules about naming here?

    # =======================================================================================
    # Properties
    # =======================================================================================
    @property
    def id(self):
        return self._id

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index
        self.increment_version()

    @property
    def indicator(self):
        return self._indicator

    @indicator.setter
    def indicator(self, indicator):
        self._indicator = indicator
        self.increment_version()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.increment_version()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        self.increment_version()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type):
        self._type = type
        self.increment_version()

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        self._children = children
        self.increment_version()

    @property
    def provider_url(self):
        return self._provider_url

    @provider_url.setter
    def provider_url(self, provider_url):
        self._provider_url = provider_url
        self.increment_version()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description
        self.increment_version()

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri
        self.increment_version()

    @property
    def subindex(self):
        return self._subindex

    @subindex.setter
    def subindex(self, subindex):
        self._subindex = subindex
        self.increment_version()

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, component):
        self._component = component
        self.increment_version()

    @property
    def provider_name(self):
        return self._provider_name

    @provider_name.setter
    def provider_name(self, provider_name):
        self._provider_name = provider_name
        self.increment_version()

    @property
    def source_name(self):
        return self._source_name

    @source_name.setter
    def source_name(self, source_name):
        self._source_name = source_name
        self.increment_version()

    @property
    def source_url(self):
        return self._source_url

    @source_url.setter
    def source_url(self, source_url):
        self._source_url = source_url
        self.increment_version()

    @property
    def short_name(self):
        return self._short_name

    @short_name.setter
    def short_name(self, short_name):
        self._short_name = short_name
        self.increment_version()

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        self._tags = tags
        self.increment_version()

    @property
    def source_data(self):
        return self._source_data

    @source_data.setter
    def source_data(self, source_data):
        self._source_data = source_data
        self.increment_version()

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units):
        self._units = units
        self.increment_version()

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, range):
        self._range = range
        self.increment_version()

    @property
    def format_notes(self):
        return self._format_notes

    @format_notes.setter
    def format_notes(self, format_notes):
        self._format_notes = format_notes
        self.increment_version()

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, license):
        self._license = license
        self.increment_version()

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, weight):
        self._weight = weight
        self.increment_version()

    # =======================================================================================
    # Commands
    # =======================================================================================
    def discard(self):
        """Discard this indicator.

        After a call to this method, the indicator can no longer be used.
        """
        self._check_not_discarded()
        event = Indicator.Discarded(originator_id=self.id,
                                    originator_version=self.version)

        self._apply(event)
        publish(event)

    def _apply(self, event):
        mutate(self, event)

    def add_organization(self, label=None):
        self._check_not_discarded()
        event = Indicator.OrganizationAdded(originator_id=self.id,
                                            originator_version=self.version,
                                            label=label)
        self._apply(event)
        publish(event)

    def add_child(self, indicator):
        # TODO: use event system
        self._children.append(indicator)
        self.increment_version()


# =======================================================================================
# Indicator aggregate root factory
# =======================================================================================
def create_indicator(id=None, index=None, indicator=None, name=None, component=None, source_name=None, source_url=None,
                     source_data=None, range=None, units=None, format_notes=None, license=None, short_name=None,
                     provider_url=None, description=None, uri=None, parent=None, provider_name=None, subindex=None,
                     type=None, tags=None, weight=None, children=None):
    """
    This function creates new indicators and acts as a factory

    Args:
        id (str, optional): Id for the indicator
        source_data (str, optional): Url for the concrete data source
        range (str, optional): Data range
        units (str, optional): Data Units
        format_notes (str, optional): Additional notes related to data format
        license (str, optional): License associated to the data
        source_url (str, optional): URL for the data source
        index (str, optional): Index to which this indicator belongs to
        indicator (str, optional): Indicator name, this is used to reference from other indicators
        name (str, optional): Indicator name, this is used as the long name so it could be longer and more complex than indicator
        component (str, optional):  Indicator name of the component that this indicator belongs to
        parent (str, optional): Indicator name of the parent, this must reference indicator attribute of the parent indicator
        provider_url (str, optional): URL where data have been obtained
        description (str, optional): Description of the indicator
        uri (str, optional): URI that identifies this unique resource, normally composed depending on deployment address
        subindex (str, optional): Indicator name of the subindex that this indicator belongs to
        type (str, optional): Type of the indicator, normally one of: Index, SubIndex, Component, Primary or Secondary
        weight(float, optional): The weight of the indicator
        children (list of Indicator, optional): Children that have this indicator as its parent
        source_name (str, optional): Name of the source where data have been obtained
        provider_name (str, optional): Name of the provider where data have been obtained
        tags (str, optional): Tags for the indicator

    Returns:
        Indicator: Created indicator
    """
    indicator_id = uuid.uuid4().hex[:24]
    children = [] if children is None else children
    event = Indicator.Created(originator_id=indicator_id, originator_version=0, id=id, index=index, indicator=indicator,
                              name=name, parent=parent, provider_url=provider_url, description=description, uri=uri,
                              provider_name=provider_name, subindex=subindex, source_data=source_data,
                              short_name=short_name, source_url=source_url, units=units, format_notes=format_notes,
                              range=range, license=license, component=component, source_name=source_name, type=type,
                              tags=tags, weight=weight, children=children)
    indicator = when(event)
    publish(event)
    return indicator


# =======================================================================================
# Mutators
# =======================================================================================
@when.register(Indicator.Created)
def _(event):
    """Create a new aggregate root"""
    indicator = Indicator(event)
    indicator.increment_version()
    return indicator


@when.register(Indicator.Discarded)
def _(event, indicator):
    indicator.validate_event_originator(event)
    indicator._discarded = True
    indicator.increment_version()
    return indicator


# =======================================================================================
# Indicator Repository
# =======================================================================================
class Repository(object, metaclass=ABCMeta):
    """Abstract implementation of generic queries for managing indicators."""

    def find_indicator_by_code(self, indicator_code, _type=None):
        pass

    def find_indicators_index(self):
        pass

    def find_indicators_sub_indexes(self):
        pass

    def find_indicators_components(self, parent=None):
        pass

    def find_indicators_primary(self, parent=None):
        pass

    def find_indicators_secondary(self, parent=None):
        pass

    def find_indicators_indicators(self, parent=None):
        pass

    def find_indicators_by_level(self, level, parent=None):
        pass

    def find_indicator_children(self, indicator):
        pass

    def insert_indicator(self, indicator):
        pass
