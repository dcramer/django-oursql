A simple database backend for Django to utilize the oursql connector.

Install with setuptools or pip::

	pip install django-oursql

Update your sttings::

	DATABASES = {
	    'default': {
	        'ENGINE': 'mysql_oursql.standard',
	        # or 'mysql_oursql.gis'
	    },
	}

For more information about oursql, check the docs: http://packages.python.org/oursql/