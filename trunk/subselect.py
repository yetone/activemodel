from activemodel import *

class Post(Model):
    pass

Model.establish_connection(adapter="mysql", database="test", userid="root")
spam = where(Post.subject != "spam").as_subselect("spam")
for row in select(spam.id, spam.body.length()):
    print row
