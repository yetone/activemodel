from activemodel.adapters.base import *
from activemodel.base import *


DEBUG = True



class MySQLResult(DatabaseResult):


    def __init__(self, cursor):
        self.cursor = cursor
        self.types = {}
        self.column_names = []
        for entry in self.cursor.description:
            (name, type_code,
             display_size, internal_size, precision, scale,
             null_ok) = entry
            self.column_names.append(name)
##            self.types[name] = self.typemap.get(type_code, None)


    def __len__(self):
        return self.cursor.rowcount




class MySQLAdapter(DatabaseAdapter):
##    __connection_cache__ = {}
##    __typemap__ = {}
    wildcard = "%s"


    def __init__(self, db_url):
        try:
            self.mod = __import__("MySQLdb")
        except ImportError, e:
            self.error("Required database module " \
                       "MySQLdb not available: %s" % e)
        try:
            self.con = self.mod.Connection(
                host=db_url.host,
                user=db_url.userid,
                passwd=db_url.password,
                db=db_url.database,
                **db_url.options)
        except Exception, e:
            self.error("Could not connect to database %r" \
                       " on host %r with user %r: %s" % (
                            db_url.database, db_url.host, db_url.userid, e))
##        if not MySQLAdapter.__typemap__:
##            MySQLAdapter.__typemap__ =self.init_typemap()


##    def init_typemap(self):
##        typemap = {}
##        for name in dir(self.mod.constants.FIELD_TYPE):
##            if not name.startswith("_"):
##                value = getattr(self.mod.constants.FIELD_TYPE, name)
##                typemap[value] = name
##        return typemap


    def __call__(self, sql, *args):
        try:
            cursor = self.con.cursor()
        except Exception, e:
            if DEBUG:
                self.error("MySQL-cursor error: %s:%s %r" % (e, sql, args))
            else:
                self.error("Could not get cursor for sql operaton: %s" % e)
        try:
            if isinstance(sql, list):
                cursor.executemany(sql, args)
            else:
                cursor.execute(sql, args)
        except Exception, e:
            if DEBUG:
                self.error("MySQL-query error: %s: %s %r" % (e, sql, args))
            else:
                self.error("Could not execute query: %s" % e)
        if isinstance(sql, list):
            return cursor
        lsql = sql.lower()
        if sql.lower().startswith("insert"):
            return cursor.lastrowid
        if lsql.startswith("select") or lsql.startswith("show") \
           or lsql.startswith("describe"):
            return MySQLResult(cursor)


    def inspect_table(self, table_name):
        result = self("SHOW COLUMNS FROM %s" % table_name)
        columns = {}
        for row in result:
            name = row["Field"]
            columns[name] = (name, row["Type"]), dict(
                required=(row["Null"] != "NO"),
                default=row["Default"],
                ) #pk=(row.get("KEY")=="PRI"))
        return columns
