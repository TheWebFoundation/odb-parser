def create_insert_query(table, data):
    columns = ', '.join(data.keys())
    placeholders = ':' + ', :'.join(data.keys())
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, placeholders)
    return query
