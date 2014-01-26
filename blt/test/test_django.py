import pytest
from mock import patch, call, Mock, MagicMock

from blt.tools import django

# -- Set Fixtures -------------------------------------------------------------
@pytest.fixture
def cmds():
    config = {
        "django": {
            "DJANGO_ROOT": "djangoproj"
          , "PROJECT_DIR": "pubweb"
        }
    }

    return django.DjangoCommands(config)

# -- Setup/Teardown -----------------------------------------------------------

# Setup Module-wide mocks
django.local = Mock()
django.cd = MagicMock()

def teardown_function(function):
    """this is called after every test case runs"""
    django.local.reset_mock()
    django.cd.reset_mock()

# -- Test Cases! --------------------------------------------------------------
def test_up(cmds):
    django.prompt = Mock(return_value='yes')
    cmds.up()
    calls = [ call('pip install -r requirements.txt')
            , call('python manage.py syncdb')
            , call('python manage.py migrate')
            , call('python manage.py loaddata initial')
            , call('python manage.py collectstatic --noinput')
            , call('python manage.py assets build') ]

    django.local.assert_has_calls(calls)

def test_runserver(cmds):
    cmds.runserver()
    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_called_once_with('python manage.py runserver 127.0.0.1:8000')

def test_run_gunicorn(cmds):
    cmds.gunicorn_server()
    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_called_once_with('gunicorn --access-logfile=- --error-logfile=- pubweb.wsgi:application')

def test_shell(cmds):
    cmds.shell()
    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_called_once_with('python manage.py shell')

def test_test_no_args(cmds):
    cmds.test()
    calls = [
        call('find . -name "*.pyc" -exec rm -f {} \;'),
        call('py.test --ds pubweb.settings')
    ]

    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_has_calls(calls)

def test_test_specific_apps(cmds):
    cmds.test('invest', 'payment')
    calls = [
        call('find . -name "*.pyc" -exec rm -f {} \;'),
        call('py.test --ds pubweb.settings  invest payment')
    ]

    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_has_calls(calls)

def test_test_specific_tests(cmds):
    cmds.test('invest.test.commands_test')
    calls = [
        call('find . -name "*.pyc" -exec rm -f {} \;'),
        call('py.test --ds pubweb.settings  invest -k "test and commands_test"')
    ]

    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_has_calls(calls)

def test_cov_no_args(cmds):
    cmds.cov()
    calls = [
        call('find . -name "*.pyc" -exec rm -f {} \;'),
        call('coverage run  -m py.test --ds pubweb.settings'),
        call('coverage report'),
        call('coverage html -d coverage_html')
    ]

    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_has_calls(calls)

def test_cov_specific_apps(cmds):
    cmds.cov('invest', 'payment')
    calls = [
        call('find . -name "*.pyc" -exec rm -f {} \;'),
        call('coverage run --source invest,payment  -m py.test --ds pubweb.settings invest payment'),
        call('coverage report'),
        call('coverage html -d coverage_html')
    ]

    django.cd.assert_called_once_with('djangoproj')
    django.local.assert_has_calls(calls)

def test_covrpt(cmds):
    cmds.covrpt()

    django.local.assert_called_once_with('open coverage_html/index.html')
