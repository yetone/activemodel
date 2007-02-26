import os
import pwd
import urlparse
import urllib
import Queue


class DatabaseURL:


    def __init__(self, url):
        self.scheme, self.netloc, self.path, query, self.fragment = \
                                                          urlparse.urlsplit(url)
        self.user, self.host = urllib.splituser(self.netloc)
        if not self.user:
            try: # get userid from current user 
                self.user = pwd.getpwuid(os.getuid())[0]
            except KeyError: self.user = "nobody"
        self.user = self.user or ""
        self.userid = self.username = self.user # aliases
        self.adapter = self.scheme
        self.host, self.port = urllib.splitport(self.host)
        self.user, self.password = urllib.splitpasswd(self.user or "")
        self.password = self.password or ""
        self.path = self.path[1:]
        self.database = self.path
        if query:
            try:
                self.query = dict([
                    (k,urllib.unquote_plus(v)) for k,v in [e.split("=", 1) for e in self.query.split("&", 1)]
                    ])
            except ValueError, e:
                raise ValueError, "Query part in url cannot be parsed: %r (%s)" % (self.query, e)
        else: self.query = {}
        self.options = self.query



    




class ConnectionPool(Queue.Queue):


    def __init__(self, connector, size=5):
        Queue.Queue.__init__(self, size)
        self.connector = connector


    def get(self, block=1):
        try:
            return self.empty() and self.connector() or \
                   Queue.Queue.get(self, block)
        except Queue.Empty:
            return self.connector()

        
    def put(self, obj, block=1):
        try:
            return self.full() and None or Queue.Queue.put(self, obj, block)
        except Queue.Full:
            pass




class Connector:


    def __init__(self, function, *args, **kwargs):
        self.f = function
        self.args = args
        self.kwargs = kwargs


    def __call__(self):
        return self.f(*self.args, **self.kwargs)





class DatabaseError(Exception):
    pass


registered_protocol_list = []

def register_protocol(proto):
    if proto in registered_protocol_list:
        return
    urlparse.uses_netloc.append(proto)
    urlparse.uses_relative.append(proto)
    urlparse.uses_query.append(proto)
    urlparse.uses_params.append(proto)
    urlparse.uses_fragment.append(proto)
    registered_protocol_list.append(proto)

# XXX: Hack to make modules dynamically available
map(register_protocol, ["mysql", "sqlite3"])


class DatabaseAdapter(object):
    __registered__ = {}


    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            t = type.__new__(cls, name, bases, attrs)
            aname = name[:-7].lower()
            if aname != "database":
                t.__registered__[aname] = t
                register_protocol(aname)
            return t


    def error(self, msg):
        raise DatabaseError, msg


    @staticmethod
    def get(name):
        if name not in DatabaseAdapter.__registered__:
            __import__("activemodel.adapters", {}, {}, [name])
        try:
            return DatabaseAdapter.__registered__[name]
        except KeyError:
            raise DatabaseError, "Adapter for %r not available" % name




class DatabaseRecord(object):


    def __init__(self, data):
        self.__data__ = dict(data)


    def __repr__(self):
        return "<DatabaseRecord %r>" % self.__data__


    def get(self, name, default=None):
        return self.__data__.get(name, default)

    
    def __getitem__(self, key):
        #if isinstance(key, int):
        #    return self.__data__[self.__column_names__[key]]
        #else:
        return self.__data__[key]


    def __iter__(self):
        for key in self.__data__.keys(): #__column_names__:
            yield key
        raise StopIteration


    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        else:
            return self.__data__[name]


    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self.__data__[name] = value



class DatabaseResult(object):


    def __init__(self, cursor):
        self.cursor = cursor
        self.types = {}
        self.column_names = []
        for entry in self.cursor.description:
            (name, type_code,
             display_size, internal_size, precision, scale,
             null_ok) = entry
            self.column_names.append(name)
        self.cache = None
    

    def __len__(self):
        rowcount = self.cursor.rowcount
        if rowcount == -1:
            # XXX: Not supported, e.g. pysqlite2
            # Is this a good solution
            self.cache = self.cursor.fetchall()
            rowcount = len(self.cache)
        return rowcount

    
    def __iter__(self):
        result = []
        if self.cache != None:
            for row in self.cache:
                yield DatabaseRecord(zip(self.column_names, row))
        else:
            for row in self.cursor.fetchall():
                yield DatabaseRecord(zip(self.column_names, row))
        raise StopIteration


    def get_all(self):
        return list(self)


    def get_next(self, iterate=False):
        if self.cache != None:
            if len(self.cache):
                one = self.cache[0]
                del self.cache[0]
            else: one = None
        else:
            one = self.cursor.fetchone()
        if one == None:
            return
        record = DatabaseRecord(zip(self.column_names, one))
        return record

