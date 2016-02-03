from operator import attrgetter

from sortedcontainers import SortedListWithKey

from application.odbFetcher.parsing.excel_model.excel_observation import ExcelObservation
from application.odbFetcher.parsing.parser import Parser
from application.odbFetcher.parsing.utils import excel_observation_to_dom, na_to_none
from infrastructure.errors.errors import IndicatorRepositoryError, AreaRepositoryError
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository


class ObservationParser(Parser):
    """
    Retrieves the observations from the data Excel file and stores them into the database.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        super(ObservationParser, self).__init__(log, config, area_repo, indicator_repo, observation_repo)
        self._excel_raw_observations = []

    def run(self):
        self._log.info("Running observation parser")
        raw_obs_sheets = self._get_raw_obs_sheets()
        self._retrieve_raw_observations(raw_obs_sheets)
        self._store_raw_observations()
        scaled_obs_sheets = self._get_scaled_obs_sheets()
        self._retrieve_scaled_observations(scaled_obs_sheets)
        self._store_scaled_observations()
        # self._retrieve_secondary_observations(secondary_obs_sheet)
        # self._store_secondary_observations()

    def _get_raw_obs_sheets(self):
        self._log.info("\tGetting raw observations sheets...")
        data_file_name = self._config.get("DATA_ACCESS", "FILE_NAME")
        raw_obs_pattern = self._config.get("RAW_OBSERVATIONS", "SHEET_NAME_PATTERN")
        raw_obs_sheets = self._get_sheets_by_pattern(data_file_name, raw_obs_pattern)
        return raw_obs_sheets

    def _get_scaled_obs_sheets(self):
        self._log.info("\tGetting scaled observations sheets...")
        data_file_name = self._config.get("DATA_ACCESS", "FILE_NAME")
        scaled_obs_pattern = self._config.get("SCALED_OBSERVATIONS", "SHEET_NAME_PATTERN")
        scaled_obs_sheets = self._get_sheets_by_pattern(data_file_name, scaled_obs_pattern)
        return scaled_obs_sheets

    def _retrieve_raw_observations(self, raw_obs_sheets):
        self._log.info("\tRetrieving raw observations...")
        year_column = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN")
        iso3_column = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN")
        observation_name_row = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_NAME_ROW")
        observation_start_row = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_START_ROW")
        observation_start_column = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_START_COLUMN")

        for raw_obs_sheet in raw_obs_sheets:  # Per year
            for column_number in range(observation_start_column, raw_obs_sheet.ncols):  # Per indicator
                # Maintain sorted list with elements sorted by value
                # Elements are tuples of the form (ExcelObservation, Area, Indicator)
                per_indicator_observations = SortedListWithKey(
                    key=lambda x: x[0].value if x[0].value is not None and na_to_none(x[0].value) is not None else 0)
                # HACK: Curate data by stripping year
                indicator_code_retrieved = raw_obs_sheet.cell(observation_name_row, column_number).value
                if len(indicator_code_retrieved.split()) > 1:
                    self._log.warn('Indicator %s in %s data had to be stripped of year', indicator_code_retrieved,
                                   raw_obs_sheet.name)
                indicator_code = indicator_code_retrieved.split()[0]

                try:
                    indicator = self._indicator_repo.find_indicator_by_code(indicator_code)
                    for row_number in range(observation_start_row, raw_obs_sheet.nrows):  # Per country
                        year = int(raw_obs_sheet.cell(row_number, year_column).value)
                        iso3 = raw_obs_sheet.cell(row_number, iso3_column).value

                        try:
                            area = self._area_repo.find_by_iso3(iso3)
                            value_retrieved = raw_obs_sheet.cell(row_number, column_number).value
                            value = na_to_none(value_retrieved)
                            excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator_code, value=value,
                                                                 year=year)
                            per_indicator_observations.add((excel_observation, area, indicator))
                        except AreaRepositoryError:
                            self._log.error("No area with code %s for indicator %s(%s)" % (iso3, indicator_code, year))
                except IndicatorRepositoryError:
                    self._log.error(
                        "No indicator with code %s in %s data, indicator and year will be skipped for all countries" % (
                            indicator_code, raw_obs_sheet.name))

                self._update_observation_ranking(per_indicator_observations, observation_getter=lambda x: x[0])
                self._excel_raw_observations.extend(per_indicator_observations)

    def _retrieve_scaled_observations(self, scaled_obs_sheets):
        self._log.info("\tRetrieving scaled observations...")

    def _store_scaled_observations(self):
        self._log.info("\tStoring scaled observations...")

    @staticmethod
    def _update_observation_ranking(sorted_observations, order='asc', observation_getter=lambda x: x,
                                    attribute_getter=attrgetter('value')):
        """
        Updates a list of excel observations with the rank.
        The list must contain scores related to an indicator and a year

        Note: tied scores get the same position in the ranking
        Args:
            sorted_observations (list): a list of tuples with the observations sorted by value in ascending order (obs, area, indicator)
            order (str): order of the scores in the list, either 'asc' for ascending order or 'desc' for descending order
            observation_getter (func): function to extract an observation from the list (i.e. in the case the observation is stored in a tuple or a dict)
            attribute_getter (func): function to extract the attribute from the observation

        Returns:
            list: the resulting list with the elements updated
        """
        assert order and (order.lower() == 'asc' or order.lower() == 'desc')

        latest_observation = None
        observation_list = reversed(sorted_observations) if order.lower() == 'asc' else sorted_observations
        for idx, data in enumerate(observation_list):
            current_observation = observation_getter(data)
            if latest_observation and attribute_getter(latest_observation) == attribute_getter(current_observation):
                current_observation.ranking = latest_observation.ranking
            else:
                current_observation.ranking = idx + 1
            latest_observation = current_observation

        return observation_list

    def _store_raw_observations(self):
        self._log.info("\tStoring raw observations...")
        self._observation_repo.begin_transaction()
        for excel_raw_observation in self._excel_raw_observations:
            area = excel_raw_observation[1]
            indicator = excel_raw_observation[2]
            observation = excel_observation_to_dom(excel_raw_observation[0], area, indicator)
            self._observation_repo.insert_observation(observation, commit=False)
        self._observation_repo.commit_transaction()


if __name__ == "__main__":
    import logging
    import configparser

    log = logging.getLogger(__name__)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console.setFormatter(formatter)
    log.addHandler(console)

    config = configparser.RawConfigParser()
    config.read("../../../configuration.ini")
    config.set("CONNECTION", 'SQLITE_DB', '../../../odb2015.db')
    config.set("DATA_ACCESS", "FILE_NAME", "../../../20160128_data.xlsx")

    obs_repo = None
    indicator_repo = IndicatorRepository(False, log, config)
    area_repo = AreaRepository(False, log, config)
    parser = ObservationParser(log, config, observation_repo=obs_repo, indicator_repo=indicator_repo,
                               area_repo=area_repo)

    parser.run()
