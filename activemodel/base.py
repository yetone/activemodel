import os
import pwd
import re
import time
import datetime
from activemodel.adapters.base import *
from activemodel.utils import *


DEBUG = True

if DEBUG:
    def debug(msg):
        print "#", msg
    debug("Debug is enabled")
    
    


class AttributeBase(object):


    def __init__(self, *args, **kwargs):
        self._init(*args, **kwargs)


    def _init(self, *args, **kwargs):
        pass


    def __getattr__(self, name):
        if not name.startswith("_"):
            return Function(self, name)
        try:
            return self.__dict__[name] #object.__getattr__(self, name)
        except KeyError:
            raise AttributeError, name


    def _cond(self, c):
        if isinstance(c, str):
            return SqlString(c)
        elif isinstance(c, int):
            return SqlInt(c)
        elif isinstance(c, float):
            return SqlFloat(c)
        elif isinstance(c, datetime.datetime):
            return SqlDateTime(c)
        elif isinstance(c, datetime.date):
            return SqlDate(c)
        return c


    def __op__(self, op, other): return Attribute(op, self, self._cond(other))
    def __eq__(self, other): return self.__op__("=", other)
    def __ne__(self, other): return self.__op__("<>", other)
    def __not__(self, other): return self.__op__(" NOT ", other)
    def __gt__(self, other): return self.__op__(">", other)
    def __ge__(self, other): return self.__op__(">=", other)
    def __lt__(self, other): return self.__op__("<", other)
    def __le__(self, other): return self.__op__("<=", other)
    def __and__(self, other): return self.__op__(" AND ", other)
    def __rand__(self, other): return self._cond(other).__op__(" AND ", self)
    def __add__(self, other): return self.__op__("+", other)
    def __radd__(self, other): return self._cond(other).__op__("+", self)
    def __sub__(self, other): return self.__op__("-", other)
    def __rsub__(self, other): return self._cond(other).__op__("-", self)
    def __mul__(self, other): return self.__op__("*", other)
    def __rmul__(self, other): return self._cond(other).__op__("*", self)
    def __div__(self, other): return self.__op__("/", other)
    def __rdiv__(self, other): return self._cond(other).__op__("/", self)
    def __mod__(self, other): return self.__op__("%", other)
    def __or__(self, other):return self.__op__(" OR ", other)
    def __ror__(self, other): return self._cond(other).__op__(" OR ", self)


    def _children(self):
        r = []
        a = getattr(self, "_a", getattr(self, "_parent", None))
        b = getattr(self, "_b", None)
        if isinstance(a, AttributeBase):
            r.extend(a._children() or [])
        r.append(self)
        if isinstance(b, AttributeBase):
            r.extend(b._children() or [])
        return r


    def __iter__(self):
        return iter(self._children())



class SqlParam(AttributeBase):
    

    def _init(self, value, wildcard=None):
        self._wildcard = wildcard or Model.__connection__.wildcard
        self._value = value

        
    def __repr__(self):
        return "%s" % self._wildcard
    
    
    def __str__(self):
        return repr(self)



class SqlDataType(AttributeBase):


    def __repr__(self):
        return str(self._value)


    def __str__(self):
        return repr(self)
    


class SqlString(SqlDataType):


    def _init(self, value, q='"'):
        self._value = "%s%s%s" % (q, value.replace(q, "\\%s" % q), q)



class SqlInt(SqlDataType):


    def _init(self, value):
        self._value = value


class SqlFloat(SqlDataType):


    def _init(self, value):
        self._value = value




class SqlDateTime(SqlDataType):


    def _init(self, value, q="'", format="%Y-%m-%d %H:%M:%s"):
        self._value = "%s%s%s" % (q, value.strftime(format), q)



class SqlDate(SqlDataType):


    def _init(self, value, q="'", format="%Y%m%d"):
        self._value = "%s%s%s" %(q, value.strftime(format), q)
        



