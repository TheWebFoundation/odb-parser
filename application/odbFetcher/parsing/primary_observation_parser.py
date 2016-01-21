from application.a4aiFetcher.parsing.excel_model.excel_observation import ExcelObservation
from application.a4aiFetcher.parsing.parser import Parser
from application.a4aiFetcher.parsing.utils import excel_observation_to_dom

__author__ = 'Rodrigo'


class PrimaryObservationParser(Parser):
    """
    Retrieves the primary observations from the data Excel file and stores them into the database.
    """

    def __init__(self, log, config):
        super(PrimaryObservationParser, self).__init__(log, config)
        self._excel_primary_observations = []

    def run(self):
        self._log.info("Running primary observation parser")
        print "Running primary observation parser"
        primary_obs_sheet = self._initialize_primary_obs_sheet()
        self._retrieve_primary_observations(primary_obs_sheet)
        self._store_primary_observations()

    def _initialize_primary_obs_sheet(self):
        self._log.info("\tGetting primary observations sheet...")
        print "\tGetting primary observations sheet..."
        data_file_name = self._config.get("DATA_ACCESS", "FILE_NAME")
        primary_sheet_number = self._config.getint("PRIMARY_OBSERVATIONS", "SHEET_NUMBER")
        primary_obs_sheet = self._get_sheet(data_file_name, primary_sheet_number)
        return primary_obs_sheet

    def _retrieve_primary_observations(self, primary_obs_sheet):
        self._log.info("\tRetrieving primary observations...")
        print "\tRetrieving primary observations..."
        country_column = self._config.getint("PRIMARY_OBSERVATIONS", "COUNTRY_COLUMN")
        country_start_row = self._config.getint("PRIMARY_OBSERVATIONS", "COUNTRY_START_ROW")
        indicator_codes_row = self._config.getint("PRIMARY_OBSERVATIONS", "INDICATOR_CODES_ROW")
        indicator_start_column = self._config.getint("PRIMARY_OBSERVATIONS", "INDICATOR_START_COLUMN")
        for row_number in range(country_start_row, primary_obs_sheet.nrows):
            for column_number in range(indicator_start_column, primary_obs_sheet.ncols):
                country_name = primary_obs_sheet.cell(row_number, country_column).value
                indicator_code = primary_obs_sheet.cell(indicator_codes_row, column_number).value
                observation_value = primary_obs_sheet.cell(row_number, column_number).value
                observation = ExcelObservation(country_name, indicator_code, observation_value)
                self._excel_primary_observations.append(observation)

    def _store_primary_observations(self):
        """
        Before storing the observations and their information into the database it's necessary to transform them from
        the auxiliary Excel model to the domain model.
        :return:
        """
        self._log.info("\tStoring primary observations...")
        print "\tStoring primary observations..."
        for excel_observation in self._excel_primary_observations:
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
