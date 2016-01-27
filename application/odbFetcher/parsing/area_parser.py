from application.odbFetcher.parsing.excel_model.excel_area import ExcelArea
from application.odbFetcher.parsing.parser import Parser

__author__ = 'Rodrigo'

# FIXME: move to configuration
FAKE_ISO = {
    u'Latin America & Caribbean': {
        'iso2': ':L',
        'iso3': ':LA'
    },
    u'East Asia & Pacific': {
        'iso2': ':P',
        'iso3': ':PA'
    },
    u'Europe & Central Asia': {
        'iso2': ':E',
        'iso3': ':EU'
    },
    u'Middle East & North Africa': {
        'iso2': ':M',
        'iso3': ':ME'
    },
    u'South Asia': {
        'iso2': ':S',
        'iso3': ':SA'
    },
    u'Sub-Saharan Africa': {
        'iso2': ':A',
        'iso3': ':AF'
    },
    u'North America': {
        'iso2': ':N',
        'iso3': ':NA'
    }
}


class AreaParser(Parser):
    """
    Retrieves the areas and their information from the structure Excel file and stores them into the database.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        super(AreaParser, self).__init__(log, config, area_repo, indicator_repo, observation_repo)
        self._excel_countries = []
        self._excel_regions = set()

    def run(self):
        self._log.info("Running area parser")
        print "Running area parser"
        area_sheet = self._initialize_area_sheet()
        self._retrieve_areas(area_sheet)
        self._store_areas()

    def _initialize_area_sheet(self):
        self._log.info("\tGetting area sheet...")
        print "\tGetting area sheet..."
        structure_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("STRUCTURE_ACCESS", "AREA_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(structure_file_name, indicator_sheet_number)
        return indicator_sheet

    def _retrieve_areas(self, area_sheet):
        self._retrieve_regions(area_sheet)
        self._retrieve_countries(area_sheet)

    def _build_fake_iso_code(self, region_name):
        if not FAKE_ISO.has_key(region_name):
            self._log.error("\t%s doesn't have a corresponding ISO", region_name)
            print "\t", region_name, "doesn't have a corresponding ISO"
            return None

        return FAKE_ISO[region_name]

    def _retrieve_regions(self, area_sheet):
        self._log.info("\tRetrieving regions...")
        print "\tRetrieving regions..."

        region_column = self._config.getint("STRUCTURE_ACCESS", "AREA_REGION_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "AREA_START_ROW")
        for row_number in range(start_row, area_sheet.nrows):
            region = area_sheet.cell(row_number, region_column).value
            iso_codes = self._build_fake_iso_code(region)
            if iso_codes is not None:
                region = ExcelArea(iso_codes['iso2'], iso_codes['iso3'], region, None)
                self._excel_regions.add(region)

    def _retrieve_countries(self, area_sheet):
        self._log.info("\tRetrieving countries...")
        print "\tRetrieving countries..."

        iso2_column = self._config.getint("STRUCTURE_ACCESS", "AREA_ISO2_COLUMN")
        iso3_column = self._config.getint("STRUCTURE_ACCESS", "AREA_ISO3_COLUMN")
        name_column = self._config.getint("STRUCTURE_ACCESS", "AREA_NAME_COLUMN")
        region_column = self._config.getint("STRUCTURE_ACCESS", "AREA_REGION_COLUMN")
        start_row = self._config.getint("STRUCTURE_ACCESS", "AREA_START_ROW")
        for row_number in range(start_row, area_sheet.nrows):
            region = area_sheet.cell(row_number, region_column).value
            iso2 = area_sheet.cell(row_number, iso2_column).value
            iso3 = area_sheet.cell(row_number, iso3_column).value
            name = area_sheet.cell(row_number, name_column).value
            region = ExcelArea(iso2, iso3, name, region)
            self._excel_countries.append(region)

    def _store_areas(self):
        """
        Before storing the areas and their information into the database it's necessary to transform them from
        the auxiliary Excel model to the domain model.
        :return:
        """
        self._log.info("\tStoring areas...")
        print "\tStoring areas..."
        self._store_regions()
        self._store_countries()

    def _store_regions(self):
        for excel_region in self._excel_regions:
            # Transform to domain and insert via repo
            pass

    def _store_countries(self):
        for excel_country in self._excel_countries:
            # Transform to domain and insert via repo
            pass


if __name__ == "__main__":
    import logging
    import ConfigParser

    logger = logging.getLogger(__name__)
    config = ConfigParser.RawConfigParser()
    config.add_section("STRUCTURE_ACCESS")
    config.set("STRUCTURE_ACCESS", "FILE_NAME", "../../../20160121_data.xlsx")
    config.set("STRUCTURE_ACCESS", "AREA_SHEET_NUMBER", "2")
    config.set("STRUCTURE_ACCESS", "AREA_START_ROW", "1")
    config.set("STRUCTURE_ACCESS", "AREA_ISO2_COLUMN", "0")
    config.set("STRUCTURE_ACCESS", "AREA_ISO3_COLUMN", "1")
    config.set("STRUCTURE_ACCESS", "AREA_NAME_COLUMN", "2")
    config.set("STRUCTURE_ACCESS", "AREA_REGION_COLUMN", "5")

    parser = AreaParser(logger, config)
    parser.run()

    print "Regions are:", [str(region) for region in parser._excel_regions]
    print "Countries are:", [str(country) for country in parser._excel_countries]