class Function(AttributeBase):


    def _init(self, parent, name):
        self._parent = parent
        self._name = name
        self._args = []


    def __call__(self, *args):
        for a in args:
            if isinstance(a, str):
                a = SqlString(a)
            elif isinstance(a, int):
                a = SqlInt(a)
            elif isinstance(a, float):
                a = SqlFloat(a)
            elif isinstance(a, datetime.datetime):
                a = SqlDateTime(a)
            elif isinstance(a, datetime.date):
                a = SqlDate(a)
            self._args.append(a)
        return self


    def __repr__(self):
        vargs =  map(str,map(self._cond, self._args))
        args = ",".join(vargs)
        # in-fix instead of post-fix
        name = self._name.upper()
        if name in ["AS", "LIKE"]:
            return "%s %s %s" % (self._parent, name, args)
        elif name == "BETWEEN": 
            return "%s BETWEEN %s..%s" % (self._parent, vargs[0], vargs[1])
        elif name == "IN":
            if len(vargs) == 1:
                return "%s = %s" % (self._parent, args)
            return "%s IN (%s)" % (self._parent, args)
        elif name == "DISTINCT":
            return "DISTINCT %s" % self._parent
        # XXX: istartswith, iendswith, icontains
        elif name == "STARTSWITH":
            q = args[-1]
            if q in ["'", '"']:
                args = args[:-1] + "%%" + q
            return '%s LIKE %s' % (self._parent, args)
        elif name == "ENDSWITH":
            q = args[0]
            if q in ["'", '"']:
                args = q + "%%" + args[1:]
            return '%s LIKE %s' % (self._parent, args)
        elif name == "CONTAINS":
            q = args[0]
            if q in ["'", '"']:
                args = q + "%%" + args[1:-1] + "%%"  + q
            return '%s LIKE %s' % (self._parent, args)            
        else:
            if args:
                args = ",%s" % args
            return "%s(%s%s)" % (self._name.upper(), self._parent, args)


FUNC = Function(None, "")



class AND(AttributeBase):


    def _init(self, *ands):
        self._ands = ands


    def __repr__(self):
        # XXX: add () ?
        return " AND ".join(map(repr, self._ands))



class OR(AttributeBase):


    def _init(self, *ors):
        self._ors = ors


    def __repr__(self):
        # XXX: add () ?
        return " OR ".join(map(repr, self._ors))



class Attribute(AttributeBase):


    def _init(self, op, a, b):
        self._op = op
        self._a = a
        self._b = b


    def __repr__(self):
        def paren(x):
            if hasattr(x, "_children") and len(x._children()) > 1:
                x = str(x)
                if not x.startswith("(") and not x.endswith(")"):
                    x = "(%s)" % x
            return x
        a = self._cond(self._a)
        b = self._cond(self._b)
        if isinstance(self._a, str):
            a = SqlString(self._a)
        else:
            a = self._a
        if isinstance(self._b, str):
            b = SqlString(self._b)
        else:
            b = self._b
        return "(%s %s %s)" % (paren(a), self._op, paren(b))



class Column(AttributeBase):


    def _init(self, table=None, name=None, coltype=None, length=None,
              required=None, default=None, pk=None
              ):
        self._name = name
        self._table = table
        self._coltype = coltype
        self._length = length
        self._pk = pk
    

    def __repr__(self):
        tname = getattr(self._table, "_alias", None) or self._table.table_name
        return "%s.%s" % (tname, self._name)



class RawSql(AttributeBase):

    def _init(self, sql=""):
        self._sql = sql


    def __repr__(self):
        return self._sql



def tables_and_columns(*attrs):
    c = set()
    t = set()
    for a in attrs:
        if isinstance(a, Query): continue
        if isinstance(a, SubSelect): continue
        for x in a:
            if isinstance(x, Column):
                c.add(x)
                t.add(x._table.table_name)
    return list(t), list(c)



