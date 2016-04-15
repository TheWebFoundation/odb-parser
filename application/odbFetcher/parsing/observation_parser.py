import re
from operator import attrgetter
from urllib.parse import urljoin

from sortedcontainers import SortedListWithKey
from xlrd import colname, cellname

from application.odbFetcher.parsing.excel_model.excel_observation import ExcelObservation
from application.odbFetcher.parsing.parser import Parser, ParserError
from application.odbFetcher.parsing.utils import excel_observation_to_dom, na_to_none, get_column_number
from infrastructure.errors.errors import IndicatorRepositoryError, AreaRepositoryError
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from odb.domain.model.indicator.indicator import create_indicator


class ObservationParser(Parser):
    """
    Retrieves the observations from the data Excel file and stores them into the database.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        super(ObservationParser, self).__init__(log, config, area_repo, indicator_repo, observation_repo)
        self._excel_raw_observations = []
        self._excel_dataset_observations = []
        self._excel_structure_observations = []

    def run(self):
        self._log.info("Running observation parser")
        self._retrieve_raw_observations()
        self._store_raw_observations()
        self._retrieve_structure_observations()
        self._store_structure_observations()
        self._retrieve_dataset_assesments()
        self._store_dataset_observations()
        self._update_rank_change()

    def _update_rank_change(self):
        self._log.info("\tUpdating rank changes")
        self._observation_repo.update_rank_change()

    def _get_raw_obs_sheets(self):
        self._log.info("\tGetting raw observations sheets...")
        data_file_name = self._config.get("RAW_OBSERVATIONS", "FILE_NAME")
        raw_obs_pattern = self._config.get("RAW_OBSERVATIONS", "SHEET_NAME_PATTERN")
        raw_obs_sheets = self._get_sheets_by_pattern(data_file_name, raw_obs_pattern)
        return raw_obs_sheets

    def _get_dataset_obs_sheets(self):
        self._log.info("\tGetting dataset observations sheets...")
        data_file_name = self._config.get("DATASET_OBSERVATIONS", "FILE_NAME")
        dataset_obs_pattern = self._config.get("DATASET_OBSERVATIONS", "SHEET_NAME_PATTERN")
        dataset_obs_sheets = self._get_sheets_by_pattern(data_file_name, dataset_obs_pattern)
        return dataset_obs_sheets

    def _get_structure_obs_sheets(self):
        self._log.info("\tGetting structure observation sheets...")
        data_file_name = self._config.get("STRUCTURE_OBSERVATIONS", "FILE_NAME")
        structure_obs_pattern = self._config.get("STRUCTURE_OBSERVATIONS", "SHEET_NAME_PATTERN")
        structure_obs_sheets = self._get_sheets_by_pattern(data_file_name, structure_obs_pattern)
        return structure_obs_sheets

    def _retrieve_dataset_assesments(self):
        self._log.info("\tRetrieving dataset assesments")
        dataset_obs_sheets = self._get_dataset_obs_sheets()
        indicator_code_error_cache = {}

        for dataset_obs_sheet in dataset_obs_sheets:  # Per year
            sheet_year = re.match(self._config.get("DATASET_OBSERVATIONS", "SHEET_NAME_PATTERN"),
                                  dataset_obs_sheet.name).group("year")
            year_column = get_column_number(
                self._config_get("DATASET_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN", sheet_year))
            iso3_column = get_column_number(
                self._config_get("DATASET_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN", sheet_year))
            indicator_column = get_column_number(
                self._config_get("DATASET_OBSERVATIONS", "OBSERVATION_INDICATOR_COLUMN", sheet_year))
            observation_name_row = self._config_getint("DATASET_OBSERVATIONS", "OBSERVATION_NAME_ROW", sheet_year)
            observation_start_row = self._config_getint("DATASET_OBSERVATIONS", "OBSERVATION_START_ROW", sheet_year)
            observation_start_column = get_column_number(
                self._config_get("DATASET_OBSERVATIONS", "OBSERVATION_START_COLUMN", sheet_year))

            for column_number in range(observation_start_column, dataset_obs_sheet.ncols):  # Per dataset indicator
                dataset_indicator_code = dataset_obs_sheet.cell(observation_name_row, column_number).value

                try:
                    dataset_indicator = self._indicator_repo.find_indicator_by_code(dataset_indicator_code)
                except IndicatorRepositoryError:
                    if dataset_indicator_code not in indicator_code_error_cache:
                        self._log.warn(
                            "No indicator with code %s found while parsing %s[%s] (additional errors regarding this indicator will be omitted)" % (
                                dataset_indicator_code, dataset_obs_sheet.name, colname(column_number)))
                        indicator_code_error_cache[dataset_indicator_code] = True
                    continue

                for row_number in range(observation_start_row, dataset_obs_sheet.nrows):  # Per country and variable
                    year = int(dataset_obs_sheet.cell(row_number, year_column).value)
                    iso3 = dataset_obs_sheet.cell(row_number, iso3_column).value
                    try:
                        indicator_code = dataset_obs_sheet.cell(row_number, indicator_column).value
                        indicator = self._indicator_repo.find_indicator_by_code(indicator_code)
                        area = self._area_repo.find_by_iso3(iso3)
                        value_retrieved = dataset_obs_sheet.cell(row_number, column_number).value
                        value = na_to_none(value_retrieved)
                        excel_dataset_observation = ExcelObservation(iso3=iso3, indicator_code=indicator_code,
                                                                     value=value,
                                                                     year=year,
                                                                     dataset_indicator_code=dataset_indicator_code)
                        self._excel_dataset_observations.append(
                            (excel_dataset_observation, area, indicator, dataset_indicator))
                    except IndicatorRepositoryError:
                        if indicator_code not in indicator_code_error_cache:
                            self._log.warn(
                                "No indicator with code %s found while parsing %s[%s] (additional errors regarding this indicator will be omitted)" % (
                                    indicator_code, dataset_obs_sheet.name, cellname(indicator_column, row_number)))
                            indicator_code_error_cache[indicator_code] = True
                    except AreaRepositoryError:
                        self._log.error("No area found with code %s while parsing %s" % (
                            iso3, dataset_obs_sheet.name))

    def _retrieve_raw_observations(self):
        self._log.info("\tRetrieving raw observations...")
        raw_obs_sheets = self._get_raw_obs_sheets()

        for raw_obs_sheet in raw_obs_sheets:  # Per year
            sheet_year = re.match(self._config.get("RAW_OBSERVATIONS", "SHEET_NAME_PATTERN"),
                                  raw_obs_sheet.name).group("year")
            empty_row_error_cache = {}
            year_column = get_column_number(self._config_get("RAW_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN", sheet_year))
            iso3_column = get_column_number(self._config_get("RAW_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN", sheet_year))
            observation_name_row = self._config_getint("RAW_OBSERVATIONS", "OBSERVATION_NAME_ROW", sheet_year)
            observation_start_row = self._config_getint("RAW_OBSERVATIONS", "OBSERVATION_START_ROW", sheet_year)
            observation_start_column = get_column_number(
                self._config_get("RAW_OBSERVATIONS", "OBSERVATION_START_COLUMN", sheet_year))
            check_column = get_column_number(
                self._config_get("RAW_OBSERVATIONS", "OBSERVATION_CHECK_COLUMN", sheet_year))

            for column_number in range(observation_start_column, raw_obs_sheet.ncols):  # Per indicator
                # Maintain sorted list with elements sorted by value
                # Elements are tuples of the form (ExcelObservation, Area, Indicator)
                # We're using tuples just to avoid some additional round trips to the db in order to get area and indicator
                per_indicator_observations = SortedListWithKey(
                    key=lambda x: x[0].value if x[0].value is not None and na_to_none(x[0].value) is not None else 0)
                # HACK: Curate data by stripping year
                indicator_code_retrieved = raw_obs_sheet.cell(observation_name_row, column_number).value
                if len(indicator_code_retrieved.split()) > 1:
                    self._log.debug('Indicator %s in had to be stripped of year while parsing %s',
                                    indicator_code_retrieved, raw_obs_sheet.name)
                try:
                    indicator_code = indicator_code_retrieved.split()[0]
                except IndexError:
                    self._log.warn(
                        'Wrong Indicator name %s while parsing %s[%s], skipping column' % (
                            indicator_code_retrieved, raw_obs_sheet.name, colname(column_number)))
                    continue

                try:
                    indicator = self._indicator_repo.find_indicator_by_code(indicator_code)
                except IndicatorRepositoryError:
                    self._log.warn(
                        "No indicator with code %s found while parsing %s" % (indicator_code, raw_obs_sheet.name))
                    indicator = create_indicator(indicator=indicator_code)  # Orphan indicator

                for row_number in range(observation_start_row, raw_obs_sheet.nrows):  # Per country
                    if not raw_obs_sheet.cell(row_number, check_column).value or row_number in empty_row_error_cache:
                        if row_number not in empty_row_error_cache:
                            self._log.debug(
                                "Skipping row while parsing %s[%s] (did not detect value on check column, additional errors regarding this row will be omitted)" % (
                                    raw_obs_sheet.name, row_number))
                        empty_row_error_cache[row_number] = True
                        continue
                    try:
                        year = int(raw_obs_sheet.cell(row_number, year_column).value)
                        iso3 = raw_obs_sheet.cell(row_number, iso3_column).value
                        area = self._area_repo.find_by_iso3(iso3)
                        value_retrieved = raw_obs_sheet.cell(row_number, column_number).value
                        value = na_to_none(value_retrieved)
                        excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator_code, value=value,
                                                             year=year)
                        per_indicator_observations.add((excel_observation, area, indicator))
                    except AreaRepositoryError:
                        self._log.error("No area found with code %s for indicator %s while parsing %s" % (
                            iso3, indicator_code, raw_obs_sheet.name))
                    except:
                        self._log.error("Unexpected error parsing %s[%s]" % (raw_obs_sheet.name, row_number))

                self._update_observation_ranking(per_indicator_observations, observation_getter=lambda x: x[0])
                self._excel_raw_observations.extend(per_indicator_observations)

    def _retrieve_structure_observations(self):
        self._log.info("\tRetrieving structure observation...")

        structure_obs_sheets = self._get_structure_obs_sheets()
        for structure_obs_sheet in structure_obs_sheets:  # Per year
            # INDEX explicit because the columns are not ordered (simplify this if the column order gets fixed)
            self._retrieve_index_observations(structure_obs_sheet)
            self._retrieve_subindex_and_component_observations(structure_obs_sheet)

    def _parse_index_scaled_column_name(self, column_name, year):
        return re.match(self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_INDEX_SCALED_COLUMN_PATTERN", year),
                        column_name, re.IGNORECASE)

    def _parse_subindex_scaled_column_name(self, column_name, year):
        return re.match(self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_SUBINDEX_SCALED_COLUMN_PATTERN", year),
                        column_name, re.IGNORECASE)

    def _parse_subindex_column_rank(self, column_name, year):
        return re.match(self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_SUBINDEX_RANK_COLUMN_PATTERN", year),
                        column_name, re.IGNORECASE)

    def _parse_component_scaled_column_name(self, column_name, year):
        return re.match(self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_COMPONENT_SCALED_COLUMN_PATTERN", year),
                        column_name, re.IGNORECASE)

    def _find_rank_column(self, sheet, subindex_name, year):
        observation_name_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_NAME_ROW", year)
        observation_start_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_SUBINDEX_START_COLUMN", year))

        for column_number in range(observation_start_column, sheet.ncols):
            column = sheet.cell(observation_name_row, column_number).value
            parsed_column = self._parse_subindex_column_rank(column, year)
            if parsed_column:
                # It's a rank, check matching with the indicator
                if parsed_column.group('subindex').upper() == subindex_name.upper():
                    return column_number

        return None

    def _retrieve_subindex_observations(self, structure_obs_sheet, subindex_name, subindex_scaled_column, sheet_year):
        self._log.debug(
            "\t\tRetrieving subindex %s observations in sheet %s..." % (subindex_name, structure_obs_sheet.name))
        year_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN", sheet_year))
        iso3_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN", sheet_year))
        check_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_CHECK_COLUMN", sheet_year))
        observation_start_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_START_ROW", sheet_year)
        empty_row_error_cache = {}

        try:
            subindex_rank_column = self._find_rank_column(structure_obs_sheet, subindex_name, sheet_year)
            if not subindex_rank_column:
                self._log.warn("No rank column found for SUBINDEX '%s' while parsing %s" % (
                    subindex_name, structure_obs_sheet.name))
            indicator = self._indicator_repo.find_indicator_by_code(subindex_name, 'SUBINDEX')
            for row_number in range(observation_start_row, structure_obs_sheet.nrows):  # Per country
                if not structure_obs_sheet.cell(row_number, check_column).value or row_number in empty_row_error_cache:
                    if row_number not in empty_row_error_cache:
                        self._log.debug(
                            "Skipping row while parsing %s[%s] (did not detect value on check column, additional errors regarding this row will be omitted)" % (
                                structure_obs_sheet.name, row_number))
                    empty_row_error_cache[row_number] = True
                    continue
                try:
                    year = int(structure_obs_sheet.cell(row_number, year_column).value)
                    iso3 = structure_obs_sheet.cell(row_number, iso3_column).value
                    area = self._area_repo.find_by_iso3(iso3)
                    value = structure_obs_sheet.cell(row_number, subindex_scaled_column).value
                    rank = structure_obs_sheet.cell(row_number,
                                                    subindex_rank_column).value if subindex_rank_column else None
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, year=year,
                                                         rank=rank, value=value)
                    if [t for t in self._excel_structure_observations if
                        t[0].year == year and t[1].iso3 == iso3 and t[2].indicator == indicator.indicator]:
                        self._log.warn("Ignoring duplicate observations for SUBINDEX %s while parsing %s [%s]" % (
                            indicator.indicator, structure_obs_sheet.name,
                            colname(subindex_scaled_column)))
                        # Will not continue parsing, we could check this also at the beginning if we extract the
                        # year from the sheet name
                        return
                    else:
                        self._excel_structure_observations.append((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s while parsing %s" % (
                        iso3, indicator.indicator, structure_obs_sheet.name))
                except:
                    self._log.error("Unexpected error parsing %s[%s]" % (structure_obs_sheet.name, row_number))
        except IndicatorRepositoryError:
            self._log.error(
                "No SUBINDEX '%s' indicator found while parsing %s [%s]" % (
                    subindex_name, structure_obs_sheet.name, colname(subindex_scaled_column)))

    def _get_aliased_component(self, component_name, year):
        mangled_indicator = re.sub(' +', r'_', component_name).upper()
        config_alias = 'ALIAS-%s-%s' % (mangled_indicator, year)
        if self._config.has_option('STRUCTURE_OBSERVATIONS', config_alias):
            return self._config.get('STRUCTURE_OBSERVATIONS', config_alias)
        else:
            return None

    def _retrieve_component_observations(self, structure_obs_sheet, subindex_name, component_short_name,
                                         component_scaled_column, sheet_year):
        self._log.debug("\t\tRetrieving component %s from subindex %s observations in sheet %s..." % (
            component_short_name, subindex_name, structure_obs_sheet.name))
        empty_row_error_cache = {}
        year_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN", sheet_year))
        iso3_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN", sheet_year))
        observation_start_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_START_ROW", sheet_year)
        check_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_CHECK_COLUMN", sheet_year))

        aliased_short_name = self._get_aliased_component(component_short_name, sheet_year)

        if aliased_short_name:
            self._log.info("Using alias %s for COMPONENT %s while parsing %s [%s]" % (
                aliased_short_name, component_short_name, structure_obs_sheet.name, colname(component_scaled_column)))
            short_name = aliased_short_name
        else:
            short_name = component_short_name

        # Set up sorted list to simplify ranking (components are not ranked in the spreadsheet)
        sorted_observations = SortedListWithKey(
            key=lambda x: x[0].value if x[0].value is not None and na_to_none(x[0].value) is not None else 0)

        try:
            indicator = self._indicator_repo.find_component_by_short_name(short_name, subindex_name)
            for row_number in range(observation_start_row, structure_obs_sheet.nrows):  # Per country
                if not structure_obs_sheet.cell(row_number, check_column).value or row_number in empty_row_error_cache:
                    if row_number not in empty_row_error_cache:
                        self._log.debug(
                            "Skipping row while parsing %s[%s] (did not detect value on check column, additional errors regarding this row will be omitted)" % (
                                structure_obs_sheet.name, row_number))
                    empty_row_error_cache[row_number] = True
                    continue
                try:
                    year = int(structure_obs_sheet.cell(row_number, year_column).value)
                    iso3 = structure_obs_sheet.cell(row_number, iso3_column).value
                    area = self._area_repo.find_by_iso3(iso3)
                    value = structure_obs_sheet.cell(row_number, component_scaled_column).value
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, year=year,
                                                         value=value)
                    if [t for t in sorted_observations if
                        t[0].year == year and t[1].iso3 == iso3 and t[2].indicator == indicator.indicator]:
                        self._log.warn("Ignoring duplicate observations for COMPONENT %s while parsing %s [%s]" % (
                            indicator.indicator, structure_obs_sheet.name,
                            colname(component_scaled_column)))
                        # Will not continue parsing, we could check this also at the beginning if we extract the
                        # year from the sheet name
                        return
                    else:
                        sorted_observations.add((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s while parsing %s" % (
                        iso3, indicator.indicator, structure_obs_sheet.name))
                except:
                    self._log.error("Unexpected error parsing %s[%s]" % (structure_obs_sheet.name, row_number))
        except IndicatorRepositoryError:
            self._log.error(
                "No COMPONENT '%s' indicator found while parsing %s [%s]" % (
                    short_name, structure_obs_sheet.name, colname(component_scaled_column)))

        # Rank them based on their scaled score
        self._update_observation_ranking(sorted_observations, observation_getter=lambda x: x[0])
        self._excel_structure_observations.extend(sorted_observations)

    def _retrieve_subindex_and_component_observations(self, structure_obs_sheet):
        self._log.info("\t\tRetrieving subindex and component observations...")
        sheet_year = re.match(self._config.get("STRUCTURE_OBSERVATIONS", "SHEET_NAME_PATTERN"),
                              structure_obs_sheet.name).group("year")
        observation_name_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_NAME_ROW", sheet_year)
        observation_start_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_SUBINDEX_START_COLUMN", sheet_year))

        for column_number in range(observation_start_column, structure_obs_sheet.ncols):  # Per indicator
            column_name = structure_obs_sheet.cell(observation_name_row, column_number).value
            parsed_column = self._parse_subindex_scaled_column_name(column_name, sheet_year)
            if parsed_column:
                # Retrieve a subindex
                self._retrieve_subindex_observations(structure_obs_sheet, parsed_column.group('subindex'),
                                                     column_number, sheet_year)
            else:
                parsed_column = self._parse_component_scaled_column_name(column_name, sheet_year)
                if parsed_column:
                    # Retrieve a component
                    self._retrieve_component_observations(structure_obs_sheet, parsed_column.group('subindex'),
                                                          parsed_column.group('component'), column_number, sheet_year)
                else:
                    self._log.debug(
                        'Ignoring column %s while parsing %s (did not detect subindex or component scaled data)' % (
                            column_name, structure_obs_sheet.name))

    def _retrieve_index_observations(self, structure_obs_sheet):
        self._log.info("\t\tRetrieving index observations...")
        empty_row_error_cache = {}
        sheet_year = re.match(self._config.get("STRUCTURE_OBSERVATIONS", "SHEET_NAME_PATTERN"),
                              structure_obs_sheet.name).group("year")
        year_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_YEAR_COLUMN", sheet_year))
        iso3_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_ISO3_COLUMN", sheet_year))
        observation_name_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_NAME_ROW", sheet_year)
        observation_start_row = self._config_getint("STRUCTURE_OBSERVATIONS", "OBSERVATION_START_ROW", sheet_year)
        check_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_CHECK_COLUMN", sheet_year))

        index_scaled_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_INDEX_SCALED_COLUMN", sheet_year))
        index_rank_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_INDEX_RANK_COLUMN", sheet_year))
        index_rank_change_column = get_column_number(
            self._config_get("STRUCTURE_OBSERVATIONS", "OBSERVATION_INDEX_RANK_CHANGE_COLUMN", sheet_year))

        try:
            column_name = structure_obs_sheet.cell(observation_name_row, index_scaled_column).value
            parsed_column = self._parse_index_scaled_column_name(column_name, sheet_year)
            # Sanity check useful if there could be more than one INDEX, otherwise this check could be relaxed
            if not parsed_column:
                raise IndicatorRepositoryError("Column name '%s' does not match INDEX pattern while parsing %s" % (
                    column_name, structure_obs_sheet.name))
            indicator = self._indicator_repo.find_indicator_by_code(parsed_column.group('index'))
            for row_number in range(observation_start_row, structure_obs_sheet.nrows):  # Per country
                if not structure_obs_sheet.cell(row_number, check_column).value or row_number in empty_row_error_cache:
                    if row_number not in empty_row_error_cache:
                        self._log.debug(
                            "Skipping row while parsing %s[%s] (did not detect value on check column, additional errors regarding this row will be omitted)" % (
                                structure_obs_sheet.name, row_number))
                    empty_row_error_cache[row_number] = True
                    continue
                try:
                    year = int(structure_obs_sheet.cell(row_number, year_column).value)
                    iso3 = structure_obs_sheet.cell(row_number, iso3_column).value
                    area = self._area_repo.find_by_iso3(iso3)
                    value = structure_obs_sheet.cell(row_number, index_scaled_column).value
                    rank = structure_obs_sheet.cell(row_number, index_rank_column).value
                    # Allow for empty values here
                    rank_change = na_to_none(structure_obs_sheet.cell(row_number,
                                                                      index_rank_change_column).value) if index_rank_change_column else None
                    excel_observation = ExcelObservation(iso3=iso3, indicator_code=indicator.indicator, year=year,
                                                         rank=rank, value=value, rank_change=rank_change)
                    self._excel_structure_observations.append((excel_observation, area, indicator))
                except AreaRepositoryError:
                    self._log.error("No area with code %s for indicator %s while parsing %s" % (
                        iso3, indicator.indicator, structure_obs_sheet.name))
                except:
                    self._log.error("Unexpected error parsing %s[%s]" % (structure_obs_sheet.name, row_number))
        except IndicatorRepositoryError:
            self._log.error("No INDEX indicator found while parsing %s [%s]" % (
                structure_obs_sheet.name, colname(index_scaled_column)))
        except ParserError as pe:
            self._log.error(pe)

    def _store_structure_observations(self):
        self._log.info("\tStoring structure observations...")
        self._store_excel_observation_array(self._excel_structure_observations)

    def _store_excel_observation_array(self, observation_tuple_list):
        self._observation_repo.begin_transaction()
        for excel_observation_tuple in observation_tuple_list:
            area = excel_observation_tuple[1]
            indicator = excel_observation_tuple[2]
            dataset_indicator = excel_observation_tuple[3] if len(excel_observation_tuple) == 4 else None
            observation = excel_observation_to_dom(excel_observation_tuple[0], area, indicator, dataset_indicator)
            observation.uri = urljoin(self._config.get("OTHERS", "HOST"), "observations/%s/%s/%s" % (
                indicator.indicator, area.iso3, observation.year.value))
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
                current_observation.rank = latest_observation.rank
            else:
                current_observation.rank = idx + 1
            latest_observation = current_observation

        return observation_list

    def _store_raw_observations(self):
        self._log.info("\tStoring raw observations...")
        self._store_excel_observation_array(self._excel_raw_observations)

    def _store_dataset_observations(self):
        self._log.info("\tStoring dataset observations...")
        self._store_excel_observation_array(self._excel_dataset_observations)


if __name__ == "__main__":
    import logging
    import configparser

    log = logging.getLogger(__name__)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console.setFormatter(formatter)
    log.addHandler(console)

    obs_repo = None
    sqlite_config = configparser.RawConfigParser()
    sqlite_config.set("CONNECTION", 'SQLITE_DB', '../../../odb2015.db')
    sqlite_config.read("sqlite_config.ini")
    indicator_repo = IndicatorRepository(False, sqlite_config)
    area_repo = AreaRepository(False, sqlite_config)

    config = configparser.RawConfigParser()
    config.read("../../../parser_config.ini")
    config.set("DATA_ACCESS", "FILE_NAME", "../../../20160128_data.xlsx")
    parser = ObservationParser(log, config, observation_repo=obs_repo, indicator_repo=indicator_repo,
                               area_repo=area_repo)

    parser.run()
