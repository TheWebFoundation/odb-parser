from application.odbFetcher.parsing.parser import Parser
from application.odbFetcher.parsing.utils import *
from application.odbFetcher.parsing.excel_model.excel_indicator import ExcelIndicator
from utils import weight_to_float

__author__ = 'Rodrigo'


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
        subindex_sheet = self._initialize_subindex_sheet()
        indicator_sheet = self._initialize_indicator_sheet()
        self._retrieve_indicators(subindex_sheet, indicator_sheet)
        self._store_indicators()

    def _initialize_indicator_sheet(self):
        self._log.info("\tGetting indicators sheet...")
        print "\tGetting indicators sheet..."
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _initialize_subindex_sheet(self):
        self._log.info("\tGetting subindex indicators sheet...")
        print "\tGetting subindex indicators sheet..."
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _retrieve_indicators(self, subindex_sheet, indicator_sheet):
        self._retrieve_index_indicator(indicator_sheet)
        self._retrieve_subindex_indicators(subindex_sheet)
        self._retrieve_primary_secondary_indicators(indicator_sheet)

    def _retrieve_index_indicator(self, indicator_sheet):
        self._log.info("\tRetrieving index indicator...")
        print "\tRetrieving index indicator..."
        # FIXME: source_name?
        indicator = ExcelIndicator(index_code=None, code="INDEX", name="Index", _type="INDEX", subindex_code=None,
                                   component_code=None, description=None, source_name="ODB report",
                                   provider_name="Web Foundation", tags=None, weight=None)
        self._excel_indicators.append(indicator)

    def _retrieve_subindex_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving subindex indicators...")
        print "\tRetrieving subindex indicators..."
        code_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_CODE_COLUMN")
        name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_NAME_COLUMN")
        type_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_TYPE_COLUMN")
        weight_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_WEIGHT_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_START_ROW")
        last_subindex_code = None
        for row_number in range(start_row, indicator_sheet.nrows):
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            code = retrieved_code.upper().replace(" ", "_")
            name = indicator_sheet.cell(row_number, name_column).value
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            _type = retrieved_type.upper()
            retrieved_weight = indicator_sheet.cell(row_number, weight_column).value
            weight = weight_to_float(retrieved_weight)
            if _type == "SUBINDEX": last_subindex_code = code
            subindex_code = last_subindex_code if _type == "COMPONENT" else None
            # FIXME: Provider and source data?
            indicator = ExcelIndicator(index_code="INDEX", code=code, name=name, _type=_type,
                                       subindex_code=subindex_code, component_code=None, description=None,
                                       source_name=None, provider_name=None, tags=None, weight=weight)
            self._excel_indicators.append(indicator)

    def _retrieve_primary_secondary_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving primary & secondary indicators...")
        print "\tRetrieving primary & secondary indicators..."
        code_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_CODE_COLUMN")
        name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_NAME_COLUMN")
        type_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_TYPE_COLUMN")
        subindex_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COLUMN")
        component_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_COMPONENT_COLUMN")
        description_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_DESCRIPTION_COLUMN")
        source_name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SOURCE_NAME_COLUMN")
        provider_name_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_PROVIDER_NAME_COLUMN")
        tags_column = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_TAGS_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_START_ROW")
        for row_number in range(start_row, indicator_sheet.nrows):
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            code = retrieved_code.upper().replace(" ", "_")
            name = indicator_sheet.cell(row_number, name_column).value
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            _type = retrieved_type.upper()
            retrieved_subindex_code = indicator_sheet.cell(row_number, subindex_column).value
            subindex_code = retrieved_subindex_code.upper().replace(" ", "_")
            retrieved_component_code = indicator_sheet.cell(row_number, component_column).value
            component_code = retrieved_component_code.upper().replace(" ", "_")
            description = str_to_none(indicator_sheet.cell(row_number, description_column).value)
            source_name = str_to_none(indicator_sheet.cell(row_number, source_name_column).value)
            provider_name = str_to_none(indicator_sheet.cell(row_number, provider_name_column).value)
            tags = str_to_none(indicator_sheet.cell(row_number, tags_column).value)
            weight = None
            indicator = ExcelIndicator(index_code="INDEX", code=code, name=name, _type=_type,
                                       subindex_code=subindex_code, component_code=component_code,
                                       description=description, source_name=source_name, provider_name=provider_name,
                                       tags=tags, weight=weight)
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
