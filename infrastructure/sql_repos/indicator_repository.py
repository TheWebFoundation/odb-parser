__author__ = 'Rodrigo'

from infrastructure.errors.errors import IndicatorRepositoryError
from a4ai.domain.model.indicator.indicator import Repository, Indicator
# from config import port, db_name, host
# from mongo_connection import connect_to_db
from infrastructure.utils import error, success, uri, normalize_group_name
from odb.domain.model.indicator.indicator import create_indicator


class _MockDB(object):
    def __init__(self, log):
        self._log = log

    def insert(self, table, dict):
        self._log.info("\tStoring %s in %s", dict, table)


class IndicatorRepository(Repository):
    """
    Concrete sqlite repository for Indicators.
    """

    def __init__(self, log):
        """
        Constructor for IndicatorRepository

        Args:
        """
        self._log = log
        self._db = _MockDB(log)  # connect_to_db(host=host, port=port, db_name=db_name)
        # self._url_root = url_root

    def insert_indicator(self, indicator, indicator_uri=None, component_name=None, subindex_name=None, index_name=None,
                         weight=None, provider_name=None, provider_url=None, is_percentage=None, scale=None):
        indicator_dict = {}
        indicator_dict["index"] = normalize_group_name(index_name)
        indicator_dict["subindex"] = normalize_group_name(subindex_name)
        indicator_dict["indicator"] = indicator.indicator
        indicator_dict["name"] = indicator.name
        indicator_dict["description"] = indicator.description
        indicator_dict["type"] = indicator.type
        indicator_dict["parent"] = normalize_group_name(component_name)
        indicator_dict['uri'] = indicator_uri
        indicator_dict['republish'] = indicator.republish
        indicator_dict['provider_name'] = provider_name
        indicator_dict['provider_url'] = provider_url
        indicator_dict['is_percentage'] = is_percentage
        indicator_dict['scale'] = scale

        self._db.insert('indicators', indicator_dict)
