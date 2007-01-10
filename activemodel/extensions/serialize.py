"""
This extension adds a serialize behaviour. You can use it to save any 
Python values in a varchar column of a sql database:

  >>> class User(Model):
  ...    serialize("preferences", format="pickle")   
  >>> u = User.find(1)
  >>> u.preferences = {"background": "white", "show_stats": False, "mails_per_page": 10}
  
It takes the following arguments:
  * the first is the name of a column
  * the keyword format specifies the serialization format,
    pickle is default and can be omitted.

The behaviour serializes the column value before saving to the database
and decodes it on loading. 

But beware that your serialized data does not exceed the size of the
used column AND that you cannot query directly on the database with 
the find-methods.

If you don't know about serialisation please read 
http://docs.python.org/lib/module-pickle.html
"""
import pickle
# Import this module for writing extensions
from activemodel.base import *


# Specifying __all__ is important if you want your behaviour to be available 
# with "from activemodel import *"
__all__ = ["serialize"] 


class serialize(Behaviour):
    # The Behaviour metaclass will automatically register this class so that 
    # ActiveRecord knows about it


    def __call__(self, obj):
        # This method is called after the Model instance is created
        columns = self.args
        format = self.kwargs.get("format", "pickle") 
        for name in columns:
            # model_instance._[gs]et_columnname gets called if available
            # when accessing the column value. We use this hook for
            # serialization
            setattr(obj, "_get_%s" % name, getattr(self, "get_%s" % format))
            setattr(obj, "_set_%s" % name, getattr(self, "set_%s" % format))


    # probably dangerous, use only for testing
    def get_repeval(self, value):
        return eval(value)


    def set_repeval(self, value):
        return repr(value)


    def set_pickle(self, value):
        return pickle.dumps(value)
    
        
    def get_pickle(self, value):
        return pickle.loads(value)

