import json
from collections import defaultdict

from application.odbFetcher.enrichment.indicator_data import IndicatorData
from infrastructure.mongo_repos.area_repository import AreaRepository
from rest_client import *


class Enricher(object):
    """
    This class is responsible for enriching the areas documents of the database with further information. Note that,
    given the variety of data sources and the different ways of them of providing information, it's necessary to
    implement a function for each one. Currently, the enrichment is done from the information provided by two data
    sources: the World Bank and the International Telecommunication Union (ITU)
    """

    def __init__(self, log, config):
        self._log = log
        self._config = config
        self._area_repo = AreaRepository(self._config.get("CONNECTION", "MONGO_IP"))
        self._retrieved_data = defaultdict(list)

    def run(self):
        self._log.info("Enriching areas")
        print "Enriching areas"
        self._retrieve_world_bank_indicators()
        self._retrieve_itu_indicators()
        self._enrich()

    def _retrieve_world_bank_indicators(self):
        """
        The data provided by the World Bank is available through an API that returns JSON documents. This data will be
        modeled by the auxiliary class IndicatorData for its posterior storage in the database.
        :return:
        """
        self._log.info("\tRetrieving data from World Bank")
        print "\tRetrieving data from World Bank"
        uri_pattern = self._config.get("ENRICHMENT", "WB_INDICATOR_URL_QUERY_PATTERN")
        indicator_codes = self._config.get("ENRICHMENT", "WB_INDICATOR_CODES").split(", ")
        provider_name = self._config.get("ENRICHMENT", "WB_PROVIDER_NAME")
        areas = self._area_repo.find_countries("iso3")
        for indicator_code in indicator_codes:
            provider_url = self._config.get("ENRICHMENT", "WB_PROVIDER_URL_PATTERN").replace("{INDICATOR_CODE}",
                                                                                             indicator_code)
            for area in areas:
                uri = uri_pattern.replace("{ISO3}", area.iso3).replace("{INDICATOR_CODE}", indicator_code)
                response = get_json(uri, {"format": "json"})
                value = None
                year_index = 0
                while value is None and year_index < len(response[1]):
                    last_year_data = response[1][year_index]
                    value = last_year_data['value']
                    year_index += 1
                if value is not None:
                    indicator_data = IndicatorData(indicator_code.replace(".", "_"), last_year_data['date'],
                                                   last_year_data['value'], provider_name, provider_url)
                    self._retrieved_data[area.iso3].append(indicator_data)
                    print "\t\t" + area.iso3 + " " + indicator_code + " " + last_year_data['date'] + "-->" + \
                          str(last_year_data['value'])
                else:
                    print "\t\t" + area.iso3 + " has no values"
                    self._log.warning("\t\t" + area.iso3 + " has no values")

    def _retrieve_itu_indicators(self):
        """
        The data provided by the ITU is retrieved from two JSON files; one per indicator. Note that these documents
        where previously obtained by parsing a PDF report, wich is available through the ITU_PROVIDER_URL value in
        the config file. This data will be modeled by the auxiliary class IndicatorData for its posterior storage
        in the database.
        :return:
        """
        self._log.info("\tRetrieving data from ITU")
        print "\tRetrieving data from ITU"
        areas = self._area_repo.find_countries("iso3")
        file_names = self._config.get("ENRICHMENT", "ITU_FILE_NAMES").split(", ")
        provider_name = self._config.get("ENRICHMENT", "ITU_PROVIDER_NAME")
        provider_url = self._config.get("ENRICHMENT", "ITU_PROVIDER_URL")
        year = self._config.get("ENRICHMENT", "ITU_DATA_YEAR")
        for file_name in file_names:
            json_data = open(file_name)
            data = json.load(json_data)
            print "\t\t" + file_name
            for area in areas:
                found = False
                for data_element in data:
                    if area.name == data_element['country'].replace("_", " "):
                        found = True
                        for key in data_element:
                            if key != "country" and data_element[key] != "-":
                                indicator_data = IndicatorData(key, year, data_element[key], provider_name,
                                                               provider_url)
                                self._retrieved_data[area.iso3].append(indicator_data)
                if not found:
                    print "\t\t\t" + area.name + " not found"
                    self._log.warning("\t\t" + area.iso3 + " not found in " + file_name)
            json_data.close()

    def _enrich(self):
        self._log.info("\tUpdating areas")
        print "\tUpdating areas"
        areas = self._area_repo.find_countries("iso3")
        for area in areas:
            print "\t\t" + area.iso3
            data = self._retrieved_data[area.iso3]
            for data_element in data:
                print "\t\t\t" + data_element.indicator_code + " " + data_element.year + " " + data_element.value
            self._area_repo.enrich_country(area.iso3, data)
