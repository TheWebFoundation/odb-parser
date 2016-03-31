from sqlite3 import IntegrityError

from infrastructure.errors.errors import IndicatorRepositoryError, ObservationRepositoryError
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.utils import get_db, create_insert_query, is_integer
from odb.domain.model.observation.grouped_by_area_visualisation import GroupedByAreaVisualisation
from odb.domain.model.observation.observation import Repository, create_observation
from odb.domain.model.observation.statistics import Statistics
from odb.domain.model.observation.visualisation import Visualisation
from odb.domain.model.observation.year import Year


class ObservationRepository(Repository):
    """
    Concrete mongodb repository for Observations.
    """

    def __init__(self, recreate_db, area_repo, indicator_repo, config):
        """
        Constructor for ObservationRepository

        Args:
            recreate_db (bool): Indicates if the database should be dropped on start
            area_repo (AreaRepository): Area repository
            indicator_repo (IndicatorRepository): Indicator repository
        """

        self._config = config
        self._db = self._initialize_db(recreate_db)
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
                    value REAL,
                    area TEXT,
                    rank INTEGER,
                    rank_change INTEGER,
                    year INTEGER,
                    indicator TEXT,
                    dataset_indicator TEXT,
                    uri TEXT,
                    CONSTRAINT observation_indicator_area_year_uniq UNIQUE (indicator, area, year, dataset_indicator)
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
        try:
            self._db.execute(query, data)
        except IntegrityError:
            raise ObservationRepositoryError("Unique constraint failed for observation (data:%s)" % (data,))
        if commit:
            self._db.commit()

    def update_rank_change(self):
        query = """
            UPDATE observation SET rank_change = CASE
                  WHEN (SELECT 1 FROM observation o2 WHERE o2.year = observation.year - 1 AND o2.area = observation.area AND o2.indicator = observation.indicator)
                      THEN (SELECT o2.rank - observation.rank FROM observation o2 WHERE o2.year = observation.year - 1 AND o2.area = observation.area AND o2.indicator = observation.indicator)
                      ELSE NULL
                      END;
        """

        self._db.execute(query)
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

    def find_tree_observations(self, indicator_code, area_code=None, year=None, level='COMPONENT', filter_dataset=True):
        if indicator_code is not None:
            self._indicator_repo.find_indicator_by_code(indicator_code)

        data = {'indicator': indicator_code}
        year_query_filter = self._build_year_query_filter(year)
        level_query_filter = self._build_level_query_filter(level)
        area_query_filter = "area = :area" if area_code and area_code.upper() != 'ALL' else None
        if area_query_filter:
            data['area'] = area_code
        dataset_query_filter = "dataset_indicator IS NULL" if filter_dataset else None
        query_filter = " AND ".join(filter(None, [dataset_query_filter, year_query_filter, level_query_filter]))
        query = "SELECT * FROM observation WHERE " + query_filter if query_filter else "SELECT * FROM observation"
        rows = self._db.execute(query, data).fetchall()

        processed_observation_list = []
        for observation in [dict(r) for r in rows]:
            area = self._area_repo.find_by_iso3(observation['area'])
            # Filter out orphan observations
            try:
                indicator = self._indicator_repo.find_indicator_by_code(observation['indicator'])
            except IndicatorRepositoryError:
                continue
            observation['area'] = area
            observation['indicator'] = indicator
            observation['dataset_indicator'] = self._indicator_repo.find_indicator_by_code(
                observation['dataset_indicator']) if observation['dataset_indicator'] else None
            processed_observation_list.append(observation)

        return ObservationRowAdapter.transform_to_observation_list(processed_observation_list)

    # FIXME: Review area_type subquery
    # FIXME: Filter out or not dataset observations when asked for an indicator?
    def find_observations(self, indicator_code=None, area_code=None, year=None, area_type=None, filter_dataset=True):
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
        # NOTE: Original a4ai project raised error if no indicator or area were found
        if indicator_code is not None:
            self._indicator_repo.find_indicator_by_code(indicator_code)
        if area_code is not None and area_code != "ALL":
            self._area_repo.find_by_code(area_code)

        data = {}
        indicator_query_filter = "indicator = :indicator" if indicator_code else None
        if indicator_query_filter:
            data['indicator'] = indicator_code
        area_query_filter = "area = :area" if area_code and area_code.upper() != 'ALL' else None
        if area_query_filter:
            data['area'] = area_code
        year_query_filter = self._build_year_query_filter(year)
        dataset_query_filter = "dataset_indicator IS NULL" if filter_dataset else None

        query_filter = " AND ".join(
            filter(None, [dataset_query_filter, indicator_query_filter, area_query_filter, year_query_filter]))
        query = "SELECT * FROM observation WHERE " + query_filter if query_filter else "SELECT * FROM observation"
        rows = self._db.execute(query, data).fetchall()

        processed_observation_list = []
        for observation in [dict(r) for r in rows]:
            area = self._area_repo.find_by_iso3(observation['area'])
            # Filter out orphan observations
            try:
                indicator = self._indicator_repo.find_indicator_by_code(observation['indicator'])
            except IndicatorRepositoryError:
                continue
            observation['area'] = area
            observation['indicator'] = indicator
            observation['dataset_indicator'] = self._indicator_repo.find_indicator_by_code(
                observation['dataset_indicator']) if observation['dataset_indicator'] else None
            processed_observation_list.append(observation)

        # FIXME: The original sorted everything by ranking, do we want it too?
        return ObservationRowAdapter.transform_to_observation_list(processed_observation_list)

    def find_dataset_observations(self, indicator_code, area_code, year):
        indicator = self._indicator_repo.find_indicator_by_code(indicator_code)
        query = "SELECT * FROM observation WHERE year=:year AND indicator=:indicator AND area=:area AND dataset_indicator IS NOT NULL"
        data = {'indicator': indicator_code, 'year': year, 'area': area_code}
        rows = self._db.execute(query, data)

        processed_observation_list = []
        for observation in [dict(r) for r in rows]:
            area = self._area_repo.find_by_iso3(observation['area'])
            observation['area'] = area
            observation['indicator'] = indicator
            observation['dataset_indicator'] = self._indicator_repo.find_indicator_by_code(
                observation['dataset_indicator'])
            processed_observation_list.append(observation)

        return ObservationRowAdapter.transform_to_observation_list(processed_observation_list)

    def _build_level_query_filter(self, level):
        if level is None:
            return None

        if level.upper() == 'INDEX':
            return "(indicator IN (SELECT indicator FROM indicator WHERE index_code IS NULL AND indicator:indicator))"
        elif level.upper() == 'SUBINDEX':
            return "(indicator IN (SELECT indicator FROM indicator WHERE subindex IS NULL AND (index_code=:indicator OR indicator=:indicator)))"
        elif level.upper() == 'COMPONENT':
            return "(indicator IN (SELECT indicator FROM indicator WHERE component IS NULL AND (subindex=:indicator OR index_code=:indicator OR indicator=:indicator)))"
        elif level.upper() == 'INDICATOR':
            return "(indicator IN (SELECT indicator FROM indicator WHERE component=:indicator OR subindex=:indicator OR index_code=:indicator OR indicator=:indicator))"

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

    def find_observations_statistics(self, indicator_code=None, area_code=None, year=None):
        """
        Returns statitics for observations that satisfy the given filters

        Args:
            indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
            area_code (str, optional): The area code for the observation
            year (str, optional): The year when observation was observed
        Returns:
            list of Statistics: Observations statistics that satisfy the filters
        """
        return StatisticsDocumentAdapter().transform_to_statistics(
            self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year))

    def find_observations_visualisation(self, indicator_code=None, area_code=None, year=None):
        """
        Returns visualisation for observations that satisfy the given filters

        Args:
            indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
            area_code (str, optional): The area code for the observation
            year (str, optional): The year when observation was observed
        Returns:
            Visualisation: Observations visualisation that satisfy the filters
        """
        observations = self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year)
        observations_all_areas = self.find_observations(indicator_code=indicator_code, area_code='ALL', year=year)

        return VisualisationDocumentAdapter().transform_to_visualisation(observations, observations_all_areas)

    def find_observations_grouped_by_area_visualisation(self, indicator_code=None, area_code=None, year=None):
        """
        Returns grouped by area visualisation for observations that satisfy the given filters

        Args:
            indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
            area_code (str, optional): The area code for the observation
            year (str, optional): The year when observation was observed
        Returns:
            GroupedByAreaVisualisation: Observations grouped by area visualisation that satisfy the filters
        """
        area_code_splitted = area_code.split(',') if area_code is not None else None
        observations = self.find_observations(indicator_code=indicator_code, area_code=area_code, year=year)
        observations_all_areas = self.find_observations(indicator_code=indicator_code, area_code='ALL', year=year)
        if area_code_splitted is None or len(area_code_splitted) == 0 or area_code == 'ALL':
            areas = self._area_repo.find_countries(order="iso3")
            area_code_splitted = [area.iso3 for area in areas]

        return GroupedByAreaVisualisationDocumentAdapter().transform_to_grouped_by_area_visualisation(
            area_codes=area_code_splitted,
            observations=observations,
            observations_all_areas=observations_all_areas
        )

    def find_tree_observations_grouped_by_area_visualisation(self, indicator_code=None, year=None):
        """
        Returns grouped by area visualisation for observations that satisfy the given filters

        Args:
            indicator_code (str, optional): The indicator code (indicator attribute in Indicator)
            area_code (str, optional): The area code for the observation
            year (str, optional): The year when observation was observed
        Returns:
            GroupedByAreaVisualisation: Observations grouped by area visualisation that satisfy the filters
        """
        observations = self.find_tree_observations(indicator_code=indicator_code, year=year)
        areas = self._area_repo.find_countries(order="iso3")
        area_code_splitted = [area.iso3 for area in areas]

        return GroupedByAreaVisualisationDocumentAdapter().transform_to_grouped_by_area_visualisation(
            area_codes=area_code_splitted,
            observations=observations,
            observations_all_areas=observations
        )


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
            key not in ('indicator', 'dataset_indicator', 'year', 'area'))
        # Replace keys
        data['indicator'] = observation.indicator.indicator if observation.indicator else None
        data['dataset_indicator'] = observation.dataset_indicator.indicator if observation.dataset_indicator else None
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


