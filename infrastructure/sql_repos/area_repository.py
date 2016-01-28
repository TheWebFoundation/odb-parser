import sqlite3

from infrastructure.errors.errors import AreaRepositoryError
from infrastructure.sql_repos.utils import create_insert_query
from infrastructure.utils import uri
from odb.domain.model.area import area
from odb.domain.model.area.area_info import AreaInfo
from odb.domain.model.area.area_short_info import AreaShortInfo
from odb.domain.model.area.country import create_country
from odb.domain.model.area.indicator_info import IndicatorInfo, IndicatorInfoList
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
        db = sqlite3.connect(self._config.get("CONNECTION", "SQLITE_DB"))
        db.row_factory = sqlite3.Row
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS area')
            sql = '''
                CREATE TABLE area
                (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    area TEXT,
                    iso2 TEXT,
                    iso3 TEXT,
                    short_name TEXT,
                    iso_num INTEGER
                );
                '''
            db.execute(sql)
            db.commit()
        return db

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

        query = "SELECT * FROM area WHERE name=:name"
        area_name = area_name or ''
        r = self._db.execute(query, {'name': area_name}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with name " + area_name)

        data = dict(r)
        return AreaRowAdapter().dict_to_area(data)

    # def find_countries_by_code_or_income(self, area_code_or_income):
    #     """
    #     Finds countries by code or income if no area is found it will search by income
    #
    #     Args:
    #         area_code_or_income (str): iso3, iso2, name or income(for a list of countries)
    #
    #     Returns:
    #         Region with the given countries appended or a list of countries
    #
    #     Raises:
    #         AreaRepositoryError: If not countries nor areas are found
    #
    #     """
    #     area_code_or_income_upper = area_code_or_income.upper()
    #     area = self._db['areas'].find_one({"$or": [
    #         {"iso3": area_code_or_income},
    #         {"iso3": area_code_or_income_upper},
    #         {"iso2": area_code_or_income},
    #         {"iso2": area_code_or_income_upper},
    #         {"name": area_code_or_income}]})
    #
    #     if area is None:
    #         # Find if code is an income code
    #         # FIXME: This is not working, order by is needed on method call
    #         countries = self.find_countries_by_continent_or_income_or_type(area_code_or_income_upper)
    #         if countries is None:
    #             raise AreaRepositoryError("No countries for code " + area_code_or_income)
    #         else:
    #             return countries
    #
    #     self.set_continent_countries(area)
    #     self.area_uri(area)
    #     area["short_name"] = area["name"]
    #
    #     return AreaDocumentAdapter().transform_to_area(area)

    # def find_countries_by_continent_or_income_or_type(self, continent_or_income_or_type, order="iso3"):
    #     """
    #     Finds a list of countries by its continent, income or type
    #
    #     Args:
    #         continent_or_income_or_type (str): Code for continent, income or type
    #         order (str, optional): Attribute key to sort, default to iso3
    #
    #     Returns:
    #         list of Country: countries with the given continent, income or type
    #
    #     Raises:
    #         AreaRepositoryCountry: If no countries are found
    #     """
    #     order = "name" if order is None else order
    #     continent_or_income_or_type_upper = continent_or_income_or_type.upper()
    #     continent_or_income_or_type_title = continent_or_income_or_type.title()  # Nowadays, this is the way it
    #     # is stored
    #     countries = self._db['areas'].find({"$or": [
    #         {"area": continent_or_income_or_type},
    #         {"income": continent_or_income_or_type_upper},
    #         {"type": continent_or_income_or_type_title}]}, ).sort(order, 1)
    #
    #     if countries.count() == 0:
    #         raise AreaRepositoryError("No countries for code " + continent_or_income_or_type)
    #
    #     country_list = []
    #
    #     for country in countries:
    #         self.set_continent_countries(country)
    #         self.area_uri(country)
    #         country_list.append(country)
    #
    #     return CountryDocumentAdapter().transform_to_country_list(country_list)

    def insert_region(self, region):
        data = RegionRowAdapter().region_to_dict(region)
        query = create_insert_query('area', data)
        self._db.execute(query, data)
        self._db.commit()

    def insert_country(self, country):
        data = CountryRowAdapter().country_to_dict(country)
        query = create_insert_query('area', data)
        self._db.execute(query, data)
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
        query = "SELECT * FROM area WHERE iso3 LIKE :iso3 ORDER BY name ASC"
        rows = self._db.execute(query, {'iso3': iso3}).fetchall()

        country_list = []

        for country in [dict(r) for r in rows]:
            # FIXME: review
            # self.area_uri(country)
            country_list.append(country)

        if country_list.count() > 0:
            region["countries"] = country_list

    def area_uri(self, area):
        """
        Sets the URI to the given area

        Args:
            area (Area): Area to set the URI
        """
        field = "iso3" if area["iso3"] is not None else "name"
        uri(url_root=self._url_root, element=area, element_code=field,
            level="areas")

    def enrich_country(self, iso3, indicator_list):
        """
        Enriches country data with indicator info

        Note:
            The input indicator_list must contain the following attributes: indicator_code, year, value,
            provider_name and provider_value
        Args:
            iso3 (str): Iso3 of the country for which data is going to be appended.
            indicator_list (list of Indicator): Indicator list with the attributes in the note.
        """
        info_dict = {}
        for indicator in indicator_list:
            info_dict[indicator.indicator_code] = {
                "year": indicator.year,
                "value": indicator.value,
                "provider": {
                    "name": indicator.provider_name,
                    "url": indicator.provider_url
                }
            }

        self._db["areas"].update({"iso3": iso3}, {"$set": {"info": info_dict}})

    def get_areas_info(self):
        all_countries = self.find_countries(None)
        indicator_codes = set([info.indicator_code for country in all_countries for info in country.info])
        indicators_info_list = IndicatorInfoList()
        for indicator_code in indicator_codes:
            areas = []
            provider_name, provider_url = ('', '')
            for area in all_countries:
                for info_of_area in area.info:
                    if info_of_area.indicator_code == indicator_code:
                        areas.append(AreaShortInfo(area.iso3, info_of_area.value, info_of_area.year))
                        provider_name, provider_url = (info_of_area.provider_name, info_of_area.provider_url)
            indicator_info = IndicatorInfo(indicator_code, provider_name, provider_url)
            indicator_info.values = areas
            indicators_info_list.add_indicator_info(indicator_info)
        return indicators_info_list


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
        # FIXME: Check if is needed to parse countries or area info
        return create_region(**region_dict)

    @staticmethod
    def region_to_dict(region):
        # FIXME: Review fields
        data = dict((key, value) for key, value in region.to_dict().items() if
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
        data = dict((key, value) for key, value in country.to_dict().items() if
                    key not in ('countries', 'info', 'search', 'uri', 'iso_num', 'type', 'income'))
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


class AreaInfoDocumentAdapter(object):
    """
    Adapter class to transform area info from PyMongo format to Domain area info objects
    """

    def transform_to_area_info_list(self, area_info_document_dict):
        """
        Transforms a dict with area infos

        Args:
            area_info_document_dict (dict): Area info document dict in PyMongo format

        Returns:
            A list of area infos
        """
        return [AreaInfo(indicator_code=area_info_key,
                         provider_name=area_info_document_dict[area_info_key]['provider']['name'],
                         provider_url=area_info_document_dict[area_info_key]['provider']['url'],
                         value=area_info_document_dict[area_info_key]['value'],
                         year=area_info_document_dict[area_info_key]['year'])
                for area_info_key in area_info_document_dict.keys()]
