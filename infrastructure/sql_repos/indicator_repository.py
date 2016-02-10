from infrastructure.errors.errors import IndicatorRepositoryError
from infrastructure.sql_repos.utils import create_insert_query, get_db
from odb.domain.model.indicator.indicator import Repository, Indicator
from odb.domain.model.indicator.indicator import create_indicator


class IndicatorRepository(Repository):
    """
    Concrete sqlite repository for Indicators.
    """

    def __init__(self, recreate_db, config):
        """
        Constructor for IndicatorRepository

        Args:
        """
        self._config = config
        self._db = self._initialize_db(recreate_db)

    def _initialize_db(self, recreate_db):
        db = get_db(self._config)
        if recreate_db:
            db.execute('DROP TABLE IF EXISTS indicator')
            sql = '''
                CREATE TABLE indicator
                (
                    id INTEGER PRIMARY KEY,
                    component TEXT,
                    description TEXT,
                    format_notes TEXT,
                    index_code TEXT,
                    indicator TEXT COLLATE NOCASE,
                    license TEXT,
                    name TEXT,
                    provider_name TEXT,
                    provider_url TEXT,
                    range TEXT,
                    source_data TEXT,
                    source_name TEXT,
                    source_url TEXT,
                    subindex TEXT,
                    tags TEXT,
                    type TEXT,
                    units TEXT,
                    uri TEXT,
                    weight REAL
                );
                '''
            db.execute(sql)
            db.execute("CREATE UNIQUE INDEX indicator_indicator_index ON indicator (indicator COLLATE NOCASE)")
            db.commit()
        return db

    def begin_transaction(self):
        self._db.execute("BEGIN TRANSACTION")

    def commit_transaction(self):
        self._db.commit()

    def insert_indicator(self, indicator, commit=True):
        data = IndicatorRowAdapter().indicator_to_dict(indicator)
        query = create_insert_query('indicator', data)
        self._db.execute(query, data)
        if commit:
            self._db.commit()

    def find_indicator_by_code(self, indicator_code, _type=None):
        query = "SELECT * FROM indicator WHERE indicator LIKE :indicator"
        if not indicator_code:
            raise IndicatorRepositoryError("Indicator name must not be empty")
        data = {'indicator': indicator_code.upper()}
        if _type:
            query += " AND type LIKE :_type"
            data['_type'] = _type

        r = self._db.execute(query, data).fetchone()
        if r is None and _type is None:
            raise IndicatorRepositoryError("No indicator with code %s found" % (indicator_code,))
        elif r is None and _type is not None:
            raise IndicatorRepositoryError(
                "No indicator with code %s and type %s found" % (indicator_code, _type))

        data = dict(r)
        children = self.find_indicator_children(data)
        data["children"] = children

        return IndicatorRowAdapter().dict_to_indicator(data)

    def find_indicators(self):
        """
        Finds all indicators

        Returns:
            list of Indicator: All the indicators stored
        """
        _index = self.find_indicators_index()
        subindices = self.find_indicators_sub_indexes()
        indicators = self.find_indicators_indicators()

        result = (_index + subindices + indicators)
        return result

    def find_indicators_index(self):
        """
        Finds all indicators whose type is Index

        Returns:
            list of Indicator: Indicators with type Index
        """
        return self.find_indicators_by_level("INDEX")

    def find_indicators_components(self, parent=None):
        """

        Args:
            parent (Indicator, optional):

        Returns:

        """
        return self.find_indicators_by_level("COMPONENT", parent)

    def find_indicator_children(self, indicator_dict):
        """
        Finds the children of the given indicator

        Args:
            indicator_dict (dict): dict representing the indicator we want to fetch children of

        Returns:
            list of Indicator: The children of the indicator
        """
        # We could get everything in one query, but it is easier to read this way
        if indicator_dict['type'].upper() == 'INDEX':
            query = "SELECT * FROM indicator WHERE (type = 'SUBINDEX' AND index_code=:index_code)"
            indicators = self._db.execute(query, {'index_code': indicator_dict['indicator']}).fetchall()
        elif indicator_dict['type'].upper() == 'SUBINDEX':
            query = "SELECT * FROM indicator WHERE (type = 'COMPONENT' AND subindex=:subindex)"
            indicators = self._db.execute(query, {'subindex': indicator_dict['indicator']}).fetchall()
        elif indicator_dict['type'].upper() == 'COMPONENT':
            query = "SELECT * FROM indicator WHERE ((type = 'PRIMARY' OR type = 'SECONDARY') AND component = :component)"
            indicators = self._db.execute(query, {'component': indicator_dict['indicator']}).fetchall()
        else:
            return []

        processed_indicators = []
        for indicator in [dict(i) for i in indicators]:
            children = self.find_indicator_children(indicator)
            indicator["children"] = children
            processed_indicators.append(IndicatorRowAdapter.dict_to_indicator(indicator))

        return processed_indicators

    def find_indicators_sub_indexes(self):
        return self.find_indicators_by_level("SUBINDEX")

    def find_indicators_primary(self, parent=None):
        return self.find_indicators_by_level("PRIMARY", parent)

    def find_indicators_secondary(self, parent=None):
        return self.find_indicators_by_level("SECONDARY", parent)

    def find_indicators_indicators(self, parent=None):
        """
        Finds all indicators whose type is Primary or Secondary

        Args:
            parent: Additional filter to restrict the parent

        Returns:
            list of Indicator: Indicators with type Primary or Secondary
        """
        primary = self.find_indicators_primary(parent)
        secondary = self.find_indicators_secondary(parent)

        result = (primary + secondary)
        return result

    def find_indicators_by_level(self, level, parent=None):
        """
        Finds indicators whose type is equals to the given level, e.g.: Index, SubIndex, Primary or Secondary

        Args:
            level (str): Type of the indicators to search
            parent (Indicator, optional): Parent indicator if more filter is required, default to None

        Returns:
            list of Indicator: Indicators that fit with the given filters
        """

        if parent is not None:
            # We filter by matching the parent_type to the column, in the future we may want to change this if there is
            # not a clear mapping or we are using relations (e.g. foreign keys)
            parent_column = "index_code" if parent.type == "INDEX" else parent.type
            where_clause = "WHERE (type = :type AND %s = :parent_code)" % (parent_column,)
            query = "SELECT * FROM indicator %s" % (where_clause,)
            rows = self._db.execute(query, {'type': level, 'parent_code': parent.indicator}).fetchall()
        else:
            where_clause = "WHERE (type = :type)"
            query = "SELECT * FROM indicator %s" % (where_clause,)
            rows = self._db.execute(query, {'type': level}).fetchall()

        processed_indicators = []

        for indicator in [dict(r) for r in rows]:
            children = self.find_indicator_children(indicator)
            indicator["children"] = children
            processed_indicators.append(indicator)

        return IndicatorRowAdapter().transform_to_indicator_list(processed_indicators)


