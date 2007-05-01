#from base import *


__all__ = ["Migration"]


class Column:


    def __init__(self, name, column_type, *params):
        self.name = name
        self.column_type = column_type
        self.params = params


    def __str__(self):
        s = "%r %s" % (self.name, self.column_type)
        if self.params:
            s += " %s" % " ".join(map(str, self.params))
        return s



def PrimaryKey(name, *params):
    return Column(name, "integer", *(("auto_increment",)+params))



class MigrationNotPossible(Exception):
    pass



class UpMigrationNotPossible(MigrationNotPossible):
    pass


class DownMigrationNotPossible(MigrationNotPossible):
    pass




class Migration:

    __registered__ = {}


    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            t = type.__new__(cls, name, bases, attrs)
            if name != "Migration":
                t.__registered__[name] = t
            t.name = name
            return t


    @classmethod
    def make(cls):
        for name in sorted(cls.__registered__.keys()):
            yield cls.__registered__[name]
            

    def __init__(self, connection):
        self._con = connection


    def __call__(self, sql):
        print sql
        return self._con(sql)


    def create_table(self, name, *columns, **options):
        self._con.create_table(name, *columns, **options)


    def drop_table(self, name):
        self._con.drop_table(name)


    def rename_table(self, table, new_name):
        self._con.rename_table(table, new_name)


    def add_column(self, table, column):
        self._con.add_column(table, column)
        

    def rename_column(self, table, column, new_name):
        self._rename_column(self, table, column, new_name)


    def remove_column(self, table, name):
        self("ALTER TABLE %r DROP %r" % (table, name))
    

    def up(self):
        raise UpMigrationNotPossible


    def down(self):
        raise DownMigrationNotPossible




if __name__ == "__main__":
    class Test1(Migration):
        def up(self):
            self.create_table("testtable",
                              PrimaryKey("id"),
                              Column("value", "text"),
                              )
        def down(self):
            self.drop_table("testtable")


    class Test2(Migration):
        def up(self):
            self.add_column("testtable", "testcolumn")
        def down(self):
            self.remove_column("testtable", "testcolumn")



    class Test3(Migration):
        def up(self):
            self.rename_column("testtable", "testcolumn", "mycolumn")
        def down(self):
            self.rename_column("testtable", "mycolumn", "testcolumn")



    import sys
    from base.adapters.sqlite3 import SqliteAdapter
    for m in Migration.make():
        print m.name
        m = m()
        m.up()
        print "-"*30
