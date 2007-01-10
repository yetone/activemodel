from activemodel.base import *

# Setting __all__ is not neccessary for dynamic methods because a 
# metaclass registers them automatically


class ToXmlMethod(InstanceMethod):
    # The method will be called "to_xml". CamelCasedWords get converted to 
    # camel_cased_words and suffixes like Method, InstanceMethod and 
    # ClassMethod will be removed.
    # If you want a different name you can either specify method_name 
    # or specify a regular expression named pattern in the class body  
    # (This is for example used for find_by_*)
    # ObjectMethods work the same way but contain a variable self.cls 
    # instead of self.obj. If you share code you can use self.parent

    def call(self, instruct=True, skip=[]):
        # This is the method call as you probably guessed
        xml = []
        xout = xml.append
        if instruct:
            xout("""<?xml version="1.0" encoding="UTF-8"?>""")
        xout("<%s>" % self.obj.table_name)
        for key in self.obj:
            if key in skip:
                continue
            value = self.obj[key]
            t = type(value).__name__
            if t in ["float", "int"]:
                t = ''' type="%s"''' % t
            else: t = ""
            xout("""  <%s%s>%s</%s>""" % (
                key, t, value, key))
        xout("</%s>" % self.obj.table_name)
        return "\n".join(xml)

