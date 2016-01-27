import ConfigParser
import logging

# from application.odbFetcher.enrichment.enricher import Enricher
# from application.odbFetcher.parsing.grouped_observation_parser import GroupedObservationParser
from application.odbFetcher.parsing.indicator_parser import IndicatorParser
# from application.odbFetcher.parsing.ranker import Ranker
from infrastructure.sql_repos.indicator_repository import IndicatorRepository

__author__ = 'Rodrigo'


def configure_log():
    _format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename="odbFetcher.log", level=logging.INFO,
                        format=_format)


def run():
    configure_log()
    log = logging.getLogger("odbFetcher")
    config = ConfigParser.RawConfigParser()
    config.read("configuration.ini")
    indicator_repo = IndicatorRepository(True, log, config)
    area_repo = None
    observation_repo = None
    parse(log, config, area_repo, indicator_repo, observation_repo)
    # rank(log, config)
    # enrich(log, config)


def parse(log, config, area_repo, indicator_repo, observation_repo):
    IndicatorParser(log, config, area_repo, indicator_repo, observation_repo).run()
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
    print "Done! :)"
