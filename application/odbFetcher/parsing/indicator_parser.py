from application.odbFetcher.parsing.excel_model.excel_indicator import ExcelIndicator
from application.odbFetcher.parsing.parser import Parser
from application.odbFetcher.parsing.utils import *
from utils import weight_to_float


class IndicatorParser(Parser):
    """
    Retrieves the indicators and their information from the structure Excel file and stores them into the database.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        super(IndicatorParser, self).__init__(log, config, area_repo, indicator_repo, observation_repo)
        self._excel_indicators = []

    def run(self):
        self._log.info("Running indicator parser")
        print "Running indicator parser"
        structure_sheet = self._initialize_structure_sheet()
        indicator_sheet = self._initialize_indicator_sheet()
        self._retrieve_indicators(structure_sheet, indicator_sheet)
        self._store_indicators()

    def _initialize_indicator_sheet(self):
        self._log.info("\tGetting indicators sheet...")
        print "\tGetting indicators sheet..."
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _initialize_structure_sheet(self):
        self._log.info("\tGetting structure indicators sheet...")
        print "\tGetting structure indicators sheet..."
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _retrieve_indicators(self, structure_sheet, indicator_sheet):
        self._retrieve_structure_indicators(structure_sheet)
        self._retrieve_primary_secondary_indicators(indicator_sheet)

    def _retrieve_structure_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving structure indicators...")
        print "\tRetrieving structure indicators..."
        code_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_CODE_COLUMN")
        name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_NAME_COLUMN")
        type_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_TYPE_COLUMN")
        weight_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_WEIGHT_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_START_ROW")
        last_subindex_code = None
        for row_number in range(start_row, indicator_sheet.nrows):
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            retrieved_weight = indicator_sheet.cell(row_number, weight_column).value
            code = retrieved_code.upper().replace(" ", "_")
            name = indicator_sheet.cell(row_number, name_column).value
            _type = retrieved_type.upper()
            index = "INDEX" if _type != 'INDEX' else None
            weight = weight_to_float(retrieved_weight)
            if _type == "SUBINDEX": last_subindex_code = code
            subindex = last_subindex_code if _type == "COMPONENT" else None
            indicator = ExcelIndicator(index=index, code=code, name=name, _type=_type,
                                       subindex=subindex, weight=weight)
            self._excel_indicators.append(indicator)

    # TODO: too much boilerplate
    def _retrieve_primary_secondary_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving primary & secondary indicators...")
        print "\tRetrieving primary & secondary indicators..."
        code_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_CODE_COLUMN")
        component_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_COMPONENT_COLUMN")
        description_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_DESCRIPTION_COLUMN")
        format_notes_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_FORMAT_NOTES_COLUMN")
        license_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_LICENSE_COLUMN")
        name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_NAME_COLUMN")
        provider_name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_PROVIDER_NAME_COLUMN")
        provider_url_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_PROVIDER_URL_COLUMN")
        range_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_RANGE_COLUMN")
        source_data_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SOURCE_DATA_COLUMN")
        source_name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SOURCE_NAME_COLUMN")
        source_url_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SOURCE_URL_COLUMN")
        subindex_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COLUMN")
        tags_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_TAGS_COLUMN")
        type_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_TYPE_COLUMN")
        units_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_UNITS_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_START_ROW")
        for row_number in range(start_row, indicator_sheet.nrows):
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            retrieved_component = indicator_sheet.cell(row_number, component_column).value
            retrieved_subindex = indicator_sheet.cell(row_number, subindex_column).value
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            _license = str_to_none(indicator_sheet.cell(row_number, license_column).value)
            _range = str_to_none(indicator_sheet.cell(row_number, range_column).value)
            _type = retrieved_type.upper()
            code = retrieved_code.upper().replace(" ", "_")
            component = retrieved_component.upper().replace(" ", "_")
            description = str_to_none(indicator_sheet.cell(row_number, description_column).value)
            format_notes = str_to_none(indicator_sheet.cell(row_number, format_notes_column).value)
            name = indicator_sheet.cell(row_number, name_column).value
            provider_name = str_to_none(indicator_sheet.cell(row_number, provider_name_column).value)
            provider_url = str_to_none(indicator_sheet.cell(row_number, provider_url_column).value)
            source_data = str_to_none(indicator_sheet.cell(row_number, source_data_column).value)
            source_name = str_to_none(indicator_sheet.cell(row_number, source_name_column).value)
            source_url = str_to_none(indicator_sheet.cell(row_number, source_url_column).value)
            subindex = retrieved_subindex.upper().replace(" ", "_")
            tags = str_to_none(indicator_sheet.cell(row_number, tags_column).value)
            units = str_to_none(indicator_sheet.cell(row_number, units_column).value)
            indicator = ExcelIndicator(index="INDEX", code=code, name=name, _type=_type,
                                       subindex=subindex, component=component,
                                       description=description, source_name=source_name, provider_name=provider_name,
                                       tags=tags, _license=_license, format_notes=format_notes, _range=_range,
                                       source_data=source_data, source_url=source_url, provider_url=provider_url,
                                       units=units)
            self._excel_indicators.append(indicator)

    def _store_indicators(self):
        """
        Before storing the indicators and their information into the database it's necessary to transform them from
        the auxiliary Excel model to the domain model.
        :return:
        """
        self._log.info("\tStoring indicators...")
        print "\tStoring indicators..."
        for excel_indicator in self._excel_indicators:
            indicator = excel_indicator_to_dom(excel_indicator)
            self._indicator_repo.insert_indicator(indicator)
