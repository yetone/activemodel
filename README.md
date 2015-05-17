activemodel - an ActiveRecord implementation as seen in Rails for Python

# Description #

Every model class represents a table in the database. Instances of the class
represent rows of the table and the attributes of an instance are the
column values of the row.

Unlike other object relationional mappers (ORMs) you do not have to
specify the columns in the class. This follows the Don't-Repeat-Yourself
principle ([DRY](http://en.wikipedia.org/wiki/DRY_code)).

## Warning ##

This software is more or less a proof of concept and far from complete. It is neither
fully tested nor working without errors.

If you need a Python ORM _now_, please look at [SQLAlchemy](http://www.sqlalchemy.org)
or [SQLObject](http://www.sqlobject.org).


# How to use #

First you have to import the package
```
 >>> from activemodel import *
```
Then you define a class which is already in the database
```
 >>> class Post(Model): pass
```
That's it! You now can access your table.
```
 >>> first_post = Post.find(1)
 >>> print first_post.subject
 The ist my first post
 >>> new_post = Post.create(subject="New", body="blala")
```
If a column has the same name as a used method or class attribute or
is no valid Python attribute you can also access it as a dictionary item.
```
 >>> s = first_post["subject"]
```


## Model class ##

The class has the following attributes

  * table\_name
> > Normallly you write class names in singular CamelCase. By
> > convention tables are lower case and plural. So the name gets
> > translated to camel\_cases.
> > If your table has another name you can set it here.
```
     >>> class DataModel(Model):
     ...    table_name = "Model"
```
> > As you see it can be helpful if your table is a reserved word
> > in Python or you have a legacy table.
  * pluralize\_table\_names (default is True)
> > If you don't like plural names, you can disable it.
```
     >>> class Data(Model):
     ....   pluralize_table_names = False
```
> > When True the function activemodel.utils.pluralize tries to pluralize
> > the name according to English plural rules. See
> > [the wikipedia article](http://en.wikipedia.org/wiki/English_plural)
> > for more information.
> > You can also set it globally with
```
     >>> Model.pluralize_table_names = False
```
  * convert\_camelcase (default is True)
  * table\_columns
> > This is a dictionary with the column name and column object.
  * primary\_key (default is "id")
> > If your primary key is something else you can specify it here.
  * auto\_save (default is False)
> > When True the save method is called after every attribute change.


To open a database connection use the following class method
  * establish\_connection
```
   >>> Model.establish_connection("mysql://root@localhost/databasename")
```
> > You can also use keyword paramaters instead of a database url
```
   >>> Model.establisj_connection(adapter="mysql", database="test")
```


Some magic
  * When a table has an attribute called created\_on or created\_at, it
> > will be automatically set on create.
  * The attributes updated\_on and updated\_at are similar. They are
> > automatically set on update.


### Behaviours ###

**These will be explained when they are fully implemented**

  * has\_many
  * belongs\_to
  * has\_one
  * has\_and\_belongs\_to\_many
  * serialize - see activemodel/extensions/serialize.py for documentation


### Class Methods ###
  * create
```
     >>> first_post = Post.create(subject="first post!", body="bla bla")
```
> > This is the same as
```
     >>> first_post = Post(subject="first post!", body="bla bla")
     >>> first_post.save()
```
  * delete-methods
```
     >>> Post.delete(1)     # delete row with primary key = 1
     >>> Post.delete([1,3]) # delete row with primary key = 1 or 3
     >>> Post.delete_by_subject("first post!")
     >>> Post.delete_by_subject_and_body(
     ...      ["first_post!", "another subject"], "bla bla")
```
> > The by-methods will be dynamically generated and can contain one
> > or more column\_names.
  * find-methods
> > Like the delete-methods there are several ways to search.
> > When find(primarykey) does not find a row it will raise the
> > ModelNotFound exception.
```
     >>> p = Post.find(1)
     >>> p = Post.find_by_subject("first post!")
     >>> p = Post.find_by_subject(["first post!", "another subject"])
     >>> plist = Post.find_all_by_subject("spam")
     >>> plist = Post.find_all_by_subject_and_body("foo", "bar")
     >>> p = Post.find_by(subject_ne="spam")
     >>> plist = Post.find_all_by(id_gt=1)
```
  * find\_or\_create\_by
> > Instead of raising an error a new object will be created and saved.
```
     >>> p = Post.find_or_create_by_subject("hello, world!",
     ...        create_data={"body": "bye"})
```
> > The keyword parameter create\_data is optional and is used when no
> > object was found to create a new one together with the search data.
  * update


### Instance Methods ###
  * delete
```
     >>> Post.delete(1)
     >>> Post.delete_by_subject("first post!")  
```
  * save
  * update
  * to\_xml - see activemodel/extensions/toxml.py for documentation


## Query class ##
  * The functions select and where help to use query objects.
```
     >>> query = select(
     ...     Post.subject, Comment.id.count().as("comment_count")
     ...   ).where(
     ...      Post.id == Comment.posts_id
     ...	 ).order_by("comment_count").group_by(Post.id)
     >>> for row in query:
     ...    print "%r has %s comments" % (row["subject"], row["comment_count"]) 
```


## Extending ##
  * examples from serialize and toxml


# TODO #
  * more database backends (sqlite, postgresql)
  * fix and complete code with # XXX:
  * tag\_with/taggable
  * acts\_as
  * validation
  * migration