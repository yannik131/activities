from django.test import AsyncRequestFactory, TestCase, runner, Client
from .views import register
from django.contrib.auth.models import AnonymousUser
from shared.shared import log
from .models import User

class TestRunner(runner.DiscoverRunner):
    """ When migrations are disabled for the test runner, the `pre_migrate` signal
    does not emit.  So we need another hook for installing the extension.  Prior to
    Django 1.9, the `pre_syncdb` signal worked for that.
    """

    def setup_databases(self, **kwargs):
        """
        Always create PostgreSQL HSTORE extension if it doesn't already exist
        on the database before syncing the database. Requires PostgreSQL >= 9.1
        """

        def wrap_create_test_db(function):
            def decorated_create_test_db(self, verbosity, autoclobber, keepdb):
                test_database_name = function(self, verbosity, autoclobber, keepdb)
                self.connection.close()
                self.connection.settings_dict["NAME"] = test_database_name
                cursor = self.connection.cursor()
                cursor.execute('CREATE EXTENSION IF NOT EXISTS hstore')
                return test_database_name
            return decorated_create_test_db

        # Overriding class method from outside is ugly, but it's just for unit
        # testing anyway.
        from django.db.backends.base import creation
        creation.BaseDatabaseCreation._create_test_db = wrap_create_test_db(
            creation.BaseDatabaseCreation._create_test_db
        )

        return super(TestRunner, self).setup_databases(**kwargs)


class RegisterTest(TestCase):
    def setUp(self) -> None:
        self.factory = AsyncRequestFactory()
    
    def test_register(self):
        c = Client()
        response = c.post('/account/register/', {'email': 'yannik131@web.de', 'username': 'aha2', 'password': 'a password', 'password2': 'a password', 'address': 'Bremen'}, HTTP_HOST='myactivities.net:8000')
        self.assertEqual(response.status_code, 200)
        u = User.objects.filter(username='aha2')
        self.assertEqual(u.exists(), True)