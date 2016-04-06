import configparser
import logging
import os

from application.odbFetcher.enrichment.enricher import Enricher
from application.odbFetcher.parsing.area_parser import AreaParser
from application.odbFetcher.parsing.indicator_parser import IndicatorParser
from application.odbFetcher.parsing.observation_parser import ObservationParser
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.observation_repository import ObservationRepository


def configure_log():
    _format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename="odbFetcher.log", level=logging.DEBUG,
                        format=_format)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def run():
    configure_log()
    log = logging.getLogger("odbFetcher")
    sqlite_config = configparser.ConfigParser()
    sqlite_config.read(os.path.join(os.path.dirname(__file__), 'sqlite_config.ini'))
    sqlite_config.set("CONNECTION", "SQLITE_DB",
                      os.path.join(os.path.dirname(__file__), sqlite_config.get("CONNECTION", "SQLITE_DB")))
    indicator_repo = IndicatorRepository(True, sqlite_config)
    area_repo = AreaRepository(True, sqlite_config)
    observation_repo = ObservationRepository(True, area_repo, indicator_repo, sqlite_config)

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "parser_config.ini"))
    config.set("STRUCTURE_ACCESS", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("STRUCTURE_ACCESS", "FILE_NAME")))
    config.set("AREA_ACCESS", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("AREA_ACCESS", "FILE_NAME")))
    config.set("RAW_OBSERVATIONS", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("RAW_OBSERVATIONS", "FILE_NAME")))
    config.set("DATASET_OBSERVATIONS", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("DATASET_OBSERVATIONS", "FILE_NAME")))
    config.set("STRUCTURE_OBSERVATIONS", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("STRUCTURE_OBSERVATIONS", "FILE_NAME")))
    config.set("AREA_INFO", "FILE_NAME",
               os.path.join(os.path.dirname(__file__), config.get("AREA_INFO", "FILE_NAME")))
    parse(log, config, area_repo, indicator_repo, observation_repo)
    # Uncomment if need enriched data
    enrich(log, config, area_repo)
    log.info('Done')


def parse(log, config, area_repo, indicator_repo, observation_repo):
    IndicatorParser(log, config, area_repo, indicator_repo, observation_repo).run()
    AreaParser(log, config, area_repo, indicator_repo, observation_repo).run()
    ObservationParser(log, config, area_repo, indicator_repo, observation_repo).run()


def enrich(log, config, area_repo):
    Enricher(log, config, area_repo).run()


if __name__ == "__main__":
    run()
    print("Done! :)")
