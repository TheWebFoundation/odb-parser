import logging
import ConfigParser
# from application.odbFetcher.enrichment.enricher import Enricher
# from application.odbFetcher.parsing.grouped_observation_parser import GroupedObservationParser
from application.odbFetcher.parsing.indicator_parser import IndicatorParser
from application.odbFetcher.parsing.primary_observation_parser import PrimaryObservationParser
# from application.odbFetcher.parsing.ranker import Ranker
from application.odbFetcher.parsing.secondary_observation_parser import SecondaryObservationParser

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
    parse(log, config)
    # rank(log, config)
    # enrich(log, config)


def parse(log, config):
    IndicatorParser(log, config).run()
    # SecondaryObservationParser(log, config).run()
    PrimaryObservationParser(log, config).run()
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
