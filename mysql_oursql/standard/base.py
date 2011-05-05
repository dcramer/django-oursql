"""
MySQL database backend for Django.

Requires oursql: https://launchpad.net/oursql
"""

import sys
import re

try:
    import oursql as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading oursql module: %s" % e)

from django.db import utils
from django.db.backends import *
from django.db.backends.signals import connection_created
from mysql_oursql.standard.client import DatabaseClient
from mysql_oursql.standard.creation import DatabaseCreation
from mysql_oursql.standard.introspection import DatabaseIntrospection
from mysql_oursql.standard.validation import DatabaseValidation
from mysql_oursql.standard.operations import DatabaseOperations
# from django.utils.safestring import SafeString, SafeUnicode

# Raise exceptions for database warnings if DEBUG is on
from django.conf import settings
if settings.DEBUG:
    from warnings import filterwarnings
    filterwarnings("error", category=Database.Warning)

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

# This should match the numerical portion of the version numbers (we can treat
# versions like 5.0.24 and 5.0.24a as the same). Based on the list of version
# at http://dev.mysql.com/doc/refman/4.1/en/news.html and
# http://dev.mysql.com/doc/refman/5.0/en/news.html .
server_version_re = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{1,2})')

params_re = re.compile(r'%[a-zA-Z]')

# TODO: monkey patch django to support our package in areas such as GIS is not a good solution
try:
    from django.conf import settings
    if settings.DATABASE_ENGINE.startswith('mysql'):
        settings.DATABASE_ENGINE = 'mysql'
except ImportError:
    pass

class CursorWrapper(object):
    """
    A thin wrapper around oursql's normal cursor class so that we can catch
    particular exception instances and reraise them with the right types.

    Implemented as a wrapper, rather than a subclass, so that we aren't stuck
    to the particular underlying representation returned by Connection.cursor().
    """
    codes_for_integrityerror = (1048,)

    def __init__(self, cursor):
        self.cursor = cursor
        
    def _replace_params(self, query):
        return params_re.sub('?', query)

    def execute(self, query, args=(), **kwargs):
        query = self._replace_params(query)
        try:
            return self.cursor.execute(query, args, **kwargs)
        except Database.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except Database.OperationalError, e:
            # Map some error codes to IntegrityError, since they seem to be
            # misclassified and Django would prefer the more logical place.
            if e[0] in self.codes_for_integrityerror:
                raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
            raise

    def executemany(self, query, args, **kwargs):
        query = self._replace_params(query)
        try:
            return self.cursor.executemany(query, args, **kwargs)
        except Database.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except Database.OperationalError, e:
            # Map some error codes to IntegrityError, since they seem to be
            # misclassified and Django would prefer the more logical place.
            if e[0] in self.codes_for_integrityerror:
                raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
            raise

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

class DatabaseFeatures(BaseDatabaseFeatures):
    empty_fetchmany_value = []
    update_can_self_select = False
    allows_group_by_pk = True
    related_fields_match_type = True

class DatabaseWrapper(BaseDatabaseWrapper):
    operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE BINARY %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE BINARY %s',
        'endswith': 'LIKE BINARY %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.server_version = None
        self.features = DatabaseFeatures()
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

    def _valid_connection(self):
        if self.connection is not None:
            try:
                self.connection.ping()
                return True
            except DatabaseError:
                self.connection.close()
                self.connection = None
        return False

    def _cursor(self):
        if not self._valid_connection():
            kwargs = {
                'charset': 'utf8',
                'use_unicode': True,
            }
            settings_dict = self.settings_dict
            if settings_dict['USER']:
                kwargs['user'] = settings_dict['USER']
            if settings_dict['NAME']:
                kwargs['db'] = settings_dict['NAME']
            if settings_dict['PASSWORD']:
                kwargs['passwd'] = settings_dict['PASSWORD']
            if settings_dict['HOST'].startswith('/'):
                kwargs['unix_socket'] = settings_dict['HOST']
            elif settings_dict['HOST']:
                kwargs['host'] = settings_dict['HOST']
            if settings_dict['PORT']:
                kwargs['port'] = int(settings_dict['PORT'])
            # We need the number of potentially affected rows after an
            # "UPDATE", not the number of changed rows.
            kwargs['found_rows'] = True
            # TODO: support for 'init_command'
            kwargs.update(settings_dict['OPTIONS'])
            self.connection = Database.connect(**kwargs)
            # XXX: oursql does not have encoders like mysqldb -- unknown if this is still needed
            # self.connection.encoders[SafeUnicode] = self.connection.encoders[unicode]
            # self.connection.encoders[SafeString] = self.connection.encoders[str]
            connection_created.send(sender=self.__class__)
        cursor = CursorWrapper(self.connection.cursor())
        return cursor

    def _rollback(self):
        try:
            BaseDatabaseWrapper._rollback(self)
        except Database.NotSupportedError:
            pass

    def get_server_version(self):
        if not self.server_version:
            if not self._valid_connection():
                self.cursor()
            m = server_version_re.match(self.connection.server_info)
            if not m:
                raise Exception('Unable to determine MySQL version from version string %r' % self.connection.server_info)
            self.server_version = tuple([int(x) for x in m.groups()])
        return self.server_version
