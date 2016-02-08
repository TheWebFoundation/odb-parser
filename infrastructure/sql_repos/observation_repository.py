from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.utils import get_db, create_insert_query, is_integer
from odb.domain.model.observation.observation import Repository, create_observation
from odb.domain.model.observation.year import Year


class ObservationRepository(Repository):
    """
    Concrete mongodb repository for Observations.
    """

    def __init__(self, recreate_db, area_repo, indicator_repo, config, url_root=""):
        """
        Constructor for ObservationRepository

        Args:
            recreate_db (bool): Indicates if the database should be dropped on start
            area_repo (AreaRepository): Area repository
            indicator_repo (IndicatorRepository): Indicator repository
            url_root (str): URL root where service is deployed, it will be used to compose URIs on areas
        """

        self._config = config
        self._db = self._initialize_db(recreate_db)
        self._url_root = url_root
        # Maybe the repos could be used in a higher level context to set areas and indicators of observations
        self._area_repo = area_repo
        self._indicator_repo = indicator_repo

    def _initialize_db(self, recreate_db):
        db = get_db(self._config)
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS observation')
            sql = '''
                CREATE TABLE observation
                (
                    id INTEGER PRIMARY KEY,
                    tendency INTEGER,
                    value REAL,
                    scaled REAL,
                    area TEXT,
                    rank INTEGER,
                    rank_change INTEGER,
                    year INTEGER,
                    indicator TEXT
                );
                '''
            db.execute(sql)
            db.commit()
        return db

    def begin_transaction(self):
        self._db.execute("BEGIN TRANSACTION")

    def commit_transaction(self):
        self._db.commit()

    def insert_observation(self, observation, commit=True):
        data = ObservationRowAdapter().observation_to_dict(observation)
        query = create_insert_query('observation', data)
        self._db.execute(query, data)
        if commit:
            self._db.commit()

    def get_year_list(self):
        """
        Returns all years with observations in descending order

        Returns:
            list of Year: All years with observations in descending order
        """
        query = "SELECT DISTINCT(year) FROM observation ORDER BY year DESC"
        rows = self._db.execute(query).fetchall()

        return YearRowAdapter().transform_to_year_list([dict(r) for r in rows])

    def find_observations(self, indicator_code=None, area_code=None, year=None, area_type=None):
        """
        Returns all observations that satisfy the given filters

        Args:
            indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
            area_code (str, optional): The area code for the observation (or ALL for all areas)
            year (str, optional): The year when observation was observed
            area_type (str, optional): The area type for the observation area
        Returns:
            list of Observation: Observation that satisfy the given filters
        """
        # FIXME: Original repository raised error if no indicator or area were found
        data = {}
        indicator_query_filter = "indicator LIKE :indicator" if indicator_code else None
        if indicator_query_filter:
            data['indicator'] = indicator_code
        area_query_filter = "area LIKE :area" if area_code and area_code.upper() != 'ALL' else None
        if area_query_filter:
            data['area'] = area_code
        year_query_filter = self._build_year_query_filter(year)
        # FIXME: Review area_type subquery
        # area_type

        query_filter = " AND ".join(filter(None, [indicator_query_filter, area_query_filter, year_query_filter]))
        query = "SELECT * FROM observation WHERE " + query_filter if query_filter else "SELECT * FROM observation"
        rows = self._db.execute(query, data).fetchall()

        processed_observation_list = []
        for observation in [dict(r) for r in rows]:
            area = self._area_repo.find_by_iso3(observation['area'])
            indicator = self._indicator_repo.find_indicator_by_code(observation['indicator'])
            observation['area'] = area
            observation['indicator'] = indicator
            processed_observation_list.append(observation)

        # FIXME: The original sorted everything by ranking, do we want it too?
        return ObservationRowAdapter.transform_to_observation_list(processed_observation_list)

    def _build_year_query_filter(self, year):
        """
        Returns a year sql filter predicate to use in other queries

        Args:
            year (str): Year, year range(year_start-year_end) or LATEST (last year with observations), divide them using a ','

        Returns:
            str: The filter query predicate for sql queries
        """
        if year is None:
            return None

        if year.upper() == 'LATEST':
            year_list = self.get_year_list()
            return "(year=%d)" % (year_list[0].value,) if year_list else None

        years = year.strip().split(",")
        year_list = []
        for year in years:
            interval = year.split("-")

            if len(interval) == 1 and is_integer(interval[0]):
                year_list.append("SELECT " + interval[0])
            elif len(interval) == 2 and is_integer(interval[0]) and is_integer(interval[1]):
                for i in range(int(interval[0]), int(interval[1]) + 1):
                    year_list.append("SELECT " + str(i))

        return "(year IN (%s))" % (' UNION '.join(year_list),) if year_list else None

        # def find_linked_observations(self):
        #     return success([obs for obs in self._db['linked_observations'].find()])


        # def get_all_indicators(self):
        #     """
        #     Returns all indicators mongodb filter to use in other queries
        #
        #     Returns:
        #         dict: The filter for mongodb queries
        #     """


        # def get_indicators_by_code(self, code):
        #     """
        #     Returns an indicator mongodb filter to use in other queries
        #
        #     Args:
        #         code (str): Indicator code or codes, for many indicator codes, divide them using a ','
        #
        #     Returns:
        #         dict: The filter for mongodb queries
        #     """
        #     if code.lower() == 'ALL'.lower():  # case does not matter
        #         return {}
        #
        #     codes = code.upper().strip().split(",")
        #
        #     for code in codes:
        #         # Check that the indicator exists
        #         indicator = self._db['indicators'].find_one({"indicator": code})
        #
        #         if indicator is None:
        #             return None
        #
        #     return {"indicator": {"$in": codes}}

        # def get_countries_by_code_name_or_income(self, code):
        #     """
        #     Returns an area mongodb filter to use in other queries
        #
        #     Args:
        #         code (str): Area code or area codes, divide them using a ','
        #
        #     Returns:
        #         dict: The filter for mongodb queries
        #     """
        #     codes = code.split(",")
        #
        #     country_codes = []
        #     areas = []
        #
        #     for code in codes:
        #         code_upper = code.upper()
        #
        #         # by ISO3
        #         countries = self._db["areas"].find({"$and": [{"iso3": code_upper}, {"area": {"$ne": None}}]})
        #
        #         # by ISO2
        #         if countries is None or countries.count() == 0:
        #             countries = self._db["areas"].find({"iso2": code_upper})
        #
        #         # by name
        #         if countries is None or countries.count() == 0:
        #             countries = self._db["areas"].find({"name": code})
        #
        #         # by Continent
        #
        #         if countries is None or countries.count() == 0:
        #             countries = self._db["areas"].find({"area": code})
        #
        #         # by Income
        #         if countries is None or countries.count() == 0:
        #             countries = self._db["areas"].find({"income": code_upper})
        #
        #         if countries is None or countries.count() == 0:
        #             return None
        #
        #         for country in countries:
        #             iso3 = country["iso3"]
        #             country_codes.append(iso3)
        #             area = country["area"]
        #             areas.append(area)
        #
        #     return {
        #         "area_filter": {"area": {"$in": country_codes}},
        #         "areas": areas,
        #         "countries": country_codes
        #     }


        # @staticmethod
        # def _look_for_computation(comp_type, observation):
        #     if observation.obs_type == comp_type:
        #         return observation.value
        #     for comp in observation.computations:
        #         if comp.comp_type == comp_type:
        #             return comp.value
        #     return None
        #
        #
        # def find_observations_statistics(self, indicator_code=None, area_code=None, year=None):
        #     """
        #     Returns statitics for observations that satisfy the given filters
        #
        #     Args:
        #         indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
        #         area_code (str, optional): The area code for the observation
        #         year (str, optional): The year when observation was observed
        #     Returns:
        #         list of Statistics: Observations statistics that satisfy the filters
        #     """
        #     return StatisticsDocumentAdapter().transform_to_statistics(
        #         self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year))
        #
        #
        # def find_observations_visualisation(self, indicator_code=None, area_code=None, year=None):
        #     """
        #     Returns visualisation for observations that satisfy the given filters
        #
        #     Args:
        #         indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
        #         area_code (str, optional): The area code for the observation
        #         year (str, optional): The year when observation was observed
        #     Returns:
        #         Visualisation: Observations visualisation that satisfy the filters
        #     """
        #     observations = self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year)
        #     observations_all_areas = self.find_observations(indicator_code=indicator_code, area_code='ALL', year=year)
        #
        #     return VisualisationDocumentAdapter().transform_to_visualisation(observations, observations_all_areas)
        #
        #
        # def find_observations_grouped_by_area_visualisation(self, indicator_code=None, area_code=None, year=None):
        #     """
        #     Returns grouped by area visualisation for observations that satisfy the given filters
        #
        #     Args:
        #         indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
        #         area_code (str, optional): The area code for the observation
        #         year (str, optional): The year when observation was observed
        #     Returns:
        #         GroupedByAreaVisualisation: Observations grouped by area visualisation that satisfy the filters
        #     """
        #     area_code_splitted = area_code.split(',') if area_code is not None else None
        #     observations = self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year)
        #     observations_all_areas = self.find_observations(indicator_code=indicator_code, area_code='ALL', year=year)
        #     if area_code_splitted is None or len(area_code_splitted) == 0 or area_code == 'ALL':
        #         areas = AreaRepository(url_root=self._url_root).find_countries(order="iso3")
        #         area_code_splitted = [area.iso3 for area in areas]
        #
        #     return GroupedByAreaVisualisationDocumentAdapter().transform_to_grouped_by_area_visualisation(
        #         area_codes=area_code_splitted,
        #         observations=observations,
        #         observations_all_areas=observations_all_areas
        #     )