class SubSelect(AttributeBase):

    
    def _init(self, query):
        self.query = query
        self.table_name = str(self.query)
        self._alias = query._alias


    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        # XXX: test if column available - else return function
        return Column(self, name)
    
    
    def __getitem__(self, name):
        return Column(self, name)
        
    
        
class Query:


    def __init__(self, parent=None, select=None, where=None,
                 limit=None, groupby=None, orderby=None, alias=None):
        if parent:
            if select: self._select = select
            else: self._select = parent._select
            if where: self._where = where
            else: self._where = parent._where
            if limit: self._limit = limit
            else: self._limit = parent._limit
            if groupby: self._groupby = groupby
            else: self._groupby = parent._groupby
            if orderby: self._orderby = orderby
            else: self._orderby = parent._orderby
            if alias: self._alias = alias
            else: self._alias = alias
        else:
            self._select = select or ()
            self._where = where or ()
            self._limit = limit 
            self._groupby = groupby
            self._orderby = orderby
            self._alias = alias
        self.table_name = self._alias
        self._sql = None
        
    
    def as_subselect(self, alias):
        return SubSelect(self.as(alias))
        

    def __getslice__(self, start, end):
        return Query(self, limit=(start,end))


    def limit(self, start, end=None):
        return self[start:end]


    def where(self, *conditions):
        return Query(self, where=conditions)


    def select(self, *attrs):
        return Query(self, select=attrs)


    def orderby(self, o):
        return Query(self, orderby=o)
    order_by = orderby


    def groupby(self, g):
        return Query(self, groupby=g)
    group_by = groupby


    def as(self, alias):
        return Query(self, alias=alias)

        
    def _select_sql(self):
        if self._sql:
            return self._sql
        a = list(self._select)
        a.extend(self._where)
        tables, columns = tables_and_columns(*a)
        sql = "SELECT %s" % (", ".join(map(str, self._select)) or "*")
        if tables:
            sql += " FROM %s" % (", ".join(tables))
        if self._where:
            sql += " WHERE %s" % " AND ".join(map(str, self._where))
        if self._groupby:
            sql += " GROUP BY %s" % self._groupby        
        if self._orderby:
            sql += " ORDER BY %s" % self._orderby
        if self._limit:
            if isinstance(self._limit, tuple):
                sql += " LIMIT %s,%s" % (self._limit[0], self._limit[1])
            else: sql += " LIMIT %s" % self._limit
        self._sql = sql
        return sql


    def __repr__(self):
        return "<Query %r>" % str(self)
    
        
    def __str__(self):
        s = "(%s)" % self._select_sql()
        if self._alias:
            s = "(%s AS %s)" % (s, self._alias)
        return s


    def __iter__(self):
        for entry in Model.__connection__(self._select_sql()):
            yield entry
        raise StopIteration



def select(*attrs, **options):
    q = Query(select=attrs, **options)
    return q


def where(*conditions, **options):
    q = Query(where=conditions, **options)
    return q
    




class Behaviour(object):
    __collector__ = []
    __registered__ = {}


    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            t = type.__new__(cls, name, bases, attrs)
            if name != "Behaviour":
                t.__registered__[name] = t
            return t
        

    def __init__(self, *args, **kwargs):
        Behaviour.__collector__.append(self)
        self.cls = None # belongs to class cls
        self.args = args
        self.kwargs = kwargs


    def connect(self, cls):
        self.cls = cls
        setattr(self.cls, self.__class__.__name__, self)
        self.init()


    def init(self):
        pass


    def __call__(self, obj):
        return self.call(obj)


    def call(self, obj):
        pass



