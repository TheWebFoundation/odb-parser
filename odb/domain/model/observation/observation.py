import uuid
from abc import ABCMeta

from infrastructure.errors.exceptions import DiscardedEntityError
from odb.domain.model.entity import Entity
from odb.domain.model.events import DomainEvent, publish
from utility.mutators import mutate, when


# =======================================================================================
# Observation aggregate root entity
# =======================================================================================
class Observation(Entity):
    """
    Observation aggregate root entity

    Attributes:
        provider_url (str): URL of the provider
        indicator (str): Indicator indicator attribute value
        indicator_name (str): Indicator name for this observation
        indicator_type (str): Indicator type for this observation
        short_name (str): Short name of the area
        area (str): Area area attribute value
        area_name (str): Name of the area
        uri (str): URI for this observation
        value (float or string): Value for this observation, could be blank if there is no valid value
        year (str): Year for this observation
        provider_name (str): Name of the observation provider
        id (str): Id for this observations
        continent (str): Continent for the area
        tendency (int): Tendency regarding previous years, -1 decreasing, 0 equal, +1 increasing
        republish (bool): True if republish is allowed, otherwise False
        area_type (str): Area type, i.g.: EMERGING or DEVELOPING
        ranking (int): Ranking for this observation
        ranking_type (int): Ranking type for this observation
    """

    class Created(Entity.Created):
        pass

    class Discarded(Entity.Discarded):
        pass

    class ComputationAdded(DomainEvent):
        pass

    class ReferencedArea(DomainEvent):
        pass

    class ReferencedIndicator(DomainEvent):
        pass

    def __init__(self, event):
        """
        Constructor for Observation, creation of new objects should be done by create_observation factory function

        Note:
            New observations should be created by create_observation function

        Args:
            event: The event with the required attributes
        """
        super(Observation, self).__init__(event.originator_id, event.originator_version)
        self._indicator = event.indicator
        self._area = event.area
        self._uri = event.uri
        self._value = event.value
        self._year = event.year
        self._id = event.id
        self._rank = event.rank
        self._rank_change = event.rank_change

    def to_dict(self):
        """
        Converts self object to dictionary

        Returns:
            dict: Dictionary representation of self object
        """
        # There could be data without an indicator associated
        indicator_dict = self.indicator.to_dict() if self.indicator else None
        return {'indicator': indicator_dict, 'area': self.area.to_dict(), 'value': self.value, 'year': self.year,
                'id': self.id, 'rank': self.rank, 'rank_change': self.rank_change, 'uri': self.uri}

    # =======================================================================================
    # Properties
    # =======================================================================================
    @property
    def indicator(self):
        return self._indicator

    @indicator.setter
    def indicator(self, indicator):
        self._indicator = indicator
        self.increment_version()

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, area):
        self._area = area
        self.increment_version()

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri
        self.increment_version()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.increment_version()

    @property
    def rank_change(self):
        return self._rank_change

    @rank_change.setter
    def rank_change(self, rank_change):
        self._rank_change = rank_change
        self.increment_version()

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, year):
        self._year = year
        self.increment_version()

    @property
    def id(self):
        return self._id

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, rank):
        self._rank = rank
        self.increment_version()

    # =======================================================================================
    # Commands
    # =======================================================================================
    def discard(self):
        """Discard this observation.

        After a call to this method, the observation can no longer be used.
        """
        self._check_not_discarded()
        event = Observation.Discarded(originator_id=self.id,
                                      originator_version=self.version)

        self._apply(event)
        publish(event)

    def reference_indicator(self, indicator):
        """Reference an indicator from this observation.

        Args:
            indicator: The Indicator to be referenced from this observation.

        Raises:
            DiscardedEntityError: If this observation or the indicator has been discarded.
            """
        self._check_not_discarded()

        if indicator.discarded:
            raise DiscardedEntityError("Cannot reference {!r}".format(indicator))

        event = Observation.ReferencedIndicator(originator_id=self.id,
                                                originator_version=self.version,
                                                indicator_id=indicator.id)
        self._apply(event)
        publish(event)

    def reference_area(self, area):
        """Reference an area from this observation.

        Args:
            area: The area (Region or Country) to be referenced from this observation.

        Raises:
            DiscardedEntityError: If this observation or the area has been discarded.
            """

        self._check_not_discarded()
        if area.discarded:
            raise DiscardedEntityError("Cannot reference {!r}".format(area))

        event = Observation.ReferencedArea(originator_id=self.id,
                                           originator_version=self.version,
                                           area_id=area.id)
        self._apply(event)
        publish(event)

    def _apply(self, event):
        mutate(self, event)


# =======================================================================================
# Observation aggregate root factory
# =======================================================================================
def create_observation(indicator=None, area=None, value=None, year=1970, id=None, rank=None, rank_change=None,
                       uri=None):
    """
    This function creates new observations and acts as a factory

    Args:
        provider_url (str, optional): URL of the provider
        indicator (str, optional): Indicator indicator attribute value
        indicator_name (str, optional): Indicator name for this observation
        indicator_type (str): Indicator type for this observation
        short_name (str, optional): Short name of the area
        area (str, optional): Area area attribute value
        area_name (str, optional): Name of the area
        uri (str, optional): URI for this observation
        value (float or string, optional): Value for this observation, could be blank if there is no valid value
        year (str, optional): Year for this observation
        provider_name (str, optional): Name of the observation provider
        id (str, optional): Id for this observations
        continent (str, optional): Continent for the area
        tendency (int, optional): Tendency regarding previous years, -1 decreasing, 0 equal, +1 increasing
        republish (bool, optional): True if republish is allowed, otherwise False
        area_type (str, optional): Area type, i.g.: EMERGING or DEVELOPING
        ranking (int, optional): Ranking for this observation
        ranking_type (int, optional): Ranking type for this observation

    Returns:
        Observation: Created observation
    """
    obs_id = uuid.uuid4().hex[:24]
    event = Observation.Created(originator_id=obs_id, originator_version=0, indicator=indicator, area=area, value=value,
                                year=year, id=id, rank=rank, rank_change=rank_change, uri=uri)
    obs = when(event)
    publish(event)
    return obs


# =======================================================================================
# Mutators
# =======================================================================================
@when.register(Observation.Created)
def _(event):
    """Create a new aggregate root"""
    obs = Observation(event)
    obs.increment_version()
    return obs


@when.register(Observation.Discarded)
def _(event, obs):
    obs.validate_event_originator(event)
    obs._discarded = True
    obs.increment_version()
    return obs


@when.register(Observation.ReferencedIndicator)
def _(event, obs):
    obs.validate_event_originator(event)
    obs._ref_indicator_id = event.indicator_id
    obs.increment_version()
    return obs


@when.register(Observation.ReferencedArea)
def _(event, obs):
    obs.validate_event_originator(event)
    obs._ref_area_id = event.area_id
    obs.increment_version()
    return obs


# =======================================================================================
# Observations Repository
# =======================================================================================
class Repository(object, metaclass=ABCMeta):
    """Abstract implementation of generic queries for managing observations."""

    def find_observations(self, indicator_code=None, area_code=None, year=None):
        pass

    def get_indicators_by_code(self, code):
        pass

    def get_countries_by_code_name_or_income(self, code):
        pass

    # def get_years(self, year):
    #     pass

    def observation_uri(self, observation):
        pass

    def set_observation_country_and_indicator_name(self, observation):
        pass

    def insert_observation(self, observation):
        pass
