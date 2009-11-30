from django.conf import settings
from django.db.backends.creation import BaseDatabaseCreation

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated MySQL column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    data_types = {
        'AutoField':         'integer AUTO_INCREMENT',
        'BooleanField':      'bool',
        'CharField':         'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField':         'date',
        'DateTimeField':     'datetime',
        'DecimalField':      'numeric(%(max_digits)s, %(decimal_places)s)',
        'FileField':         'varchar(%(max_length)s)',
        'FilePathField':     'varchar(%(max_length)s)',
        'FloatField':        'double precision',
        'IntegerField':      'integer',
        'IPAddressField':    'char(15)',
        'NullBooleanField':  'bool',
        'OneToOneField':     'integer',
        'PositiveIntegerField': 'integer UNSIGNED',
        'PositiveSmallIntegerField': 'smallint UNSIGNED',
        'SlugField':         'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField':         'longtext',
        'TimeField':         'time',
    }

    def sql_table_creation_suffix(self):
        suffix = []
        if settings.TEST_DATABASE_CHARSET:
            suffix.append('CHARACTER SET %s' % settings.TEST_DATABASE_CHARSET)
        if settings.TEST_DATABASE_COLLATION:
            suffix.append('COLLATE %s' % settings.TEST_DATABASE_COLLATION)
        return ' '.join(suffix)

    def sql_for_inline_foreign_key_references(self, field, known_models, style):
        "All inline references are pending under MySQL"
        return [], True
        
    def sql_for_inline_many_to_many_references(self, model, field, style):
        from django.db import models
        opts = model._meta
        qn = self.connection.ops.quote_name
        
        table_output = [
            '    %s %s %s,' %
                (style.SQL_FIELD(qn(field.m2m_column_name())),
                style.SQL_COLTYPE(models.ForeignKey(model).db_type()),
                style.SQL_KEYWORD('NOT NULL')),
            '    %s %s %s,' %
            (style.SQL_FIELD(qn(field.m2m_reverse_name())),
            style.SQL_COLTYPE(models.ForeignKey(field.rel.to).db_type()),
            style.SQL_KEYWORD('NOT NULL'))
        ]
        deferred = [
            (field.m2m_db_table(), field.m2m_column_name(), opts.db_table,
                opts.pk.column),
            (field.m2m_db_table(), field.m2m_reverse_name(),
                field.rel.to._meta.db_table, field.rel.to._meta.pk.column)
            ]
        return table_output, deferred

    def _create_test_db(self, verbosity, autoclobber):
        "Internal implementation - creates the test db tables."
        suffix = self.sql_table_creation_suffix()

        if settings.TEST_DATABASE_NAME:
            test_database_name = settings.TEST_DATABASE_NAME
        else:
            test_database_name = TEST_DATABASE_PREFIX + settings.DATABASE_NAME

        qn = self.connection.ops.quote_name

        # Create the test database and connect to it. We need to autocommit
        # if the database supports it because PostgreSQL doesn't allow
        # CREATE/DROP DATABASE statements within transactions.
        cursor = self.connection.cursor()
        self.set_autocommit()
        try:
            cursor.execute("CREATE DATABASE %s %s" % (qn(test_database_name), suffix), plain_query=True)
        except Exception, e:
            sys.stderr.write("Got an error creating the test database: %s\n" % e)
            if not autoclobber:
                confirm = raw_input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)
            if autoclobber or confirm == 'yes':
                try:
                    if verbosity >= 1:
                        print "Destroying old test database..."
                    cursor.execute("DROP DATABASE %s" % qn(test_database_name), plain_query=True)
                    if verbosity >= 1:
                        print "Creating test database..."
                    cursor.execute("CREATE DATABASE %s %s" % (qn(test_database_name), suffix), plain_query=True)
                except Exception, e:
                    sys.stderr.write("Got an error recreating the test database: %s\n" % e)
                    sys.exit(2)
            else:
                print "Tests cancelled."
                sys.exit(1)

        return test_database_name