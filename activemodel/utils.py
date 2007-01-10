import re


def pluralize(name):
    # Totally imcomplete and untested
    # http://en.wikipedia.org/wiki/English_plural
    # Also interesting:
    # http://opensvn.csie.org/inflector/trunk/python/Rules/English.py
    special = {
        "sheep": "sheep", "mouse": "mice", "man": "men", "woman":"women",
        "person": "people" }
    s = special.get(name)
    if s: return s
    if name.endswith("y") and name[-2] not in "AOIUaoiu":
        return name[:-1] + "ies"
    elif name.endswith("sh") or name.endswith("ss") \
             or name.endswith("ch") or name.endswith("o"):
        return name + "es"
    elif not name.endswith("s"):
        return name + "s"
    return name



cap_re = re.compile("([A-Z][a-z]+)([A-Z][a-z]+)")

def from_camelcase(s):
    while True:
        old = s
        s = cap_re.sub("\\1_\\2", s)
        if old == s: break
    return s.lower()


def to_camelcase(s):
    return "".join([p.capitalize() for p in s.split("_")])



def install_hook(obj, name, function):
    h = getattr(obj, name, None)
    if not h:
        setattr(obj, name, Hook())
    h.append(function)
    

class Hook:


    def __init__(self):
        self.functions = []


    def append(self, f):
        self.functions.append(f)

        
    def __call__(self, *args, **kwargs):
        for f in self.functions:
            f(*args, **kwargs)

        