class Foreign:

    def __init__(self, obj, foreign, many=True, **options):
        self.obj = obj
        self.foreign = foreign
        self.options = options
        key = "%s_%s" % (
            obj.table_name,
            obj.primary_key)
        if many:
            self.find = FindMethod(foreign, "find_all_by_%s" % key)
        else:
            self.find = FindMethod(foreign, "find_by_%s" % key)
        obj[foreign.table_name] = self
        obj.__dict__["_get_%s" % foreign.table_name] = self.get


    def __repr__(self):
        return "<Foreign key from %s to %s>" % (
            self.obj.table_name, self.foreign.table_name)
    

    def get(self, _):
        # XXX: return list with delete, clear, append, find, build, create
        #
        return self.find(self.obj[self.obj.primary_key], **self.options)



class has_many(Behaviour):
    
    def call(self, obj):
        for foreign in self.args:
            f = MetaModel.__registered__.get(foreign, foreign)
            Foreign(obj, f, many=True, options=self.kwargs)


class has_one(Behaviour):

    # XXX: class_name, sql, order
    def call(self, obj):
        for foreign in self.args:
            f = MetaModel.__registered__.get(foreign, foreign)
            Foreign(obj, f, many=False)


# XXX: imlement
class belongs_to(Behaviour): pass
class has_and_belongs_to_many(Behaviour): pass

        


# Inject custom methods at runtime
class DynamicMethod(object):
    __registered__ = {}
    method_name = None
    pattern = None
    

    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            t = type.__new__(cls, name, bases, attrs)
            if name not in ["DynamicMethod", "ClassMethod", "InstanceMethod"]:
                p = t.pattern or t.method_name
                if not p:
                    if name.endswith("ClassMethod"):
                        p = from_camelcase(name[:-11])
                    elif name.endswith("InstanceMethod"):
                        p = from_camelcase(name[:-14])
                    elif name.endswith("Method"):
                        p = from_camelcase(name[:-6])
                    else: p = name.lower()
                rkey = (ClassMethod in bases, re.compile(p))
                t.__registered__[rkey] = t
            return t
        

    def __init__(self, parent, name, *args, **kwargs):
        self.parent = parent
        if InstanceMethod in self.__class__.__bases__:
            self.obj = parent
        else: self.cls = parent
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.init()


    def init(self):
        pass


    def __call__(self, *args, **kwargs):
        # XXX: better _before_update_cls 
        try: before = getattr(self.parent, "_before_%s" % self.name, None)
        except AttributeError: before = None
        if before: before(self.parent)
        result = self.call(*args, **kwargs)
        try: after = getattr(self.parent, "_after_%s" % self.name, None)
        except AttributeError: after = None
        if after: after(self.parent)            
        return result


    def call(self, *args, **kwargs):
        pass



class ClassMethod(DynamicMethod):
    pass


class InstanceMethod(DynamicMethod):
    pass



find_ops = [ (re.compile(op_pat), repl) for op_pat, repl in [
    ("^(.+)_eq$", "\\1 = ?"),
    ("^(.+)_ne$", "\\1 <> ?"),
    ("^(.+)_ge$", "\\1 >= ?"),
    ("^(.+)_gt$", "\\1 > ?"),
    ("^(.+)_le$", "\\1 <= ?"),
    ("^(.+)_lt$", "\\1 < ?"),
    ("^(.+)_startswith$", '\\1 LIKE CONCAT(?, "%")'),
    ("^(.+)_istartswith$", 'LOWER(\\1) LIKE CONCAT(?, LOWER("%"))'),    
    ("^(.+)_endswith$", '\\1 LIKE CONCAT("%", ?)'),
    ("^(.+)_contains$", '\\1 LIKE CONCAT("%", ?, "%")'),
    ("^(.+)_eq$", "\\1 = ?")
    ] ]


