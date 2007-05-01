from activemodel.adapters.base import *
from activemodel.base import *


DEBUG = True


class SqliteResult(DatabaseResult):
    pass


class SqliteAdapter(DatabaseAdapter):
    wildcard = "?"


    def __init__(self, db_url):
        # XXX: other order?
        try:
            self.mod = __import__("pysqlite2.dbapi2", {}, {}, ["dbapi2"])
        except ImportError, e:
            try:
                self.mod = __import__("sqlite3.dbapi2", {}, {}, ["dbapi2"])
            except ImportError, e:
                self.error("Required database module " \
                           "sqlite3 or pysqlite2 not available: %s" % e)
        try:
            filename = db_url.netloc
            if db_url.path:
                 filename += ("/" + db_url.path)
            self.con = self.mod.Connection(
                filename,
                **db_url.options)
        except Exception, e:
            self.error("Could not connect to database %r: %s"  % (
                            db_url.database, e))


    def __call__(self, sql, *args):
        try:
            cursor = self.con.cursor()
        except Exception, e:
            if DEBUG:
                self.error("Sqlite-cursor error: %s:%s %r" % (e, sql, args))
            else:
                self.error("Could not get cursor for sql operaton: %s" % e)
        try:
            if isinstance(sql, list):
                cursor.executemany(sql, args)
            else:
                cursor.execute(sql, args)
        except Exception, e:
            if DEBUG:
                self.error("Sqlite-query error: %s: %s %r" % (e, sql, args))
            else:
                self.error("Could not execute query: %s" % e)
        if isinstance(sql, list):
            return cursor
        lsql = sql.lower()
        if sql.lower().startswith("insert"):
            return cursor.lastrowid
        if lsql.startswith("select") or lsql.startswith("show") \
           or lsql.startswith("describe") or lsql.startswith("pragma"):
            return SqliteResult(cursor)

        
    def list_tables(self):
        result = self("select name from sqlite_master where type='table' and not name='sqlite_sequence'")
        return [row for row in result]


    def inspect_table(self, table_name):
        result = self('pragma table_info("%s")' % table_name)
        columns = {}
        for col in result:
            col_name = col["name"]
            columns[col_name] = (col_name, col["type"]),  dict(
              required=col["notnull"] != 0,
              default=col["dflt_value"],
              pk=col["pk"] != 0)
        return columns


