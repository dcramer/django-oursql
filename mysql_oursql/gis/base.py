from mysql_oursql.standard.base import DatabaseWrapper as MySQLDatabaseWrapper
from mysql_oursql.gis.creation import MySQLCreation
from mysql_oursql.gis.introspection import MySQLIntrospection
from mysql_oursql.gis.operations import MySQLOperations

class DatabaseWrapper(MySQLDatabaseWrapper):

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = MySQLCreation(self)
        self.ops = MySQLOperations()
        self.introspection = MySQLIntrospection(self)
