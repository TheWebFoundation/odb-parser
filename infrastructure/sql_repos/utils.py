import sqlite3


def create_insert_query(table, data):
    columns = ', '.join(data.keys())
    placeholders = ':' + ', :'.join(data.keys())
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, placeholders)
    return query


def get_db(config):
    db = sqlite3.connect(config.get("CONNECTION", "SQLITE_DB"))
    db.row_factory = sqlite3.Row
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

    return db