class ObservationRowAdapter(object):
    """
    Adapter class to transform observations between SQLite objects and Domain objects
    """

    @staticmethod
    def observation_to_dict(observation):
        """
        Transforms one single observation into a dict ready to be used in a sqlite statement

        Args:
            observation (Observation): An observation

        Returns:
            dict: Dictionary with keys and values mapped to the sqlite table
        """
        # Strip unwanted values
        data = dict(
            (key, value) for key, value in list(observation.to_dict().items()) if
            key not in ('indicator', 'year', 'area'))
        # Replace keys
        data['indicator'] = observation.indicator.indicator if observation.indicator else None
        data['year'] = observation.year.value
        data['area'] = observation.area.iso3
        return data

    @staticmethod
    def dict_to_observation(observation_dict):
        """
        Transforms one single observation

        Args:
            observation_dict (dict): Observation dictionary coming from a sqlite row with area and indicator already filled

        Returns:
            Observation: Observation object with the data in observation_dict
        """
        data = dict(observation_dict)
        return create_observation(**data)

    @staticmethod
    def transform_to_observation_list(observation_dict_list):
        """
        Transforms a list of observations

        Args:
            observation_dict_list (list): Observation dict list

        Returns:
            list of Observation: A list of observations with the data in observation_dict_list
        """
        return [ObservationRowAdapter.dict_to_observation(observation_dict) for observation_dict in
                observation_dict_list]