def query_keywords(cls, *values, **options):
    # XXX: work on real column objects
    table = cls.table_name
    for v in values: options.update(v)
    c = []
    params = []
    wc = cls.__connection__.wildcard
    for name, value in options.items():
        name = "%s.%s" % (table, name)
        if isinstance(value, tuple):
            c.append("%s BETWEEN %s AND %s" % (name, wc, wc))
            if len(value) != 2:
                raise ValueError, "length for between value is not 2"
            params.extend(list(value))
        elif isinstance(value, list):
            if name.endswith("_not_in"):
                name = name[:-7]
                c.append("%s NOT IN (%s)" % (name, ",".join([wc]*len(value))))
            else:
                c.append("%s IN (%s)" % (name, ",".join([wc]*len(value))))
            params.extend(value)
        else:
            found = False
            for op_re, repl in find_ops:
                cond = op_re.sub(repl, name)
                if cond != name:
                    cond = cond.replace("?", wc)
                    c.append(cond)
                    params.append(value)
                    found = True
                    break
            if not found:
                c.append("%s = %s" % (name, wc))
                params.append(value)
    return table, " AND ".join(c), tuple(params)




def query_simple(cls, columns, *values, **conditions):
    def get_col(col):
        if isinstance(col, Column): return col
        return cls.table_columns[col]
    if not isinstance(columns, list):
        columns = columns.split("_and_")
    columns = map(get_col, columns)
    conditions = conditions.get("conditions", [])
    if not isinstance(conditions, list):
        conditions = [conditions]
    wc = cls.__connection__.wildcard
    if not values and not conditions:
        raise ValueError, "neither values nor conditions specified"
    params = []
    if conditions:
        for i in range(len(conditions)):
            c = conditions[i]
            if 1: #if isinstance(c, basestring):
                if isinstance(c, tuple):
                    ps = c[1]
                    if not isinstance(ps, list): ps = [ps]
                    for p in ps:
                        #if not isinstance(p, SqlParam): p = SqlParam(p, wc)
                        # XXX: replace wildcard
                        params.append(p)
                    c = c[0]
                if not isinstance(c, RawSql):
                    c = RawSql(c)
                conditions[i] = c
    if values:
        if len(values) != len(columns):
            raise ValueError, "numbers of values does not match number of columns"
        i = 0
        for col in columns:
            col_values = values[i]
            if not isinstance(col_values, list):
                col_values = [col_values]
            cond = col.IN(*[SqlParam(cv, wc) for cv in col_values])
            conditions.append(cond)
            params.extend(col_values)
            i += 1
    return cls.table_name, AND(*conditions), tuple(params)
        
 



class RecordList:


    def __init__(self, l, cond):
        self.l = l
        self.cond = conf


    def __len__(self):
        return len(self.l)
    

    def __getiten__(self, i):
        return self.l[i]
    

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name.startswith("find"):
            setattr(self, name, FindMethod(name, self, conditions=self.cond))
        

    def __iter__(self):
        return iter(self.l)
    


