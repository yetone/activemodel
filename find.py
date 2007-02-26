from activemodel import *

class Post(Model): has_many("comments", orderby="id desc")
class Comment(Model): belongs_to("posts")
#Model.establish_connection("mysql://root@localhost/test")
Model.establish_connection("sqlite3://test.db")


#print Post.find([1,3], conditions=["id>0", ("id<%s", 10)])
#print Post.find_by_subject("second test")
print Post.find_by(id=(0,3))
#print Post.find(Post.subject !="first post")
