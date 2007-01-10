""" 
All modules in this directory are automatically imported and are added to the main namespace.
If you implement a Behaviour, ClassMethod or InstanceMethod it will available to all models.
See serialize.py for a simple example.
"""
__all__ = [
    "available_extensions"
    # more added below
]


import os


def import_extensions():
    l = []
    path = os.path.dirname(__file__) or os.getcwd()
    for name in os.listdir(path):
        mod_name, ext = os.path.splitext(name)
        if not name.startswith("_") and ext == ".py":
            filename = os.path.join(path, name)
            try:
                ext = "activemodel.extensions.%s" % mod_name
                mod = __import__(ext, {}, {}, [mod_name])
            except ImportError, e:
                raise ImportError, "Could not load ActiveModel extension %r from %r: %s" % (
                    ext, filename, e)
            for obj_name in getattr(mod, "__all__", []):
                obj = getattr(mod, obj_name)
                globals()[obj_name] = obj
                l.append(obj_name)
    return l


available_extensions = import_extensions()
__all__.extend(available_extensions)
