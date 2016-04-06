from functools import lru_cache

from infrastructure.errors.errors import AreaRepositoryError
from infrastructure.sql_repos.utils import create_insert_query, get_db, create_replace_query
from odb.domain.model.area.area import Repository, Area
from odb.domain.model.area.area_info import AreaInfo
from odb.domain.model.area.area_short_info import AreaShortInfo
from odb.domain.model.area.country import create_country
from odb.domain.model.area.indicator_info import IndicatorInfoList, IndicatorInfo
from odb.domain.model.area.region import create_region


class AreaRepository(Repository):
    """
    Concrete sqlite repository for Areas.
    """

    def __init__(self, recreate_db, config):
        """
        Constructor for AreaRepository

        Args:
        """
        self._config = config
        self._db = self._initialize_db(recreate_db)

    def _initialize_db(self, recreate_db):
        db = get_db(self._config)
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS area')
            sql = """
                CREATE TABLE area
                (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    area TEXT,
                    iso2 TEXT COLLATE NOCASE,
                    iso3 TEXT COLLATE NOCASE,
                    search TEXT,
                    short_name TEXT,
                    income TEXT,
                    hdi_rank INTEGER,
                    g20 BOOLEAN,
                    g7 BOOLEAN,
                    iodch BOOLEAN,
                    oecd BOOLEAN,
                    uri TEXT
                );
                """
            db.execute(sql)
            db.execute("CREATE UNIQUE INDEX area_iso3_iso2_index ON area(iso3 COLLATE NOCASE, iso2 COLLATE NOCASE)")
            db.execute('DROP TABLE IF EXISTS area_info')
            sql = """
                CREATE TABLE area_info
                (
                    indicator_code TEXT,
                    area TEXT,
                    value TEXT,
                    provider_url TEXT,
                    provider_name TEXT,
                    year INTEGER,
                    CONSTRAINT area_info_indicator_code_year_area_pk PRIMARY KEY (indicator_code, year, area)
                );
                """
            db.execute(sql)
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

        query = "SELECT * FROM area WHERE name = :name"
        area_name = area_name or ''
        r = self._db.execute(query, {'name': area_name}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with name " + area_name)

        data = dict(r)
        self.set_region_countries(data)
        self.set_area_info(data)
        return AreaRowAdapter().dict_to_area(data)

    def find_by_code(self, area_code):
        query = "SELECT * FROM area WHERE (iso3 = :code OR iso2 = :code)"
        area_code = area_code or ''
        r = self._db.execute(query, {'code': area_code}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with code " + area_code)

        data = dict(r)
        self.set_region_countries(data)
        self.set_area_info(data)
        return AreaRowAdapter().dict_to_area(data)

    @lru_cache(maxsize=None)
    def find_by_iso3(self, iso3_code):
        query = "SELECT * FROM area WHERE (iso3 = :iso3_code)"
        iso3_code = iso3_code or ''
        r = self._db.execute(query, {'iso3_code': iso3_code}).fetchone()
        if r is None:
            raise AreaRepositoryError("No area with code %s" % (iso3_code,))

        data = dict(r)
        self.set_region_countries(data)
        self.set_area_info(data)
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

        query = "SELECT * FROM area WHERE (iso3 = :iso3 OR iso2 = :iso2 OR name = :name)"
        r = self._db.execute(query, dict.fromkeys(['iso2', 'iso3', 'name'], area_code_or_income)).fetchone()

        if r is None:
            # FIXME: Review (old comment was: This is not working, order by is needed on method call)
            countries = self.find_countries_by_region_or_income(area_code_or_income)
            if not countries:
                raise AreaRepositoryError("No countries for code %s" % (area_code_or_income,))
            else:
                return countries

        area = dict(r)
        self.set_area_info(area)
        self.set_region_countries(area)

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
        query = "SELECT * FROM area WHERE (area = :area OR income = :income) ORDER BY :order ASC"
        params = dict.fromkeys(['area', 'income'], region_or_income)
        params['order'] = order
        rows = self._db.execute(query, params).fetchall()

        if not rows:
            raise AreaRepositoryError("No countries for code %s" % (region_or_income,))

        country_list = []

        for country in [dict(r) for r in rows]:
            self.set_region_countries(country)
            self.set_area_info(country)
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

    def upsert_area_info(self, area_or_iso3, area_info, commit=True):
        iso3 = area_or_iso3.iso3 if isinstance(area_or_iso3, Area) else area_or_iso3
        data = AreaInfoRowAdapter().info_to_dict(iso3, area_info)
        query = create_replace_query('area_info', data)
        self._db.execute(query, data)
        if commit:
            self._db.commit()

    def update_search_data(self, iso3, search, commit=True):
        self._db.execute('UPDATE area SET search=:search WHERE iso3=:iso3', {'iso3': iso3, 'search': search})
        if commit:
            self._db.commit()

    def find_area_info(self, iso3):
        """
        Finds the area infor for the country with the iso3 specified
        Args:
            iso3: iso3 code for the related area

        Returns:
            list of AreaInfo: The list of AreaInfo objects

        """
        query = "SELECT * FROM area_info WHERE area = :iso3 ORDER BY year DESC"
        rows = self._db.execute(query, {"iso3": iso3}).fetchall()

        return [dict(r) for r in rows]

    def find_areas(self, order="name"):
        """
        Finds all areas in the repository

        Args:
            order (str): Attribute of Area to sort by

        Returns:
            list of Area: All regions and countries
        """
        regions = self.find_regions(order)
        countries = self.find_countries(order)

        return regions + countries

    def find_regions(self, order="name"):
        """
        Finds all regions in the repository

        Args:
            order (str): Attribute of Region to sort by

        Returns:
            list of Region: All regions
        """
        query = "SELECT * FROM area WHERE area IS NULL ORDER BY :order ASC"
        rows = self._db.execute(query, {'order': order}).fetchall()

        regions = []

        for region in [dict(r) for r in rows]:
            self.set_region_countries(region)
            self.set_area_info(region)

            regions.append(region)

        return RegionRowAdapter().transform_to_region_list(regions)

    def find_countries(self, order="name"):
        """
        Finds all countries in the repository

        Args:
            order (str): Attribute of Country to sort by

        Returns:
            list of Country: All countries
        """
        query = "SELECT * FROM area WHERE area IS NOT NULL ORDER BY :order ASC"
        rows = self._db.execute(query, {'order': order}).fetchall()

        country_list = []

        for country in [dict(r) for r in rows]:
            self.set_area_info(country)
            country_list.append(country)

        return CountryRowAdapter().transform_to_country_list(country_list)

    def set_area_info(self, area_dict):
        """
        Finds and sets the area info for an area_dict
        Args:
            area_dict (dict): dict with area data

        Returns:

        """
        iso3 = area_dict["iso3"]
        info_list = self.find_area_info(iso3)
        area_dict["info"] = info_list

    def set_region_countries(self, region):
        """
        Sets the countries that belong to a region

        Args:
            region (dict): dict with region row data

        Returns:

        """
        iso3 = region["iso3"]
        query = "SELECT * FROM area WHERE area = :iso3 ORDER BY name ASC"
        rows = self._db.execute(query, {'iso3': iso3}).fetchall()

        country_list = []

        for country in [dict(r) for r in rows]:
            self.set_area_info(country)
            country_list.append(country)

        if country_list:
            region["countries"] = country_list

    def get_areas_info(self):
        all_countries = self.find_countries()
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
        """

        Args:
            region_dict: dict representing a row

        Returns:

        """
        data = {key: value for key, value in region_dict.items() if
                key in ['name', 'short_name', 'area', 'iso3', 'iso2', 'id', 'search', 'uri']}
        data['countries'] = CountryRowAdapter.transform_to_country_list(region_dict['countries'])
        data['info'] = AreaInfoRowAdapter.transform_to_info_list(region_dict['info'])
        return create_region(**data)

    @staticmethod
    def region_to_dict(region):
        data = dict((key, value) for key, value in list(region.to_dict().items()) if
                    key not in ['countries', 'info', 'search'])
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
        data = {key: value for key, value in country_dict.items() if
                key not in ['info']}
        data['info'] = AreaInfoRowAdapter.transform_to_info_list(country_dict['info'])
        return create_country(**data)

    @staticmethod
    def country_to_dict(country):
        data = dict((key, value) for key, value in list(country.to_dict().items()) if
                    key not in ('countries', 'info', 'search'))
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


class AreaInfoRowAdapter(object):
    @staticmethod
    def info_to_dict(iso3, area_info):
        """
        Args:
            iso3 (str):
            area_info (AreaInfo):

        Returns:
            dict: dictionary to be inserted in SQlite
        """
        data = {'area': iso3, 'value': area_info.value, 'year': area_info.year, 'provider_url': area_info.provider_url,
                'provider_name': area_info.provider_name, 'indicator_code': area_info.indicator_code}
        return data

    @staticmethod
    def dict_to_info(info_dict):
        data = {k: v for k, v in info_dict.items() if k != 'area'}
        return AreaInfo(**data)

    @staticmethod
    def transform_to_info_list(info_dict_list):
        return [AreaInfoRowAdapter.dict_to_info(info_dict) for info_dict in info_dict_list]


if __name__ == "__main__":
    import configparser
    import json

    sqlite_config = configparser.RawConfigParser()
    sqlite_config.add_section("CONNECTION")
    sqlite_config.set("CONNECTION", 'SQLITE_DB', '../../odb2015.db')
    repo = AreaRepository(False, sqlite_config)

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

    regions_by_name = repo.find_regions('name')
    assert len(regions_by_name) > 0
    print(json.dumps([region.to_dict() for region in regions_by_name]))

    france = repo.find_by_code('fr')
    assert france is not None and france.iso2 == 'FR'
    print(json.dumps(france.to_dict()))

    all_areas = repo.find_areas()
    assert all_areas
    print(json.dumps([area.to_dict() for area in all_areas]))

    print('OK!')
