from urllib.parse import urljoin

from application.odbFetcher.parsing.excel_model.excel_indicator import ExcelIndicator
from application.odbFetcher.parsing.parser import Parser
from application.odbFetcher.parsing.utils import *
from .utils import weight_to_float


class IndicatorParser(Parser):
    """
    Retrieves the indicators and their information from the structure Excel file and stores them into the database.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        super(IndicatorParser, self).__init__(log, config, area_repo, indicator_repo, observation_repo)
        self._excel_indicators = []

    def run(self):
        self._log.info("Running indicator parser")
        structure_sheet = self._initialize_structure_sheet()
        indicator_sheet = self._initialize_indicator_sheet()
        self._retrieve_indicators(structure_sheet, indicator_sheet)
        self._store_indicators()

    def _initialize_indicator_sheet(self):
        self._log.info("\tGetting indicators sheet...")
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _initialize_structure_sheet(self):
        self._log.info("\tGetting structure indicators sheet...")
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _retrieve_indicators(self, structure_sheet, indicator_sheet):
        self._retrieve_structure_indicators(structure_sheet)
        self._retrieve_primary_secondary_indicators(indicator_sheet)

    def _retrieve_structure_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving structure indicators...")
        code_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_CODE_COLUMN"))
        name_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_NAME_COLUMN"))
        short_name_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SHORT_NAME_COLUMN"))
        type_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_TYPE_COLUMN"))
        weight_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_WEIGHT_COLUMN"))
        range_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_RANGE_COLUMN"))
        provider_name_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_PROVIDER_NAME_COLUMN"))
        provider_url_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_PROVIDER_URL_COLUMN"))
        source_data_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SOURCE_DATA_COLUMN"))
        source_name_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SOURCE_NAME_COLUMN"))
        source_url_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_SOURCE_URL_COLUMN"))
        license_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_LICENSE_COLUMN"))
        format_notes_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_FORMAT_NOTES_COLUMN"))
        description_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_DESCRIPTION_COLUMN"))
        units_column = get_column_number(
            self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_UNITS_COLUMN"))
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COMPONENT_START_ROW")
        last_subindex_code = None
        last_index_code = None
        for row_number in range(start_row, indicator_sheet.nrows):
            _license = str_to_none(indicator_sheet.cell(row_number, license_column).value)
            _range = str_to_none(indicator_sheet.cell(row_number, range_column).value)
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            _type = retrieved_type.upper()
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            code = retrieved_code.upper().replace(" ", "_")
            description = indicator_sheet.cell(row_number, description_column).value
            format_notes = str_to_none(indicator_sheet.cell(row_number, format_notes_column).value)
            name = indicator_sheet.cell(row_number, name_column).value
            provider_name = str_to_none(indicator_sheet.cell(row_number, provider_name_column).value)
            provider_url = str_to_none(indicator_sheet.cell(row_number, provider_url_column).value)
            retrieved_weight = indicator_sheet.cell(row_number, weight_column).value
            retrieved_short_name = indicator_sheet.cell(row_number, short_name_column).value
            short_name = retrieved_short_name.upper().replace(" ", "_")
            source_data = str_to_none(indicator_sheet.cell(row_number, source_data_column).value)
            source_name = str_to_none(indicator_sheet.cell(row_number, source_name_column).value)
            source_url = str_to_none(indicator_sheet.cell(row_number, source_url_column).value)
            units = str_to_none(indicator_sheet.cell(row_number, units_column).value)
            index = last_index_code if _type != 'INDEX' else None
            weight = weight_to_float(retrieved_weight)
            last_subindex_code = code if _type == "SUBINDEX" else last_subindex_code
            last_index_code = code if _type == "INDEX" else last_index_code
            subindex = last_subindex_code if _type == "COMPONENT" else None
            indicator = ExcelIndicator(index=index, code=code, name=name, _type=_type, short_name=short_name,
                                       subindex=subindex, weight=weight, _range=_range, description=description,
                                       format_notes=format_notes, provider_name=provider_name,
                                       provider_url=provider_url, source_data=source_data, source_name=source_name,
                                       source_url=source_url, _license=_license, units=units)
            self._excel_indicators.append(indicator)

    def _retrieve_primary_secondary_indicators(self, indicator_sheet):
        self._log.info("\tRetrieving primary & secondary indicators...")
        index = [i for i in self._excel_indicators if i.is_index()][0]
        code_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_CODE_COLUMN"))
        component_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_COMPONENT_COLUMN"))
        description_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_DESCRIPTION_COLUMN"))
        format_notes_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_FORMAT_NOTES_COLUMN"))
        license_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_LICENSE_COLUMN"))
        name_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_NAME_COLUMN"))
        provider_name_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_PROVIDER_NAME_COLUMN"))
        provider_url_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_PROVIDER_URL_COLUMN"))
        range_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_RANGE_COLUMN"))
        source_data_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_SOURCE_DATA_COLUMN"))
        source_name_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_SOURCE_NAME_COLUMN"))
        source_url_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_SOURCE_URL_COLUMN"))
        subindex_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_SUBINDEX_COLUMN"))
        tags_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_TAGS_COLUMN"))
        type_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_TYPE_COLUMN"))
        units_column = get_column_number(self._config.get("STRUCTURE_ACCESS", "INDICATOR_UNITS_COLUMN"))
        start_row = self._config.getint("STRUCTURE_ACCESS", "INDICATOR_START_ROW")
        for row_number in range(start_row, indicator_sheet.nrows):
            retrieved_code = indicator_sheet.cell(row_number, code_column).value
            retrieved_component = indicator_sheet.cell(row_number, component_column).value
            retrieved_subindex = indicator_sheet.cell(row_number, subindex_column).value
            retrieved_type = indicator_sheet.cell(row_number, type_column).value
            _license = str_to_none(indicator_sheet.cell(row_number, license_column).value)
            _range = str_to_none(indicator_sheet.cell(row_number, range_column).value)
            _type = retrieved_type.upper()
            code = retrieved_code.strip().upper().replace(" ", "_")
            component = retrieved_component.strip().upper().replace(" ", "_")
            if not [i for i in self._excel_indicators if i.code == component]:
                self._log.warn("No corresponding component %s found in the structure sheet while parsing %s" % (
                    component, indicator_sheet.name))
            description = str_to_none(indicator_sheet.cell(row_number, description_column).value)
            format_notes = str_to_none(indicator_sheet.cell(row_number, format_notes_column).value)
            name = indicator_sheet.cell(row_number, name_column).value
            provider_name = str_to_none(indicator_sheet.cell(row_number, provider_name_column).value)
            provider_url = str_to_none(indicator_sheet.cell(row_number, provider_url_column).value)
            source_data = str_to_none(indicator_sheet.cell(row_number, source_data_column).value)
            source_name = str_to_none(indicator_sheet.cell(row_number, source_name_column).value)
            source_url = str_to_none(indicator_sheet.cell(row_number, source_url_column).value)
            subindex = retrieved_subindex.strip().upper().replace(" ", "_")
            if not [i for i in self._excel_indicators if i.code == subindex]:
                self._log.warn("No corresponding subindex %s found in the structure sheet while parsing %s" % (
                    subindex, indicator_sheet.name))
            tags = str_to_none(indicator_sheet.cell(row_number, tags_column).value)
            units = str_to_none(indicator_sheet.cell(row_number, units_column).value)
            indicator = ExcelIndicator(index=index.code, code=code, name=name, _type=_type,
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
        self._indicator_repo.begin_transaction()
        for excel_indicator in self._excel_indicators:
            indicator = excel_indicator_to_dom(excel_indicator)
            indicator.uri = urljoin(self._config.get("OTHERS", "HOST"), indicator.indicator)
            self._indicator_repo.insert_indicator(indicator, commit=False)
        self._indicator_repo.commit_transaction()
