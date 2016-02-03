from application.odbFetcher.parsing.excel_model.excel_area import ExcelArea
from application.odbFetcher.parsing.parser import Parser
from application.odbFetcher.parsing.utils import excel_region_to_dom, excel_country_to_dom, str_to_none, \
    is_not_empty

# FIXME: move to configuration
# If handcrafted iso codes then we need a matching function between names and codes (or include everything in the sheet)
# Otherwise we could just auto-increment
FAKE_ISO = {
    'latin america & caribbean': {
        'iso2': ':L',
        'iso3': ':LA'
    },
    'east asia & pacific': {
        'iso2': ':P',
        'iso3': ':PA'
    },
    'europe & central asia': {
        'iso2': ':E',
        'iso3': ':EU'
    },
    'middle east & north africa': {
        'iso2': ':M',
        'iso3': ':ME'
    },
    'south asia': {
        'iso2': ':S',
        'iso3': ':SA'
    },
    'sub-saharan africa': {
        'iso2': ':A',
        'iso3': ':AF'
    },
    'north america': {
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
        self._excel_countries = None
        self._excel_regions = None

    def run(self):
        self._log.info("Running area parser")
        area_sheet = self._initialize_area_sheet()
        self._retrieve_areas(area_sheet)
        self._store_areas()

    def _initialize_area_sheet(self):
        self._log.info("\tGetting area sheet...")
        area_file_name = self._config.get("STRUCTURE_ACCESS", "FILE_NAME")
        indicator_sheet_number = self._config.getint("AREA_ACCESS", "AREA_SHEET_NUMBER")
        indicator_sheet = self._get_sheet(area_file_name, indicator_sheet_number)
        return indicator_sheet

    def _retrieve_areas(self, area_sheet):
        self._excel_regions = self._retrieve_regions(area_sheet)
        self._excel_countries = self._retrieve_countries(area_sheet, self._excel_regions)

    def _build_fake_iso_code(self, region_name):
        if region_name.lower() not in FAKE_ISO:
            self._log.error("\t%s doesn't have a corresponding ISO", region_name)
            return None

        return FAKE_ISO[region_name.lower()]

    def _retrieve_regions(self, area_sheet):
        self._log.info("\tRetrieving regions...")

        region_set = set()

        region_column = self._config.getint("AREA_ACCESS", "AREA_REGION_COLUMN")
        start_row = self._config.getint("AREA_ACCESS", "AREA_START_ROW")
        for row_number in range(start_row, area_sheet.nrows):
            region = area_sheet.cell(row_number, region_column).value
            iso_codes = self._build_fake_iso_code(region)
            if iso_codes is not None:
                region = ExcelArea(iso2=iso_codes['iso2'], iso3=iso_codes['iso3'], name=region, region=None)
                region_set.add(region)

        return region_set

    def _retrieve_countries(self, area_sheet, regions):
        self._log.info("\tRetrieving countries...")

        country_list = []

        iso2_column = self._config.getint("AREA_ACCESS", "AREA_ISO2_COLUMN")
        iso3_column = self._config.getint("AREA_ACCESS", "AREA_ISO3_COLUMN")
        name_column = self._config.getint("AREA_ACCESS", "AREA_NAME_COLUMN")
        region_column = self._config.getint("AREA_ACCESS", "AREA_REGION_COLUMN")
        income_column = self._config.getint("AREA_ACCESS", "AREA_INCOME_COLUMN")
        hdi_rank_column = self._config.getint("AREA_ACCESS", "AREA_HDI_RANK_COLUMN")
        g20_column = self._config.getint("AREA_ACCESS", "AREA_G20_COLUMN")
        g7_column = self._config.getint("AREA_ACCESS", "AREA_G7_COLUMN")
        iodch_column = self._config.getint("AREA_ACCESS", "AREA_IODCH_COLUMN")
        oecd_column = self._config.getint("AREA_ACCESS", "AREA_OECD_COLUMN")
        cluster_group_column = self._config.getint("AREA_ACCESS", "AREA_CLUSTER_GROUP_COLUMN")
        start_row = self._config.getint("AREA_ACCESS", "AREA_START_ROW")
        for row_number in range(start_row, area_sheet.nrows):
            region_name = area_sheet.cell(row_number, region_column).value
            region = next((r for r in regions if region_name.lower() == r.name.lower()), None)
            iso2 = area_sheet.cell(row_number, iso2_column).value
            iso3 = area_sheet.cell(row_number, iso3_column).value
            name = area_sheet.cell(row_number, name_column).value
            income = str_to_none(area_sheet.cell(row_number, income_column).value.replace('-', ' '))
            hdi_rank = str_to_none(area_sheet.cell(row_number, hdi_rank_column).value)
            g20 = is_not_empty(area_sheet.cell(row_number, g20_column).value)
            g7 = is_not_empty(area_sheet.cell(row_number, g7_column).value)
            iodch = is_not_empty(area_sheet.cell(row_number, iodch_column).value)
            oecd = is_not_empty(area_sheet.cell(row_number, oecd_column).value)
            cluster_group = str_to_none(area_sheet.cell(row_number, cluster_group_column).value.replace('-', ' '))
            country = ExcelArea(iso2=iso2, iso3=iso3, name=name, region=region.iso3, income=income, hdi_rank=hdi_rank,
                                g20=g20, g7=g7, iodch=iodch, oecd=oecd, cluster_group=cluster_group)
            country_list.append(country)

        return country_list

    def _store_areas(self):
        """
        Before storing the areas and their information into the database it's necessary to transform them from
        the auxiliary Excel model to the domain model.
        :return:
        """
        self._log.info("\tStoring areas...")
        self._area_repo.begin_transaction()
        self._store_regions()
        self._store_countries()
        self._area_repo.commit_transaction()

    def _store_regions(self):
        for excel_region in self._excel_regions:
            region = excel_region_to_dom(excel_region)
            self._area_repo.insert_region(region, commit=False)

    def _store_countries(self):
        for excel_country in self._excel_countries:
            country = excel_country_to_dom(excel_country)
            self._area_repo.insert_country(country, commit=False)


if __name__ == "__main__":
    import logging
    import configparser
    from infrastructure.sql_repos.area_repository import AreaRepository

    log = logging.getLogger(__name__)
    config = configparser.RawConfigParser()
    config.read("../../../configuration.ini")
    config.set("CONNECTION", 'SQLITE_DB', '../../../odb2015.db')
    config.set("STRUCTURE_ACCESS", "FILE_NAME", "../../../20160128_data.xlsx")

    area_repo = AreaRepository(False, log, config)
    parser = AreaParser(log, config, area_repo=area_repo)

    parser.run()

    print("Regions are:", [str(region) for region in parser._excel_regions])
    print("Countries are:", [str(country) for country in parser._excel_countries])