class YearRowAdapter(object):
    """
    Adapter class to transform years from Sqlite format to Domain Year objects
    """

    @staticmethod
    def dict_to_year(year_dict):
        """
        Transforms one single year

        Args:
            year_dict (dict): Year document in sqlite format

        Returns:
            Year: Year object with the data in year_dict
        """
        return Year(year_dict['year'])

    @staticmethod
    def transform_to_year_list(year_dict_list):
        """
        Transforms a list of years

        Args:
            year_dict_list (list): Year dict list in Sqlite format

        Returns:
            list of Year: A list of years with the data in year_document_list
        """
        return [YearRowAdapter.dict_to_year(year_dict) for year_dict in year_dict_list]


# class StatisticsDocumentAdapter(object):
#     """
#     Adapter class to transform observations from PyMongo format to Domain Statistics objects
#     """
#
#     def transform_to_statistics(self, observations):
#         """
#         Transforms a list of observations into statistics
#
#         Args:
#             observations (list): Observation document list in PyMongo format
#
#         Returns:
#             Statistics: Statistics object with statistics data for the given observations
#         """
#         return Statistics(observations)
#
#
# class VisualisationDocumentAdapter(object):
#     """
#     Adapter class to transform observations from PyMongo format to Domain Visualisation objects
#     """
#
#     def transform_to_visualisation(self, observations, observations_all_areas):
#         """
#         Transforms a list of observations into visualisation
#
#         Args:
#             observations (list of Observation): Observation list
#             observations_all_areas (list of Observation): Observations list with all areas without filter applied
#
#         Returns:
#             Visualisation: Visualisation object for the given observations
#         """
#         return Visualisation(observations, observations_all_areas)
#
#
# class GroupedByAreaVisualisationDocumentAdapter(object):
#     """
#     Adapter class to transform observations from PyMongo format to Domain GroupedByAreaVisualisation objects
#     """
#
#     def transform_to_grouped_by_area_visualisation(self, area_codes, observations, observations_all_areas):
#         """
#         Transforms a list of observations into GroupedByAreaVisualisation
#
#         Args:
#             area_codes (list of str): Iso3 codes for the area to group by
#             observations (list of Observation): Observation list
#             observations_all_areas (list of Observation): Observations list with all areas without filter applied
#
#         Returns:
#             GroupedByAreaVisualisation: GroupedByAreaVisualisation object for the given observations
#         """
#         return GroupedByAreaVisualisation(area_codes, observations, observations_all_areas)


if __name__ == "__main__":
    import configparser
    import json

    sqlite_config = configparser.RawConfigParser()
    sqlite_config.add_section('CONNECTION')
    sqlite_config.set('CONNECTION', 'SQLITE_DB', '../../odb2015.db')

    area_repo = AreaRepository(False, sqlite_config)
    indicator_repo = IndicatorRepository(False, sqlite_config)
    obs_repo = ObservationRepository(False, area_repo, indicator_repo, sqlite_config)

    print(obs_repo.get_year_list())
    print(json.dumps([o.to_dict() for o in obs_repo.find_observations(area_code="FRA", year='2014-2015')]))
