import json
from collections import defaultdict

from odb.domain.model.area.area_info import AreaInfo
from .rest_client import *


class Enricher(object):
    """
    This class is responsible for enriching the areas documents of the database with further information. Note that,
    given the variety of data sources and the different ways of them of providing information, it's necessary to
    implement a function for each one. Currently, the enrichment is done from the information provided by two data
    sources: the World Bank and the International Telecommunication Union (ITU)
    """

    def __init__(self, log, config, area_repo):
        self._log = log
        self._config = config
        self._area_repo = area_repo
        self._retrieved_area_info = defaultdict(list)
        self._retrieved_search_data = []

    def run(self):
        self._log.info("Enriching areas")
        # self._retrieve_world_bank_indicators()
        self._retrieve_search_data()
        self._enrich()

    def _retrieve_world_bank_indicators(self):
        """
        The data provided by the World Bank is available through an API that returns JSON documents. This data will be
        modeled by the auxiliary class IndicatorData for its posterior storage in the database.
        :return:
        """
        self._log.info("\tRetrieving data from World Bank")
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
                    area_info = AreaInfo(indicator_code=indicator_code.replace(".", "_"), year=last_year_data['date'],
                                         value=last_year_data['value'], provider_name=provider_name,
                                         provider_url=provider_url)
                    self._retrieved_area_info[area.iso3].append(area_info)
                else:
                    self._log.warning("\t\t" + area.iso3 + " has no values")

    def _retrieve_search_data(self):
        self._log.info("\tRetrieving search data")
        self._retrieved_search_data = json.load(open('search.json'))

    def _enrich(self):
        self._log.info("\tUpdating areas")
        self._area_repo.begin_transaction()

        for iso3, area_info_dict in self._retrieved_area_info.items():
            area_info = area_info_dict
            self._area_repo.upsert_area_info(iso3, area_info, commit=False)

        for iso3, search in self._retrieved_search_data.items():
            self._area_repo.update_search_data(iso3, search, commit=False)
        self._area_repo.commit_transaction()
