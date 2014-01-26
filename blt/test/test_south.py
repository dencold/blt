import pytest
from mock import patch, call, Mock, MagicMock

from blt.tools import south

# -- Set Fixtures -------------------------------------------------------------
@pytest.fixture
def cmds():
    config = {
        "django": {
            "DJANGO_ROOT": "djangoproj"
          , "PROJECT_DIR": "pubweb"
        }
    }

    return south.SouthCommands(config)

# -- Setup/Teardown -----------------------------------------------------------

# Setup Module-wide mocks
south.local = Mock()
south.cd = MagicMock()

def teardown_function(function):
    """this is called after every test case runs"""
    south.local.reset_mock()
    south.cd.reset_mock()

# -- Test Cases! --------------------------------------------------------------
def test_delta(cmds):
    cmds.delta('invest', 'payment')
    calls = [ call('python manage.py schemamigration invest --auto')
            , call('python manage.py schemamigration payment --auto')]

    south.cd.assert_called_once_with('djangoproj')
    south.local.assert_has_calls(calls)

def test_migrate(cmds):
    cmds.migrate('invest')
    south.cd.assert_called_once_with('djangoproj')
    south.local.assert_called_once_with('python manage.py migrate invest')
