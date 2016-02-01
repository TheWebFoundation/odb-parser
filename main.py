import configparser
import logging

from application.odbFetcher.parsing.area_parser import AreaParser
from application.odbFetcher.parsing.indicator_parser import IndicatorParser
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository


def configure_log():
    _format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename="odbFetcher.log", level=logging.INFO,
                        format=_format)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def run():
    configure_log()
    log = logging.getLogger("odbFetcher")
    config = configparser.RawConfigParser()
    config.read("configuration.ini")
    indicator_repo = IndicatorRepository(True, log, config)
    area_repo = AreaRepository(True, log, config)
    observation_repo = None
    parse(log, config, area_repo, indicator_repo, observation_repo)
    # rank(log, config)
    # enrich(log, config)


def parse(log, config, area_repo, indicator_repo, observation_repo):
    IndicatorParser(log, config, area_repo, indicator_repo, observation_repo).run()
    AreaParser(log, config, area_repo, indicator_repo, observation_repo).run()
    # SecondaryObservationParser(log, config).run()
    # PrimaryObservationParser(log, config).run()
    # GroupedObservationParser(log, config).run()


# def rank(log, config):
#     Ranker(log, config).run()
#
#
# def enrich(log, config):
#     Enricher(log, config).run()

if __name__ == "__main__":
    run()
    print("Done! :)")
