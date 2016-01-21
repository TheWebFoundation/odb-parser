__author__ = 'Rodrigo'

from infrastructure.errors.errors import IndicatorRepositoryError
from odb.domain.model.indicator.indicator import Repository, Indicator
from infrastructure.utils import error, success, uri, normalize_group_name
from odb.domain.model.indicator.indicator import create_indicator


class _MockDB(object):
    def __init__(self, log):
        self._log = log

    def insert(self, table, indicator):
        self._log.info("\tStoring %s in %s", indicator.__dict__, table)


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
        self._db = _MockDB(log)

    # FIXME: Why the parameters?
    def insert_indicator(self, indicator, indicator_uri=None, component_name=None, subindex_name=None, index_name=None,
                         weight=None, source_name=None, provider_name=None, provider_url=None, is_percentage=None,
                         scale=None, tags=None):
        self._db.insert('indicators', indicator)
