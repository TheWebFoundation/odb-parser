import json
import logging
import os

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
    uri = "http://localhost:5000/areas/countries"
    filename = os.path.join(os.path.dirname(__file__), "json", "countries.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = get_json(uri, {"format": "json"})
    json.dump(response['data'], open(filename, "w"), ensure_ascii=False)


def generateIndicatorsJson(log):
    log.info('Generating indicators document')
    uri = "http://localhost:5000/indicators"
    filename = os.path.join(os.path.dirname(__file__), "json", "indicators.json")
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


def run():
    configure_log()
    log = logging.getLogger("odbFetcher")
    generateIndicatorsJson(log)
    generateCountriesJson(log)
    generateOdbJson(log)
    generateOdbPerCountryJson(log)
    log.info('Done')


if __name__ == "__main__":
    run()
    print("Done! :)")
