import uuid

from odb.domain.model.area.area import Area
from odb.domain.model.area.region import Region
from odb.domain.model.entity import Entity
from odb.domain.model.events import publish
from utility.mutators import mutate, when


class Country(Area):
    """
    Country entity

    Attributes:
        income (str): Income level, e.g.: LIC(Low income), LMC(Lower middle income), OEC(High income, OECD)
        type (str): Type of development for the country e.g.: Developing, Emerging
    """

    class Created(Entity.Created):
        pass

    class Discarded(Entity.Discarded):
        pass

    def __init__(self, event):
        """
        Constructor for Country

        Note:
            New countries should be created by create_country factory function

        Args:
            event: Event with the required attributes
        """
        super(Country, self).__init__(event)
        self._income = event.income
        self._hdi_rank = event.hdi_rank
        self._g20 = event.g20
        self._g7 = event.g7
        self._iodch = event.iodch
        self._oecd = event.oecd

    # FIXME: Bad repr
    # def __repr__(self):
    #     return "{d}Country(id={id!r}, region_id={c._region.id!r}, " \
    #            "iso2_code={c._iso2_code}, iso3_code={c._iso3_code}, label={c._label!r})". \
    #         format(d="Discarded" if self.discarded else "", id=self._id, c=self,
    #                type=self._type)

    def to_dict(self):
        """
        Converts self object to dictionary

        Returns:
            dict: Dictionary representation of self object
        """
        dictionary = super(Country, self).to_dict()
        dictionary['income'] = self.income
        dictionary['oecd'] = self.oecd
        dictionary['hdi_rank'] = self.hdi_rank
        dictionary['g20'] = self.g20
        dictionary['g7'] = self.g7
        dictionary['iodch'] = self.iodch
        return dictionary

    def to_dict_without_info(self):
        dictionary = super(Country, self).to_dict_without_info()
        dictionary['income'] = self.income
        dictionary['oecd'] = self.oecd
        dictionary['hdi_rank'] = self.hdi_rank
        dictionary['g20'] = self.g20
        dictionary['g7'] = self.g7
        dictionary['iodch'] = self.iodch
        return dictionary

    # =======================================================================================
    # Properties
    # =======================================================================================
    @property
    def income(self):
        return self._income

    @income.setter
    def income(self, income):
        self._income = income
        self.increment_version()

    @property
    def oecd(self):
        return self._oecd

    @oecd.setter
    def oecd(self, oecd):
        self._oecd = oecd
        self.increment_version()

    @property
    def hdi_rank(self):
        return self._hdi_rank

    @hdi_rank.setter
    def hdi_rank(self, hdi_rank):
        self._hdi_rank = hdi_rank
        self.increment_version()

    @property
    def g20(self):
        return self._g20

    @g20.setter
    def g20(self, g20):
        self._g20 = g20
        self.increment_version()

    @property
    def g7(self):
        return self._g7

    @g7.setter
    def g7(self, g7):
        self._g7 = g7
        self.increment_version()

    @property
    def iodch(self):
        return self._iodch

    @iodch.setter
    def iodch(self, iodch):
        self._iodch = iodch
        self.increment_version()

    # =======================================================================================
    # Commands
    # =======================================================================================
    def discard(self):
        """Discard this region.

        After a call to this method, the region can no longer be used.
        """
        self._check_not_discarded()
        event = Region.Discarded(originator_id=self.id, originator_version=self.version)

        self._apply(event)
        publish(event)

    def _apply(self, event):
        mutate(self, event)


# =======================================================================================
# Region aggregate root factory
# =======================================================================================
def create_country(name=None, short_name=None, area=None, income=None, uri=None, iso3=None, iso2=None, id=None,
                   search=None, hdi_rank=None, g20=None, g7=None, iodch=None, oecd=None, info=None):
    """
    This function creates new countries and acts as a factory

    Args:
        name (str, optional): Name for the country
        short_name (str, optional): Short name for the country, could be the same as name
        area (str, optional): Area where this country belongs to, e.g.: Europe for Spain
        income (str, optional): Income level, e.g.: LIC(Low income), LMC(Lower middle income), OEC(High income, OECD)
        uri (str, optional): URI that identifies this unique resource, normally composed depending on deployment address
        iso3 (str, optional): ISO 3166-1 alpha-3 code for the country
        iso2 (str, optional): ISO 3166-1 alpha-2 code for the country
        iso_num (str, optional): ISO 3166-1 number code for the country
        id (optional): Id code for the country
        type (str, optional): Type of development for the country e.g.: Developing, Emerging
        search (str, optional): Search names separated by ';' with the name of the country in various languages
        info (list of AreaInfo): List of area info for this area

    Returns:
        Country: Created country
    """
    country_id = uuid.uuid4().hex[:24]
    if not info: info = []
    event = Country.Created(originator_id=country_id, originator_version=0, name=name, short_name=short_name, area=area,
                            income=income, uri=uri, iso3=iso3, iso2=iso2, id=id, search=search,
                            g20=g20, g7=g7, hdi_rank=hdi_rank, oecd=oecd, iodch=iodch, info=info)
    country = when(event)
    publish(event)
    return country


# =======================================================================================
# Mutators
# =======================================================================================
@when.register(Country.Created)
def _(event):
    """Create a new aggregate root"""
    country = Country(event)
    country.increment_version()
    return country


@when.register(Country.Discarded)
def _(event, country):
    country.validate_event_originator(event)
    country._discarded = True
    country.increment_version()
    return country