class IndicatorRowAdapter(object):
    """
    Adapter class to transform indicators between SQLite objects and Domain objects
    """

    @staticmethod
    def indicator_to_dict(indicator):
        """
        Transforms one single indicator into a dict ready to be used in a sqlite statement

        Args:
            indicator (Indicator): An indicator

        Returns:
            dict: Dictionary with keys and values mapped to the sqlite table
        """
        # Strip unwanted values
        data = dict(
            (key, value) for key, value in list(indicator.to_dict().items()) if key not in ('parent', 'children'))
        # Replace keys
        data['index_code'] = data['index']
        data.pop('index')
        return data

    @staticmethod
    def dict_to_indicator(indicator_dict):
        """
        Transforms one single indicator

        Args:
            indicator_dict (dict): Indicator dictionary coming from a sqlite row with children already filled

        Returns:
            Indicator: Indicator object with the data in indicator_dict
        """
        data = dict(indicator_dict)
        data['index'] = data['index_code']
        data.pop('index_code')
        return create_indicator(**data)

    @staticmethod
    def transform_to_indicator_list(indicator_dict_list):
        """
        Transforms a list of indicators

        Args:
            indicator_dict_list (list): Indicator dict list

        Returns:
            list of Indicator: A list of indicators with the data in indicator_row_list
        """
        return [IndicatorRowAdapter.dict_to_indicator(indicator_dict) for indicator_dict in indicator_dict_list]


if __name__ == "__main__":
    import configparser
    import json

    sqlite_config = configparser.RawConfigParser()
    sqlite_config.add_section('CONNECTION')
    sqlite_config.set('CONNECTION', 'SQLITE_DB', '../../odb2015.db')

    repo = IndicatorRepository(False, sqlite_config)

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

    readiness = repo.find_indicator_by_code('readiness')
    indicators = repo.find_indicators_by_level('component', parent=readiness)
    assert 0 < len(indicators) < 10
    print(json.dumps([i.to_dict() for i in indicators]))

    print('OK!')