class FindMethod(ClassMethod):
    pattern = "(find_or_create_by_.+|find_by_.+|find_all_by_.+|find_by|find_all_by|find_all|find)$"


    def __repr__(self):
        return "%s.%s" % (self.cls, self.name)
    

    def init(self):
        self.create = False
        if self.name.startswith("find_all_by_"):
            self.all = True
            columns = self.name[12:]
        elif self.name.startswith("find_all"):
            self.all = True
            columns = self.cls.primary_key
        elif self.name.startswith("find_by_"):
            self.all = False
            columns = self.name[8:]
        elif self.name == "find_by":
            self.all = False
            columns = ""
        elif self.name == "find_all_by":
            self.all = False
            columns = ""
        elif self.name.startswith("find_or_create_by_"):
            self.all = False
            self.create = True
            columns = self.name[18:]
        elif self.name == "find":
            self.all = False
            columns = self.cls.primary_key
        else:
            raise ModelError("unknown find-method: %r" % self.name)
        self.columns = columns.split("_and_")
        #cnames = self.cls.columns.keys()
        #for c in self.columns:
        #    if c not in cnames:
        #        raise DatabaseError, "%s: Column %r not in %r" % (self.method_name,
        #                                                          c, self.cls.table_name)


    def find_query(self, *values, **options):
        # XXX: better implementation needed
        return self.cls.table_name, " AND ".join(map(str, values)), ()


    def find_keywords(self, *values, **options):
        print "+++", query_keywords(self.cls, *values, **options)
        table = self.cls.table_name
        for v in values: options.update(v)
        c = []
        params = []
        wc = self.cls.__connection__.wildcard
        for name, value in options.items():
            name = "%s.%s" % (table, name)
            if isinstance(value, tuple):
                c.append("%s BETWEEN %s AND %s" % (name, wc, wc))
                if len(value) != 2:
                    raise ValueError, "length for between value is not 2"
                params.extend(list(value))
            elif isinstance(value, list):
                if name.endswith("_not_in"):
                    name = name[:-7]
                    c.append("%s NOT IN (%s)" % (name, ",".join([wc]*len(value))))
                else:
                    c.append("%s IN (%s)" % (name, ",".join([wc]*len(value))))
                params.extend(value)
            else:
                found = False
                for op_re, repl in self.find_ops:
                    cond = op_re.sub(repl, name)
                    if cond != name:
                        cond = cond.replace("?", wc)
                        c.append(cond)
                        params.append(value)
                        found = True
                        break
                if not found:
                    c.append("%s = %s" % (name, wc))
                    params.append(value)
        params = tuple(params)
        where = " AND ".join(c)
        return table, where, params


    def call(self, *values, **options):
        if self.name == "find" and len(values) and isinstance(values[0], AttributeBase):
            table, where, params = self.find_query(*values, **options)
        elif self.name in ["find_by", "find_all_by"]:
            table, where, params = self.find_keywords(*values, **options)
        else:
            table, where, params = query_simple(
                self.cls, self.columns, *values, **options)
        options = options.get("options", {})
        sql = "SELECT %s.* FROM %s WHERE %s" % (table, table, where)
        groupby = options.get("groupby")
        if groupby: sql += " GROUP BY %s" % groupby
        orderby = options.get("orderby")
        if orderby: sql += " ORDER BY %s" % orderby
        if not self.all:
            sql += " LIMIT 1"
        if DEBUG: debug("%s %r" % (sql, params))
        result = self.cls.__connection__(sql, *params)
        if self.all:
            a = []
            for row in result:
                obj = self.cls()
                for key in row:
                    obj[key] = row[key]
                a.append(obj)
            return a
        elif result:
            obj = self.cls()
            row = result.get_next()
            for key in row:
                obj[key] = row[key]
            return obj
        elif self.create:
            data = {}
            i = 0
            for col in self.columns:
                data[col] = values[i]
                i += 1
            data.update(
                options.get("create_data", {}))
            return self.cls.create(**data)
        else:
            raise ModelNotFound("%s.%s%r" % (self.cls.__name__, self.method_name, params))


# XXX: delete_all
class DeleteClassMethod(ClassMethod):
    pattern = "(delete|delete_by_.+)$"


    def init(self):
        if self.name == "delete":
            self.columns = self.cls.primary_key
        else:
            self.columns = self.name[10:]


    def call(self, *values, **options):
        # XXX:
        table, where, params = query_simple(
            self.cls, self.columns, *values, **options)
        if DEBUG:
            debug("DELETE FROM %s WHERE %s %r" % (table, where, params))



class CreateMethod(ClassMethod):


    def call(self, *l, **namevalues):
        if len(l):
            objs = []
            for namevalues in l:
                objs.append(self.cls.create(**namevalues))
            return objs
        else:
            obj = self.cls(**namevalues)
            if "created_at" in obj.table_columns.keys(): # XXX: created_on
                obj["created_at"] = time.time()
            pkid = obj.save()
            obj[self.cls.primary_key] = pkid
            return obj



