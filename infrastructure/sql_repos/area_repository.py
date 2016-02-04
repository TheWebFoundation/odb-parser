from infrastructure.errors.errors import AreaRepositoryError
from infrastructure.sql_repos.utils import create_insert_query, get_db
from odb.domain.model.area import area
from odb.domain.model.area.country import create_country
from odb.domain.model.area.region import create_region


class AreaRepository(area.Repository):
    """
    Concrete sqlite repository for Areas.
    """

    def __init__(self, recreate_db, log, config):
        """
        Constructor for AreaRepository

        Args:
        """
        self._config = config
        self._log = log
        self._db = self._initialize_db(recreate_db)

    def _initialize_db(self, recreate_db):
        db = get_db(self._config)
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS area')
            sql = '''
                CREATE TABLE area
                (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    area TEXT,
                    iso2 TEXT COLLATE NOCASE,
                    iso3 TEXT COLLATE NOCASE,
                    short_name TEXT,
                    iso_num INTEGER,
                    income TEXT,
                    hdi_rank INTEGER,
                    g20 BOOLEAN,
                    g7 BOOLEAN,
                    iodch BOOLEAN,
                    oecd BOOLEAN
                );
                '''
            db.execute(sql)
            db.execute("CREATE INDEX area_iso3_iso2_index ON area(iso3  COLLATE NOCASE,iso2 COLLATE NOCASE)")
            db.commit()
        return db

    def begin_transaction(self):
        self._db.execute("BEGIN TRANSACTION")

    def commit_transaction(self):
        self._db.commit()

    def find_by_name(self, area_name):
        """
        Finds one area by its name

        Args:
            area_name (str): Name of the area to query, case insensitive

        Returns:
            Area: The first area with the given name

        Raises:
            AreaRepositoryError: If there is not an area with the given name
        """

        query = "SELECT * FROM area WHERE name LIKE :name"
        area_name = area_name or ''
        r = self._db.execute(query, {'name': area_name}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with name " + area_name)

        data = dict(r)
        return AreaRowAdapter().dict_to_area(data)

    def find_by_code(self, area_code):
        query = "SELECT * FROM area WHERE (iso3 LIKE :code OR iso2 LIKE :code)"
        area_code = area_code or ''
        r = self._db.execute(query, {'code': area_code}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with code " + area_code)

        data = dict(r)
        return AreaRowAdapter().dict_to_area(data)

    def find_by_iso3(self, iso3_code):
        query = "SELECT * FROM area WHERE (iso3 LIKE :iso3_code)"
        iso3_code = iso3_code or ''
        r = self._db.execute(query, {'iso3_code': iso3_code}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with code %s" % (iso3_code,))

        data = dict(r)
        return AreaRowAdapter().dict_to_area(data)

    # FIXME: Review this method signature
    def find_countries_by_code_or_income(self, area_code_or_income):
        """
        Finds countries by code or income if no area is found it will search by income

        Args:
            area_code_or_income (str): iso3, iso2, name or income(for a list of countries)

        Returns:
            Region with the given countries appended or a list of countries

        Raises:
            AreaRepositoryError: If not countries nor areas are found

        """

        query = "SELECT * FROM area WHERE (iso3 LIKE :iso3 OR iso2 LIKE :iso2 OR name LIKE :name)"
        r = self._db.execute(query, dict.fromkeys(['iso2', 'iso3', 'name'], area_code_or_income)).fetchone()

        if r is None:
            # FIXME: Review (old comment was: This is not working, order by is needed on method call)
            countries = self.find_countries_by_region_or_income(area_code_or_income)
            if not countries:
                raise AreaRepositoryError("No countries for code %s" % (area_code_or_income,))
            else:
                return countries

        area = dict(r)
        self.set_region_countries(area)
        self.area_uri(area)

        return AreaRowAdapter().dict_to_area(area)

    def find_countries_by_region_or_income(self, region_or_income, order="iso3"):
        """
        Finds a list of countries by its region, income or type

        Args:
            region_or_income (str): Code for region or income
            order (str, optional): Attribute key to sort, default to iso3

        Returns:
            list of Country: countries with the given region or income

        Raises:
            AreaRepositoryCountry: If no countries are found
        """
        order = "name" if order is None else order
        query = "SELECT * FROM area WHERE (area LIKE :area OR income LIKE :income) ORDER BY :order ASC"
        params = dict.fromkeys(['area', 'income'], region_or_income)
        params['order'] = order
        rows = self._db.execute(query, params).fetchall()

        if not rows:
            raise AreaRepositoryError("No countries for code %s" % (region_or_income,))

        country_list = []

        for country in [dict(r) for r in rows]:
            self.set_region_countries(country)
            self.area_uri(country)
            country_list.append(country)

        return CountryRowAdapter().transform_to_country_list(country_list)

    def insert_region(self, region, commit=True):
        data = RegionRowAdapter().region_to_dict(region)
        query = create_insert_query('area', data)
        self._db.execute(query, data)
        if commit:
            self._db.commit()

    def insert_country(self, country, commit=True):
        data = CountryRowAdapter().country_to_dict(country)
        query = create_insert_query('area', data)
        self._db.execute(query, data)
        if commit:
            self._db.commit()

    def find_areas(self, order):
        """
        Finds all areas in the repository

        Args:
            order (str): Attribute of Area to sort by

        Returns:
            list of Area: All regions and countries
        """
        order = "name" if order is None else order
        regions = self.find_regions(order)
        countries = self.find_countries(order)

        return regions + countries

    def find_regions(self, order):
        """
        Finds all regions in the repository

        Args:
            order (str): Attribute of Region to sort by

        Returns:
            list of Region: All regions
        """
        order = "name" if order is None else order
        query = "SELECT * FROM area WHERE area IS NULL ORDER BY :order ASC"
        rows = self._db.execute(query, {'order': order}).fetchall()

        regions = []

        for region in [dict(r) for r in rows]:
            self.set_region_countries(region)

            # FIXME: Review
            # self.area_uri(continent)
            regions.append(region)

        return RegionRowAdapter().transform_to_region_list(regions)

    def find_countries(self, order):
        """
        Finds all countries in the repository

        Args:
            order (str): Attribute of Country to sort by

        Returns:
            list of Country: All countries
        """
        order = "name" if order is None else order
        query = "SELECT * FROM area WHERE area IS NOT NULL ORDER BY :order ASC"
        rows = self._db.execute(query, {'order': order}).fetchall()

        country_list = []

        for country in [dict(r) for r in rows]:
            # FIXME: review
            # self.area_uri(country)
            country_list.append(country)

        return CountryRowAdapter().transform_to_country_list(country_list)

    def set_region_countries(self, region):
        """
        Sets the countries that belong to a region

        Args:
            region (dict): dict with region row data

        Returns:

        """
        iso3 = region["iso3"]
        query = "SELECT * FROM area WHERE area LIKE :iso3 ORDER BY name ASC"
        rows = self._db.execute(query, {'iso3': iso3}).fetchall()

        country_list = []

        for country in [dict(r) for r in rows]:
            # FIXME: review
            self.area_uri(country)
            country_list.append(country)

        if country_list:
            region["countries"] = country_list


# def area_uri(self, area):
#     """
#     Sets the URI to the given area
#
#     Args:
#         area (Area): Area to set the URI
#     """
#     field = "iso3" if area["iso3"] is not None else "name"
#     uri(url_root=self._url_root, element=area, element_code=field,
#         level="areas")

# def enrich_country(self, iso3, indicator_list):
#     """
#     Enriches country data with indicator info
#
#     Note:
#         The input indicator_list must contain the following attributes: indicator_code, year, value,
#         provider_name and provider_value
#     Args:
#         iso3 (str): Iso3 of the country for which data is going to be appended.
#         indicator_list (list of Indicator): Indicator list with the attributes in the note.
#     """
#     info_dict = {}
#     for indicator in indicator_list:
#         info_dict[indicator.indicator_code] = {
#             "year": indicator.year,
#             "value": indicator.value,
#             "provider": {
#                 "name": indicator.provider_name,
#                 "url": indicator.provider_url
#             }
#         }
#
#     self._db["areas"].update({"iso3": iso3}, {"$set": {"info": info_dict}})

# def get_areas_info(self):
#     all_countries = self.find_countries(None)
#     indicator_codes = set([info.indicator_code for country in all_countries for info in country.info])
#     indicators_info_list = IndicatorInfoList()
#     for indicator_code in indicator_codes:
#         areas = []
#         provider_name, provider_url = ('', '')
#         for area in all_countries:
#             for info_of_area in area.info:
#                 if info_of_area.indicator_code == indicator_code:
#                     areas.append(AreaShortInfo(area.iso3, info_of_area.value, info_of_area.year))
#                     provider_name, provider_url = (info_of_area.provider_name, info_of_area.provider_url)
#         indicator_info = IndicatorInfo(indicator_code, provider_name, provider_url)
#         indicator_info.values = areas
#         indicators_info_list.add_indicator_info(indicator_info)
#     return indicators_info_list


class AreaRowAdapter(object):
    """
    Adapter class to transform areas between SQLite objects and Domain objects
    """

    @staticmethod
    def dict_to_area(area_dict):
        """
        Transforms one single area

        Args:
            area_dict (dict): Area document coming from sqlite

        Returns:
            A region or country object, depending on the type
        """
        if area_dict['area'] is None:
            return RegionRowAdapter().dict_to_region(area_dict)
        else:
            return CountryRowAdapter().dict_to_country(area_dict)

    @staticmethod
    def transform_to_area_list(area_dict_list):
        return [AreaRowAdapter.dict_to_area(area_dict) for area_dict in area_dict_list]


class RegionRowAdapter(object):
    @staticmethod
    def dict_to_region(region_dict):
        """

        Args:
            region_dict: dict representing a row

        Returns:

        """
        # FIXME: Check if is needed to parse countries or area info
        # TODO: we could avoid the need to be explicit with the fields if we just used **kwargs in create_region to swallow all the unwanted fields
        data = dict((key, value) for key, value in list(region_dict.items()) if
                    key in ['name', 'short_name', 'area', 'iso3', 'iso2', 'iso_num', 'id', 'search', 'info', 'uri'])
        data['countries'] = CountryRowAdapter.transform_to_country_list(region_dict['countries'])
        return create_region(**data)

    @staticmethod
    def region_to_dict(region):
        # FIXME: Review fields
        data = dict((key, value) for key, value in list(region.to_dict().items()) if
                    key not in ('countries', 'info', 'search', 'uri', 'iso_num'))
        return data

    @staticmethod
    def transform_to_region_list(region_dict_list):
        """
        Transforms a list of regions

        Args:
            region_dict_list (list): Region dict list

        Returns:
            list of Region: A list of regions with the data in region_dict_list
        """
        return [RegionRowAdapter.dict_to_region(region_dict) for region_dict in region_dict_list]


class CountryRowAdapter(object):
    @staticmethod
    def dict_to_country(country_dict):
        # FIXME: Check if is needed to parse area info
        return create_country(**country_dict)

    @staticmethod
    def country_to_dict(country):
        data = dict((key, value) for key, value in list(country.to_dict().items()) if
                    key not in ('countries', 'info', 'search', 'uri', 'iso_num'))
        return data

    @staticmethod
    def transform_to_country_list(country_dict_list):
        """
        Transforms a list of countries

        Args:
            country_dict_list (list): Country dict list

        Returns:
            list of Country: A list of countries with the data in country_dict_list
        """
        return [CountryRowAdapter.dict_to_country(country_dict) for country_dict in country_dict_list]


# class AreaInfoDocumentAdapter(object):
#     """
#     Adapter class to transform area info from PyMongo format to Domain area info objects
#     """
#
#     def transform_to_area_info_list(self, area_info_document_dict):
#         """
#         Transforms a dict with area infos
#
#         Args:
#             area_info_document_dict (dict): Area info document dict in PyMongo format
#
#         Returns:
#             A list of area infos
#         """
#         return [AreaInfo(indicator_code=area_info_key,
#                          provider_name=area_info_document_dict[area_info_key]['provider']['name'],
#                          provider_url=area_info_document_dict[area_info_key]['provider']['url'],
#                          value=area_info_document_dict[area_info_key]['value'],
#                          year=area_info_document_dict[area_info_key]['year'])
#                 for area_info_key in area_info_document_dict.keys()]

if __name__ == "__main__":
    import logging
    import configparser
    import json

    logger = logging.getLogger(__name__)
    config = configparser.RawConfigParser()
    config.add_section('CONNECTION')
    config.set('CONNECTION', 'SQLITE_DB', '../../odb2015.db')

    repo = AreaRepository(False, logger, config)

    high_income_countries = repo.find_countries_by_code_or_income('High income')
    assert len(high_income_countries) > 0 and all(
        [country.income.lower() == 'high income' for country in high_income_countries])
    print(json.dumps([i.to_dict() for i in high_income_countries]))

    europe = repo.find_countries_by_code_or_income(':EU')
    assert europe is not None and len(europe.countries) > 0 and all(
        [country.area == ':EU' for country in europe.countries])
    print(json.dumps(europe.to_dict()))

    spain = repo.find_countries_by_code_or_income('es')
    assert spain is not None and spain.iso3 == 'ESP'
    print(json.dumps(spain.to_dict()))

    regions = repo.find_regions('name')
    assert len(regions) > 0
    print(json.dumps([region.to_dict() for region in regions]))

    france = repo.find_by_code('fr')
    assert france is not None and france.iso2 == 'FR'
    print(json.dumps(france.to_dict()))

    print('OK!')
