from activemodel import *

CREATE = [
    """DROP TABLE IF EXISTS posts""",
    """DROP TABLE IF EXISTS comments""",    
    #"""CREATE TABLE posts (id INT AUTO_INCREMENT, subject VARCHAR(100), body VARCHAR(255), PRIMARY KEY(id))""",
    """CREATE TABLE posts (id INTEGER PRIMARY KEY, subject VARCHAR(100), body VARCHAR(255))""",    
    """CREATE TABLE comments (id INT AUTO_INCREMENT, body VARCHAR(255),  posts_id INT, PRIMARY KEY(id))"""
]

class Post(Model):
    has_many("comments", orderby="id desc")

class Comment(Model):
    belongs_to("posts")

Model.establish_connection("sqlite://test.db")

for sql in CREATE: 
    print sql
    Model.__connection__(sql)


p = Post.create(
    {"subject": "first post", "body": "hello wordl"}, 
    {"subject": "second test", "body": "wow it seems to work"}
)
c1 = Comment.create(body="nice!", posts_id=p[0].id)
c2 = Comment.create(body="spam spam spam", posts_id=p[1].id)
c3 = Comment.create(body="second comment for second post", posts_id=p[1].id)
