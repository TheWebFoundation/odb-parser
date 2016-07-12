import json
import logging
import os
from operator import itemgetter

from application.odbFetcher.enrichment.rest_client import get_json


def configure_log():
    _format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename="odbFetcher.log", level=logging.DEBUG,
                        format=_format)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def generateOdbJson(log):
    log.info('Generating ODB data per year documents')
    uri = "http://localhost:5000/years"
    response = get_json(uri, {"format": "json"})
    years = [y['value'] for y in response['data']]
    for year in years:
        log.info('\tRetrieving ODB data for %s' % (year,))
        uri = "http://localhost:5000/indexObservations/%s" % (year,)
        filename = os.path.join(os.path.dirname(__file__), "json", "odb_%s.json" % (year,))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        response = get_json(uri, {"format": "json"})
        json.dump(response['data'], open(filename, "w"), ensure_ascii=False)


def generateCountriesJson(log):
    log.info('Generating countries document')
    uri = "http://localhost:5000/areas/regions"
    countries_filename = os.path.join(os.path.dirname(__file__), "json", "countries.json")
    regions_filename = os.path.join(os.path.dirname(__file__), "json", "regions.json")
    os.makedirs(os.path.dirname(countries_filename), exist_ok=True)
    response = get_json(uri, {"format": "json"})
    regions = []
    countries = []
    for region in sorted(response['data'], key=itemgetter('short_name')):
        regions.append({k: v for (k, v) in region.items() if k in ['iso3', 'name', 'short_name']})
        countries.extend(region['countries'])
    countries = sorted(countries, key=itemgetter('short_name'))
    json.dump(countries, open(countries_filename, "w"), ensure_ascii=False)
    json.dump(regions, open(regions_filename, "w"), ensure_ascii=False)


def generateIndicatorsJson(log):
    log.info('Generating indicators document')
    uri = "http://localhost:5000/indicators_flattened"
    filename = os.path.join(os.path.dirname(__file__), "json", "indicators.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = get_json(uri, {"format": "json"})
    json.dump(response['data'], open(filename, "w"), ensure_ascii=False)


def generateMetaIndicatorsJson(log):
    log.info('Generating meta indicators document')
    uri = "http://localhost:5000/indicators_meta"
    filename = os.path.join(os.path.dirname(__file__), "json", "indicators_meta.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = get_json(uri, {"format": "json"})
    json.dump(response['data'], open(filename, "w"), ensure_ascii=False)

def generateOdbPerCountryJson(log):
    log.info('Generating ODB data per country documents')
    uri = "http://localhost:5000/areas/countries"
    response = get_json(uri, {"format": "json"})
    countries = [c['iso3'] for c in response['data']]
    for country in countries:
        log.info('\tRetrieving ODB data for ' + country)
        uri = "http://localhost:5000/countryObservations/%s" % (country,)
        filename = os.path.join(os.path.dirname(__file__), "json", "odb_%s.json" % (country,))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        response = get_json(uri, {"format": "json"})
        json.dump(response['data'], open(filename, "w"), ensure_ascii=False)

def generateYearsWithIndicatorDataJson(log):
    log.info('Generating years with indicator data document')
    uri = "http://localhost:5000/yearsWithIndicatorData"
    filename = os.path.join(os.path.dirname(__file__), "json", "years_with_data.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = get_json(uri, {"format": "json"})
    json.dump(response['data'], open(filename, "w"), ensure_ascii=False)


def generateStatsJson(log):
    log.info('Generating stats document')
    filename = os.path.join(os.path.dirname(__file__), "json", "stats.json")

    uri = "http://localhost:5000/years"
    response = get_json(uri, {"format": "json"})
    years = [y['value'] for y in response["data"]]

    data = {}
    for year in years:
        uri = "http://localhost:5000/indexStats/%s" % (year,)
        response = get_json(uri, {"format": "json"})
        data[year] = response['data']['stats']

    json.dump(data, open(filename, "w"), ensure_ascii=False)

def run():
    configure_log()
    log = logging.getLogger("odbFetcher")
    generateIndicatorsJson(log)
    generateMetaIndicatorsJson(log)
    generateCountriesJson(log)
    generateOdbJson(log)
    generateOdbPerCountryJson(log)
    generateYearsWithIndicatorDataJson(log)
    generateStatsJson(log)
    log.info('Done')


if __name__ == "__main__":
    run()
    print("Done! :)")