# XXX: return True on success; raise ModelSaveError (->transactions!)
class SaveMethod(InstanceMethod):


    def call(self):
        # XXX: update if exists
        c = self.obj.table_columns.keys()
        d = dict([(k,v) for k,v in self.obj.__data__.items() if k in c])
        pk = self.obj.primary_key
        if self.obj[pk] != None:
            self.obj.update(d)
            return
        if pk in d.keys():
            del d[pk]
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (
            self.obj.table_name,
            ", ".join(d.keys()),
            ", ".join(
              [self.obj.__connection__.wildcard] * len(d)))
        params = tuple(d.values())
        if DEBUG:
            debug("%s %r" % (sql, params))
        pkid = self.obj.__connection__(sql, *params)
        return pkid



class DeleteInstanceMethod(InstanceMethod):

    def call(self):
        sql = "DELETE FROM %s WHERE %s = ?" % (
            self.obj.table_name, self.obj.primary_key)
        params = tuple(self.obj[self.obj.primary_key],)
        if DEBUG:
            debug("%s %r" % (sql, (self.obj[self.obj.primary_key],)))
        self.obj.__connection__(sql, *params)



class DeleteDuplicatesMethod(InstanceMethod):


    def call(self):
        sql = "DELETE FROM %s WHERE " % self.obj.table_name
        d = dict(self.obj.__data__)
        if self.obj.primary_key in d:
            del d[self.obj.primary_key]
        c = ["%s = ?" % k for k in d.keys()]
        c.append("%s <> ?" % self.obj.primary_key)
        sql += " AND ".join(c)
        if DEBUG:
            debug("%s %r" % (sql, tuple(d.values() + [self.obj[self.obj.primary_key]])))



class UpdateInstanceMethod(InstanceMethod):


    def call(self,  __data=None, **kwdata):
        self.obj.__data__.update(__data or {})
        self.obj.__data__.update(kwdata)
        if "updated_at" in list(self.obj): # XXX: updated_on
            self.obj.updated_at = time.time() 
        sql = "UPDATE %s SET " % self.obj.table_name
        params = []
        pk = self.obj.primary_key
        s = []
        for n,v in self.obj.__data__.items():
            if n == pk: continue
            s.append("%s = %s" % (n,self.obj.__connection__.wildcard))
            params.append(v)
        params = tuple(params + [self.obj[pk]])
        sql += ",".join(s)
        sql += " WHERE %s = %s" % (pk, self.obj.__connection__.wildcard)
        if DEBUG:
            debug("%s %r" % (sql, params))
        self.obj.__connection__(sql, *params)


# XXX: UpdateAll
class UpdateClassMethod(ClassMethod):


    def call(self, pkvalue, __data=None, **kwdata):
        if type(pkvalue) == type([]):
            for pv in pkvalue:
                self.call(pv, __data, **kwdata)
            return
        data = __data or {}
        data.update(kwdata)
        #if "updated_at" in list(obj): # XXX: updated_on
        #    self.obj.updated_at = time.time()
        sql = "UPDATE %s SET " % self.cls.table_name
        params = []
        pk = self.cls.primary_key
        s = []
        for n,v in data.items():
            if n == pk: continue
            s.append("%s = %s" % (n,self.cls.__connection__.wildcard))
            params.append(v)
        params = tuple(params + [pkvalue])
        sql += ",".join(s)
        sql += " WHERE %s = %s" % (pk, self.cls.__connection__.wildcard)
        if DEBUG:
            debug("%s %r" % (sql, params))
        self.cls.__connection__(sql, *params)





class ModelError(Exception):
    pass


class ModelNotFound(ModelError):
    pass



def find_or_404(find_function, *args, **kwargs):
    try:
        result = find_function(*args, **kwargs)
    except ModelNotFound:
        raise HttpError404



