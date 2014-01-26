import pytest
from mock import patch, call, Mock, MagicMock
import os

from blt.tools import bundle

# -- Set Fixtures -------------------------------------------------------------
@pytest.fixture
def cmds():
    config = {
        'bundle': {
            'BUNDLE_ROOT': '/tmp/bundles/',
            'LOCAL': 'sqlite://///Users/laphroaig/.virtualenvs/payinstr/db.sqlite3',
            'STAGING': 'sqlite://///Users/lagavulin/.virtualenvs/payinstr/db.sqlite3'
        },
        'django': {
            'DJANGO_ROOT': 'djangoproj'
        }
    }

    return bundle.BundleCommands(config)

# -- Setup/Teardown -----------------------------------------------------------

# Setup Module-wide mocks
bundle.local = Mock()
bundle.cd = MagicMock()

def teardown_function(function):
    """this is called after every test case runs"""
    bundle.local.reset_mock()
    bundle.cd.reset_mock()

# -- Test Cases! --------------------------------------------------------------
def test_dump(cmds):
    bundle.makedirs = Mock()
    cmds.dump('scotch-scotch-scotch', 'LOCAL')

    bundle.cd.assert_called_once_with('djangoproj')
    bundle.makedirs.assert_called_once_with('/tmp/bundles/scotch-scotch-scotch/db')
    assert os.environ.get('DATABASE_URL') == 'sqlite://///Users/laphroaig/.virtualenvs/payinstr/db.sqlite3'
    bundle.local.assert_called_once_with('python manage.py bundle dump scotch-scotch-scotch /tmp/bundles/scotch-scotch-scotch/db/fixture.xml')

def test_load(cmds):
    cmds.load('scotch-scotch-scotch', 'STAGING')

    bundle.cd.assert_called_once_with('djangoproj')
    assert os.environ.get('DATABASE_URL') == 'sqlite://///Users/lagavulin/.virtualenvs/payinstr/db.sqlite3'
    bundle.local.assert_called_once_with('python manage.py bundle load /tmp/bundles/scotch-scotch-scotch/db/fixture.xml')

def test_delete(cmds):
    cmds.delete('scotch-scotch-scotch', 'STAGING')

    bundle.cd.assert_called_once_with('djangoproj')
    assert os.environ.get('DATABASE_URL') == 'sqlite://///Users/lagavulin/.virtualenvs/payinstr/db.sqlite3'
    bundle.local.assert_called_once_with('python manage.py bundle delete scotch-scotch-scotch')


