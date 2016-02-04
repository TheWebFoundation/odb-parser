import re
from operator import attrgetter

from sortedcontainers import SortedListWithKey

from application.odbFetcher.parsing.excel_model.excel_observation import ExcelObservation
from application.odbFetcher.parsing.parser import Parser, ParserError
from application.odbFetcher.parsing.utils import excel_observation_to_dom, na_to_none, get_column_number
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
        self._excel_scaled_observations = []

    def run(self):
        self._log.info("Running observation parser")
        self._retrieve_raw_observations()
        self._store_raw_observations()
        self._retrieve_scaled_observations()
        self._store_scaled_observations()

    def _get_raw_obs_sheets(self):
        self._log.info("\tGetting raw observations sheets...")
        data_file_name = self._config.get("RAW_OBSERVATIONS", "FILE_NAME")
        raw_obs_pattern = self._config.get("RAW_OBSERVATIONS", "SHEET_NAME_PATTERN")
        raw_obs_sheets = self._get_sheets_by_pattern(data_file_name, raw_obs_pattern)
        return raw_obs_sheets

    def _get_scaled_obs_sheets(self):
        self._log.info("\tGetting scaled observations sheets...")
        data_file_name = self._config.get("SCALED_OBSERVATIONS", "FILE_NAME")
        scaled_obs_pattern = self._config.get("SCALED_OBSERVATIONS", "SHEET_NAME_PATTERN")
        scaled_obs_sheets = self._get_sheets_by_pattern(data_file_name, scaled_obs_pattern)
        return scaled_obs_sheets

    def _retrieve_raw_observations(self):
        self._log.info("\tRetrieving raw observations...")
        raw_obs_sheets = self._get_raw_obs_sheets()
        year_column = get_column_number(self._config.get("RAW_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN"))
        iso3_column = get_column_number(self._config.get("RAW_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN"))
        observation_name_row = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_NAME_ROW")
        observation_start_row = self._config.getint("RAW_OBSERVATIONS", "OBSERVATION_START_ROW")
        observation_start_column = get_column_number(self._config.get("RAW_OBSERVATIONS", "OBSERVATION_START_COLUMN"))

        for raw_obs_sheet in raw_obs_sheets:  # Per year
            for column_number in range(observation_start_column, raw_obs_sheet.ncols):  # Per indicator
                # Maintain sorted list with elements sorted by value
                # Elements are tuples of the form (ExcelObservation, Area, Indicator)
                # We're using tuples just to avoid some additional round trips to the db in order to get area and indicator
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

    def _retrieve_scaled_observations(self):
        self._log.info("\tRetrieving scaled observations...")

        scaled_obs_sheets = self._get_scaled_obs_sheets()
        for scaled_obs_sheet in scaled_obs_sheets:  # Per year
            # HACK: INDEX explicit because the columns are not ordered (simplify this if the column order gets fixed)
            self._retrieve_index_scaled_observations(scaled_obs_sheet)
            self._retrieve_subindex_and_component_scaled_observations(scaled_obs_sheet)

    def _parse_index_column_name(self, column_name):
        return re.match(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_INDEX_COLUMN_PATTERN"), column_name,
                        re.IGNORECASE)

    def _parse_subindex_column_name(self, column_name):
        return re.match(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_SUBINDEX_COLUMN_PATTERN"), column_name,
                        re.IGNORECASE)

    def _parse_subindex_column_rank(self, column_name):
        return re.match(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_SUBINDEX_RANK_COLUMN_PATTERN"),
                        column_name, re.IGNORECASE)

    def _parse_component_column_name(self, column_name):
        return re.match(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_COMPONENT_COLUMN_PATTERN"), column_name,
                        re.IGNORECASE)

    def _find_rank_column(self, sheet, subindex_name):
        observation_name_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_NAME_ROW")
        observation_start_column = get_column_number(
            self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_SUBINDEX_START_COLUMN"))

        for column_number in range(observation_start_column, sheet.ncols):
            column = sheet.cell(observation_name_row, column_number).value
            parsed_column = self._parse_subindex_column_rank(column)
            if parsed_column:
                # It's a rank, check matching with the indicator
                if parsed_column.group('subindex').upper() == subindex_name.upper():
                    return column_number

        return None

    def _retrieve_subindex_scaled_observations(self, scaled_obs_sheet, subindex_name, subindex_column):
        self._log.debug(
            "\t\tRetrieving subindex %s observations in sheet %s..." % (subindex_name, scaled_obs_sheet.name))
        year_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN"))
        iso3_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN"))
        observation_start_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_START_ROW")

        try:
            subindex_rank_column = self._find_rank_column(scaled_obs_sheet, subindex_name)
            if not subindex_rank_column:
                raise ParserError(
                    "No rank column found for SUBINDEX '%s' while parsing %s" % (subindex_name, scaled_obs_sheet.name))
            indicator = self._indicator_repo.find_indicator_by_code(subindex_name, 'SUBINDEX')
            for row_number in range(observation_start_row, scaled_obs_sheet.nrows):  # Per country
                year = int(scaled_obs_sheet.cell(row_number, year_column).value)
                iso3 = scaled_obs_sheet.cell(row_number, iso3_column).value

                try:
                    area = self._area_repo.find_by_iso3(iso3)
                    value = scaled_obs_sheet.cell(row_number, subindex_column).value
                    ranking = scaled_obs_sheet.cell(row_number, subindex_rank_column).value
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, value=value,
                                                         year=year, ranking=ranking)
                    self._excel_scaled_observations.append((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s(%s) while parsing %s" % (
                        iso3, indicator.indicator, year, scaled_obs_sheet.name))

        except IndicatorRepositoryError:
            self._log.error(
                "No SUBINDEX '%s' indicator found while parsing %s" % (subindex_name, scaled_obs_sheet.name))
        except ParserError as pe:
            self._log.error(pe)

    def _retrieve_component_scaled_observations(self, scaled_obs_sheet, component_name, component_column):
        self._log.debug(
            "\t\tRetrieving component %s observations in sheet %s..." % (component_name, scaled_obs_sheet.name))
        year_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN"))
        iso3_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN"))
        observation_start_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_START_ROW")

        # Set up sorted list to simplify ranking
        sorted_observations = SortedListWithKey(
            key=lambda x: x[0].value if x[0].value is not None and na_to_none(x[0].value) is not None else 0)

        try:
            indicator = self._indicator_repo.find_indicator_by_code(component_name, 'COMPONENT')
            for row_number in range(observation_start_row, scaled_obs_sheet.nrows):  # Per country
                year = int(scaled_obs_sheet.cell(row_number, year_column).value)
                iso3 = scaled_obs_sheet.cell(row_number, iso3_column).value

                try:
                    area = self._area_repo.find_by_iso3(iso3)
                    value = scaled_obs_sheet.cell(row_number, component_column).value
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, value=value,
                                                         year=year)
                    sorted_observations.add((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s(%s) while parsing %s" % (
                        iso3, indicator.indicator, year, scaled_obs_sheet.name))

        except IndicatorRepositoryError:
            self._log.error(
                "No SUBINDEX '%s' indicator found while parsing %s" % (component_name, scaled_obs_sheet.name))
        except ParserError as pe:
            self._log.error(pe)

        self._update_observation_ranking(sorted_observations, observation_getter=lambda x: x[0])
        self._excel_raw_observations.extend(sorted_observations)

    def _retrieve_subindex_and_component_scaled_observations(self, scaled_obs_sheet):
        self._log.info("\t\tRetrieving subindex and component observations...")
        observation_name_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_NAME_ROW")
        observation_start_column = get_column_number(
            self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_SUBINDEX_START_COLUMN"))

        for column_number in range(observation_start_column, scaled_obs_sheet.ncols):  # Per indicator
            column_name = scaled_obs_sheet.cell(observation_name_row, column_number).value
            parsed_column = self._parse_subindex_column_name(column_name)
            if parsed_column:
                # Retrieve a subindex
                self._retrieve_subindex_scaled_observations(scaled_obs_sheet, parsed_column.group('subindex'),
                                                            column_number)
            else:
                parsed_column = self._parse_component_column_name(column_name)
                if parsed_column:
                    # Retrieve a component
                    self._retrieve_component_scaled_observations(scaled_obs_sheet, parsed_column.group('component'),
                                                                 column_number)
                else:
                    self._log.warn('Ignoring column %s while parsing %s (did not detect subindex or component data)' % (
                        column_name, scaled_obs_sheet.name))

    def _retrieve_index_scaled_observations(self, scaled_obs_sheet):
        self._log.info("\t\tRetrieving index observations...")
        year_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN"))
        iso3_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN"))
        observation_name_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_NAME_ROW")
        observation_start_row = self._config.getint("SCALED_OBSERVATIONS", "OBSERVATION_START_ROW")

        index_score_column = get_column_number(
            self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_INDEX_VALUE_COLUMN"))
        index_rank_column = get_column_number(self._config.get("SCALED_OBSERVATIONS", "OBSERVATION_INDEX_RANK_COLUMN"))

        try:
            column_name = scaled_obs_sheet.cell(observation_name_row, index_score_column).value
            parsed_column = self._parse_index_column_name(column_name)
            if not parsed_column:
                raise ParserError("Column name '%s' does not match INDEX pattern while parsing %s" % (
                    column_name, scaled_obs_sheet.name))
            indicator = self._indicator_repo.find_indicator_by_code(parsed_column.group('index'))
            for row_number in range(observation_start_row, scaled_obs_sheet.nrows):  # Per country
                year = int(scaled_obs_sheet.cell(row_number, year_column).value)
                iso3 = scaled_obs_sheet.cell(row_number, iso3_column).value

                try:
                    area = self._area_repo.find_by_iso3(iso3)
                    value = scaled_obs_sheet.cell(row_number, index_score_column).value
                    ranking = scaled_obs_sheet.cell(row_number, index_rank_column).value
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, value=value,
                                                         year=year, ranking=ranking)
                    self._excel_scaled_observations.append((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s(%s) while parsing %s" % (
                        iso3, indicator.indicator, year, scaled_obs_sheet.name))
        except IndicatorRepositoryError:
            self._log.error("No INDEX indicator found while parsing %s" % (scaled_obs_sheet.name,))
        except ParserError as pe:
            self._log.error(pe)

    def _store_scaled_observations(self):
        self._log.info("\tStoring scaled observations...")
        self._store_excel_observation_array(self._excel_scaled_observations)

    def _store_excel_observation_array(self, observation_tuple_list):
        self._observation_repo.begin_transaction()
        for excel_observation_tuple in observation_tuple_list:
            area = excel_observation_tuple[1]
            indicator = excel_observation_tuple[2]
            observation = excel_observation_to_dom(excel_observation_tuple[0], area, indicator)
            self._observation_repo.insert_observation(observation, commit=False)
        self._observation_repo.commit_transaction()

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
        self._store_excel_observation_array(self._excel_raw_observations)


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
