from application.a4aiFetcher.parsing.parser import Parser
from application.a4aiFetcher.parsing.utils import *
from application.a4aiFetcher.parsing.excel_model.excel_observation import ExcelObservation

__author__ = 'Rodrigo'


class GroupedObservationParser(Parser):
    """
    Retrieves the grouped observations from the data Excel file and stores them into the database.
    """

    def __init__(self, log, config):
        super(GroupedObservationParser, self).__init__(log, config)
        self._excel_grouped_observations = []

    def run(self):
        self._log.info("Running grouped observation parser")
        print "Running grouped observation parser"
        grouped_obs_sheet = self._initialize_grouped_obs_sheet()
        self._retrieve_grouped_observations(grouped_obs_sheet)
        self._store_grouped_observations()

    def _initialize_grouped_obs_sheet(self):
        self._log.info("\tGetting grouped observations sheet...")
        print "\tGetting grouped observations sheet..."
        data_file_name = self._config.get("DATA_ACCESS", "FILE_NAME")
        grouped_sheet_number = self._config.getint("GROUPED_OBSERVATIONS", "SHEET_NUMBER")
        grouped_obs_sheet = self._get_sheet(data_file_name, grouped_sheet_number)
        return grouped_obs_sheet

    def _retrieve_grouped_observations(self, grouped_obs_sheet):
        self._log.info("\tRetrieving grouped observations sheet...")
        print "\tRetrieving grouped observations sheet..."
        countries_column = self._config.getint("GROUPED_OBSERVATIONS", "COUNTRY_COLUMN")
        indicator_columns_range = self._config.get("GROUPED_OBSERVATIONS", "INDICATOR_COLUMN_RANGE").split(", ")
        indicator_names_row = self._config.getint("GROUPED_OBSERVATIONS", "INDICATOR_NAMES_ROW")
        for row_number in range(1, grouped_obs_sheet.nrows):
            country_name = grouped_obs_sheet.cell(row_number, countries_column).value
            for column_number in range(int(indicator_columns_range[0]), int(indicator_columns_range[1]) + 1):
                retrieved_indicator_code = grouped_obs_sheet.cell(indicator_names_row, column_number).value
                indicator_code = retrieved_indicator_code.upper()
                observation_value = grouped_obs_sheet.cell(row_number, column_number).value
                observation = ExcelObservation(country_name, indicator_code, observation_value)
                self._excel_grouped_observations.append(observation)

    def _store_grouped_observations(self):
        """
        Before storing the observations and their information into the database it's necessary to transform them from
        the auxiliary Excel model to the domain model.
        :return:
        """
        self._log.info("\tStoring grouped observations sheet...")
        print "\tStoring grouped observations sheet..."
        for excel_observation in self._excel_grouped_observations:
            area = self._area_repo.find_by_name(excel_observation.country_name)
            indicator = self._indicator_repo.find_indicator_by_code(excel_observation.indicator_code)
            observation = excel_observation_to_dom(excel_observation, area, indicator)
            observation_uri = self._config.get("OTHERS", "HOST") + "observations/" + indicator.indicator + "/" \
                              + area.iso3 + "/" + str(observation.year.value)
            self._observation_repo.insert_observation(observation, observation_uri=observation_uri,
                                                      area_iso3_code=area.iso3, indicator_code=indicator.indicator,
                                                      year_literal=str(observation.year.value), area_name=area.name,
                                                      indicator_name=indicator.name, republish=indicator.republish,
                                                      area_code=area.area, provider_name=indicator.provider_name,
                                                      provider_url=indicator.provider_url, short_name=area.short_name,
                                                      area_type=area.type, indicator_type=indicator.type)