class MetaModel(type):

    __method_cache__ = {}
    __registered__ = {}
    

    def __new__(cls, name, bases, attrs):
        t = type.__new__(cls, name, bases, attrs)
        if name == "Model":
            return t
        if t.convert_camelcase:
            tname = from_camelcase(name) # lowers automatically
        else:
            tname = name
        if t.pluralize_table_names:
            tname = pluralize(tname)
        t.table_name = attrs.get("table_name") or tname
        MetaModel.__registered__[t.table_name] = t
        t.__behaviours__ = b = []
        collector = Behaviour.__collector__
        while collector:
            obj = collector.pop()
            obj.connect(t)
            b.append(obj)
        r = Behaviour.__registered__
        for n, v in attrs.items():
            if n in r:
                if type(v) == type(()) and len(v) == 2 and \
                       type(v[0]) == type(()) and type(v[1]) == type({}):
                    obj = r[n](*v[0], **v[1])
                else:
                    obj = r[n](v)
                b.append(obj)
        return t


    def __getattribute__(cls, name):
        method = MetaModel.__method_cache__.get((cls,name))
        if method:
            return method
        for (is_cm,pat), dynmethod in ClassMethod.__registered__.items():
            if not is_cm: continue
            found = pat.match(name)
            if found:
                method = dynmethod(cls, name)
                break
        if not method:
            try:
                return type.__getattribute__(cls, name)
            except AttributeError:
                if name == "table_columns":
                    c = cls.__connection__.inspect_table(cls.table_name)
                    for cname, (args, kwargs) in c.items():
                        c[cname] = Column(*((cls,)+args), **kwargs)
                    cls.table_columns = c
                    return c
                try:
                    return cls.table_columns[name]
                except KeyError:
                    raise AttributeError, "%s has no method or column named %r" % (cls, name)
        MetaModel.__method_cache__[(cls,name)] = method
        return method




class Model(object):

    __metaclass__ = MetaModel
    __connection__ = None
    NotFoundError = ModelNotFound
    
    primary_key = "id"
    pluralize_table_names = True
    convert_camelcase = True
    auto_save = False
    table_name = None 



    @classmethod
    def establish_connection(cls, url=None, adapter=None, database=None, 
                             host="localhost", userid="", password="",
                             options=None):
        if url != None:
            if isinstance(url, basestring):
                url = DatabaseURL(url)
        else:
            auth = "%s" % userid
            if password:
                auth += ":%s" % password
            if auth: auth += "@"
            url = "%s://%s%s/%s" % (
                adapter, auth, host, database)
            if options: url += urllib.urlencode(options)
            url = DatabaseURL(url)
        AdapterClass = DatabaseAdapter.get(adapter or url.adapter)
        cls.__connection__ = AdapterClass(url)
    

    def __init__(self, __data=None, **kwdata):
        self.__method_cache__ = {}
        self.__data__ = dict(__data or {})
        self.__data__.update(kwdata)
        if self.primary_key not in self.__data__.keys():
            self.__data__[self.primary_key] = None
        for b in self.__behaviours__:
            b(self)


    def __getitem__(self, name):
        try:
            value = self.__data__[name]
        except KeyError:
            value = self.__dict__[name]
        m = self.__dict__.get("_get_%s" % name)
        if m: value = m(value)
        return value


    def __setitem__(self, name, value):
        m = self.__dict__.get("_set_%s" % name)
        if m: value = m(value)
        self.__data__[name] = value
        if self.auto_save:
            self.save()
    

    def __getattr__(self, name):
        try:
            value = self.__dict__[name]
            return value
        except KeyError:
            try:
                return self[name]
            except KeyError:
                method = self.__method_cache__.get(name)
                if method: return method
                for (is_cm,pat), dynmethod in InstanceMethod.__registered__.items():
                    if is_cm: continue
                    found = pat.match(name)
                    if found:
                        method = dynmethod(self, name)
                        break
                if not method: 
                    raise AttributeError, name
                self.__method_cache__[name] = method
                return method


    def __setattr__(self, name, value):
        if name.startswith("_"):
            self.__dict__[name] = value
            return
        self[name] = value


    def __repr__(self):
        d = dict(self.__data__)
        return "<Model %s: %r>" % (self.__class__.__name__, d)



