# Activemodel #

_Python already has tons of SQL-wrappers and ORMs and some are quite good. Nevertheless I started my own. Mainly to see if it is possible to implement the API used in Rails._

Some parts required a lot of tricks and magic metaclasses. But in the end it worked well.

Every model class represents a table in the database. Instances of the class represent rows of the table and the attributes of an instance are the column values of the row.

Unlike other object relationional mappers (ORMs) you do not have to specify the columns in the class. This follows the Don't-Repeat-Yourself principle (DRY).

Additionsally I added query features as seen in Django, SQLAlchemy and SQLObject.

The only supported database at the moment is MySQL but SQLite and other backends will follow probably.

Unlike Rails activemodel currently provides no mechanism for migration or validation.


Please read the [README](README.md) in the wiki for more information.


Please send questions and feedback to henning.schroeder (at) gmail (dot) com