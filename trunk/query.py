from activemodel import *

class Post(Model): has_many("comments", orderby="id desc")
class Comment(Model): belongs_to("posts")
Model.establish_connection("mysql://root@localhost/test")



print where(Post.id.IN(1) | (Post.id == 0) | (Post.id == 4))

# XXX: implement left join
query = select(
            Post.subject, Comment.id.count().as("comment_count")
        ).where(
            Post.id == Comment.posts_id
        ).order_by("comment_count").group_by(Post.id)
print query

for row in query:
    print "%r has %s comments" % (row["subject"], row["comment_count"])