class StatisticsDocumentAdapter(object):
    """
    Adapter class to transform observations from Sqlite format to Domain Statistics objects
    """

    @staticmethod
    def transform_to_statistics(observations):
        """
        Transforms a list of observations into statistics

        Args:
            observations (list): Observation document list in Sqlite format

        Returns:
            Statistics: Statistics object with statistics data for the given observations
        """
        return Statistics(observations)


class VisualisationDocumentAdapter(object):
    """
    Adapter class to transform observations from Sqlite format to Domain Visualisation objects
    """

    @staticmethod
    def transform_to_visualisation(observations, observations_all_areas):
        """
        Transforms a list of observations into visualisation

        Args:
            observations (list of Observation): Observation list
            observations_all_areas (list of Observation): Observations list with all areas without filter applied

        Returns:
            Visualisation: Visualisation object for the given observations
        """
        return Visualisation(observations, observations_all_areas)


class GroupedByAreaVisualisationDocumentAdapter(object):
    """
    Adapter class to transform observations from SQlite format to Domain GroupedByAreaVisualisation objects
    """

    @staticmethod
    def transform_to_grouped_by_area_visualisation(area_codes, observations, observations_all_areas):
        """
        Transforms a list of observations into GroupedByAreaVisualisation

        Args:
            area_codes (list of str): Iso3 codes for the area to group by
            observations (list of Observation): Observation list
            observations_all_areas (list of Observation): Observations list with all areas without filter applied

        Returns:
            GroupedByAreaVisualisation: GroupedByAreaVisualisation object for the given observations
        """
        return GroupedByAreaVisualisation(area_codes, observations, observations_all_areas)


if __name__ == "__main__":
    import configparser
    import json

    sqlite_config = configparser.RawConfigParser()
    sqlite_config.add_section('CONNECTION')
    sqlite_config.set('CONNECTION', 'SQLITE_DB', '../../odb2015.db')

    area_repo = AreaRepository(False, sqlite_config)
    indicator_repo = IndicatorRepository(False, sqlite_config)
    obs_repo = ObservationRepository(False, area_repo, indicator_repo, sqlite_config)

    # print(obs_repo.get_year_list())
    # print(json.dumps([o.to_dict() for o in obs_repo.find_observations(area_code="FRA", year='2014-2015')]))

    with open('dump.json', 'w') as f:
        json.dump([o.to_dict() for o in obs_repo.find_tree_observations(indicator_code='ODB', level='SUBINDEX')], f)
