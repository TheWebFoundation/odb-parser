import configparser
import logging

from application.odbFetcher.parsing.area_parser import AreaParser
from application.odbFetcher.parsing.indicator_parser import IndicatorParser
from application.odbFetcher.parsing.observation_parser import ObservationParser
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.observation_repository import ObservationRepository


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
    observation_repo = ObservationRepository(True, area_repo, indicator_repo, log, config)
    parse(log, config, area_repo, indicator_repo, observation_repo)
    # rank(log, config)
    # enrich(log, config)
    log.info('Done')


def parse(log, config, area_repo, indicator_repo, observation_repo):
    IndicatorParser(log, config, area_repo, indicator_repo, observation_repo).run()
    AreaParser(log, config, area_repo, indicator_repo, observation_repo).run()
    ObservationParser(log, config, area_repo, indicator_repo, observation_repo).run()
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
