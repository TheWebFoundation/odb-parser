__author__ = 'Rodrigo'

from infrastructure.errors.errors import IndicatorRepositoryError
from odb.domain.model.indicator.indicator import Repository, Indicator
from infrastructure.utils import error, success, uri, normalize_group_name
from odb.domain.model.indicator.indicator import create_indicator

import sqlite3


class _MockDB(object):
    def __init__(self, log):
        self._log = log

    def insert(self, table, indicator):
        self._log.info("\tStoring %s in %s", indicator.__dict__, table)


class IndicatorRepository(Repository):
    """
    Concrete sqlite repository for Indicators.
    """

    def __init__(self, recreate_db, log, config):
        """
        Constructor for IndicatorRepository

        Args:
        """
        self._config = config
        self._log = log
        # FIXME: The structure must be already in place
        self._db = self._initialize_db(recreate_db)

    def _initialize_db(self, recreate_db):
        db = sqlite3.connect(self._config.get("CONNECTION", "SQLITE_DB"))
        db.row_factory = sqlite3.Row
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS indicator')
            sql = '''
                CREATE TABLE indicator
                (
                    id INTEGER PRIMARY KEY,
                    index_code TEXT,
                    indicator TEXT NOT NULL,
                    name TEXT,
                    provider_url TEXT,
                    description TEXT,
                    uri TEXT,
                    component TEXT,
                    subindex TEXT,
                    type TEXT,
                    source_name TEXT,
                    provider_name TEXT,
                    republish INTEGER,
                    is_percentage INTEGER,
                    tags TEXT,
                    weight REAL,
                    scale REAL
                );
                '''
            db.execute(sql)
            db.commit()
        return db

    def _create_insert_query(self, data):
        columns = ', '.join(data.keys())
        placeholders = ':' + ', :'.join(data.keys())
        query = 'INSERT INTO indicator (%s) VALUES (%s)' % (columns, placeholders)
        return query

    # FIXME: Why the extra parameters?
    def insert_indicator(self, indicator, indicator_uri=None, component_name=None, subindex_name=None, index_name=None,
                         weight=None, source_name=None, provider_name=None, provider_url=None, is_percentage=None,
                         scale=None, tags=None):
        data = IndicatorRowAdapter().indicator_to_dict(indicator)
        query = self._create_insert_query(data)
        self._db.execute(query, data)
        self._db.commit()

    def find_indicator_by_code(self, indicator_code):
        query = "SELECT * FROM indicator where indicator=:indicator"
        indicator_code = indicator_code or ''
        r = self._db.execute(query, {'indicator': indicator_code.upper()}).fetchone()
        if r is None:
            raise IndicatorRepositoryError("No indicator with code " + indicator_code)

        data = dict(r)
        children = self._find_indicator_children(data)
        data["children"] = children

        return IndicatorRowAdapter().dict_to_indicator(data)

    def _find_indicator_children(self, indicator_dict):
        """
        Finds the children of the given indicator

        Args:
            indicator_dict (dict): dict representing the indicator we want to fetch children of

        Returns:
            list of Indicator: The children of the indicator
        """
        # We could get everything in one query, but it is easier to read this way
        if indicator_dict['type'].upper() == 'INDEX':
            query = "SELECT * FROM indicator WHERE (type LIKE 'SUBINDEX' AND index_code=:index_code)"
            indicators = self._db.execute(query, {'index_code': indicator_dict['indicator']}).fetchall()
        elif indicator_dict['type'].upper() == 'SUBINDEX':
            query = "SELECT * FROM indicator WHERE (type LIKE 'COMPONENT' AND subindex=:subindex)"
            indicators = self._db.execute(query, {'subindex': indicator_dict['indicator']}).fetchall()
        elif indicator_dict['type'].upper() == 'COMPONENT':
            query = "SELECT * FROM indicator WHERE ((type LIKE 'PRIMARY' OR type LIKE 'SECONDARY') AND component LIKE :component)"
            indicators = self._db.execute(query, {'component': indicator_dict['indicator']}).fetchall()
        else:
            return []

        processed_indicators = []
        for indicator in [dict(i) for i in indicators]:
            children = self._find_indicator_children(indicator)
            indicator["children"] = children
            processed_indicators.append(indicator)

        return processed_indicators


class IndicatorRowAdapter(object):
    """
    Adapter class to transform indicators between SQLite objects and Domain objects
    """

    def indicator_to_dict(self, indicator):
        """
        Transforms one single indicator into a dict ready to be used in a sqlite statement

        Args:
            indicator (Indicator): An indicator

        Returns:
            dict: Dictionary with keys and values mapped to the sqlite table
        """
        # Strip unwanted values
        data = dict((key, value) for key, value in indicator.to_dict().items() if key not in ('parent', 'children'))
        # Replace keys
        data['index_code'] = data['index']
        data.pop('index')
        return data

    def dict_to_indicator(self, indicator_dict):
        """
        Transforms one single indicator

        Args:
            indicator_dict (dict): Indicator dictionary coming from a sqlite row

        Returns:
            Indicator: Indicator object with the data in indicator_dict
        """
        data = dict(indicator_dict)
        data['index'] = data['index_code']
        data.pop('index_code')
        data['children'] = self._transform_to_indicator_list(data['children'])
        return create_indicator(**data)

    def _transform_to_indicator_list(self, indicator_dict_list):
        """
        Transforms a list of indicators

        Args:
            indicator_dict_list (list): Indicator dict list

        Returns:
            list of Indicator: A list of indicators with the data in indicator_row_list
        """
        return [self.dict_to_indicator(indicator_dict) for indicator_dict in indicator_dict_list]


if __name__ == "__main__":
    import logging
    import ConfigParser

    logger = logging.getLogger(__name__)
    config = ConfigParser.RawConfigParser()
    config.add_section('CONNECTION')
    config.set('CONNECTION', 'SQLITE_DB', '../../odb2015.db')

    repo = IndicatorRepository(False, logger, config)

    indicator = repo.find_indicator_by_code('ODB.2015.C.MANAG')
    assert indicator.indicator == 'ODB.2015.C.MANAG'

    indicator = repo.find_indicator_by_code('ODB.2015.C.manag')
    assert indicator.indicator == 'ODB.2015.C.MANAG'

    indicator = repo.find_indicator_by_code('government_policies')
    assert indicator.indicator == 'GOVERNMENT_POLICIES'
    assert len(indicator.children) > 0
    assert indicator.children[0]._type == 'PRIMARY' or indicator.children._type == 'SECONDARY'

    indicator = repo.find_indicator_by_code('readiness')
    assert indicator.indicator == 'READINESS'
    assert len(indicator.children) > 0
    assert indicator.children[0].type == 'COMPONENT'

    print 'OK!'
