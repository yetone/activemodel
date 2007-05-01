import re
from activemodel.base import *



class ValidationError(Exception):
    pass



class ValidationMixin:


    def __call__(self, obj):
        setattr(obj, "_before_save", self.do_validate)


    def do_validate(self, obj):
        for col in self.args:
            try:
                value = obj[col]
                self.validate(value)
            except ValidationError, e:
                obj.errors[col] = e



class validates_presense_of(Behaviour, ValidationMixin):
    
        
    def validate(self, value):
        if not value:
            raise ValidationError, "attribute cannot be blank"
        
        

class validates_format_of(Behaviour, ValidationMixin):

    
    def __call__(self, obj):
        ValidationMixin.__call__(self, obj)
        self.re = re.compile(self.kwargs["with"])
        
        
    def validate(self, value):
        if not self.re.match(value):
            raise ValidationError, "attribute has wrong format"
        
        

class validates_length_of(Behaviour):

    
    def validate(self, value):
        w = self.kwargs["within"]
        if value < w[0] or value > w[1]:
            raise ValidationError, "not in range %s..%s" % (w[0], w[1])