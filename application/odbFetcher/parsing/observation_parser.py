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
        raw_obs_sheets = self._initialize_raw_obs_sheets()
        self._retrieve_raw_observations(raw_obs_sheets)
        self._store_raw_observations()
        # self._retrieve_secondary_observations(secondary_obs_sheet)
        # self._store_secondary_observations()

    def _initialize_raw_obs_sheets(self):
        self._log.info("\tGetting raw observations sheets...")
        data_file_name = self._config.get("DATA_ACCESS", "FILE_NAME")
        raw_obs_pattern = self._config.get("RAW_OBSERVATIONS", "SHEET_NAME_PATTERN")
        raw_obs_sheets = self._get_sheets_by_pattern(data_file_name, raw_obs_pattern)
        return raw_obs_sheets

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

                self._update_observation_ranking(per_indicator_observations)
                self._excel_raw_observations.extend(per_indicator_observations)

    @staticmethod
    def _update_observation_ranking(sorted_observations):
        """
        Updates the list of observations with the rank in the list.

        Note the ranking is absolute and does not consider draws
        Args:
            sorted_observations: a list of tuples with the observations sorted by value in ascending order (obs, area, indicator)

        Returns:
            the sorted_observations list passed as argument with the elements updated
        """

        for idx, obs_tuple in enumerate(reversed(sorted_observations)):
            obs_tuple[0].ranking = idx + 1

        return sorted_observations

    def _store_raw_observations(self):
        self._log.info("\tStoring raw observations...")
        self._observation_repo.begin_transaction()
        for excel_raw_observation in self._excel_raw_observations:
            area = excel_raw_observation[1]
            indicator = excel_raw_observation[2]
            observation = excel_observation_to_dom(excel_raw_observation[0], area, indicator)
            self._observation_repo.insert_observation(observation)
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
