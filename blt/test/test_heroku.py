import pytest
from mock import patch, call, Mock

from blt.tools import heroku

# -- Set Fixtures -------------------------------------------------------------
@pytest.fixture
def heroku_cmds():
    config = {
        "heroku": {
              "app": "pubweb-staging"
            , "git_remote": "heroku-staging"
            , "git_branch": "test-branch"
            , "addons": {
                "papertrail": "choklad"
                , "newrelic": "standard"
            }
            , "config": {
                  "DEBUG": "False"
                , "PRODUCTION": "True"
                , "SSL_ENABLED": "False"
            }
            , "post_deploy": [
                  "python djangoproj/manage.py syncdb"
                , "python djangoproj/manage.py migrate"
                , "python djangoproj/manage.py loaddata dev_data"
            ]
            , "domains": [
                  "app1.pubvest.com"
                , "app2.pubvest.com"
            ]
            , "migrate": [
                "python djangoproj/manage.py migrate"
            ]
        }
        , "blt_envtype": "staging"
    }

    return heroku.HerokuCommands(config)

# -- Setup/Teardown -----------------------------------------------------------

# Setup Module-wide mocks
heroku.local = Mock()

# def setup_function(function):
#     """this is called before every test case runs"""
#     heroku.cfg = heroku_config()

def teardown_function(function):
    """this is called after every test case runs"""
    heroku.local.reset_mock()

# -- Test Cases! --------------------------------------------------------------
def test_info(heroku_cmds):
    heroku_cmds.info()
    heroku.local.assert_called_once_with('heroku apps:info --app pubweb-staging')

def test_destroy(heroku_cmds):
    heroku_cmds.destroy()
    heroku.local.assert_called_once_with('heroku apps:destroy pubweb-staging')

def test_config_no_args(heroku_cmds):
    heroku_cmds.config()
    heroku.local.assert_called_once_with('heroku config --app pubweb-staging')

def test_config_set_default(heroku_cmds):
    heroku_cmds.config('set')
    heroku.local.assert_called_once_with('heroku config:set DEBUG=False SSL_ENABLED=False PRODUCTION=True --app pubweb-staging')

def test_config_cmd_and_args(heroku_cmds):
    heroku_cmds.config('set', 'Darth=Vader Han=Solo')
    heroku.local.assert_called_once_with('heroku config:set Darth=Vader Han=Solo --app pubweb-staging')

def test_addon_no_args(heroku_cmds):
    heroku_cmds.addon()
    heroku.local.assert_called_once_with('heroku addons --app pubweb-staging')

def test_addon_add_default(heroku_cmds):
    heroku_cmds.addon('add')
    calls = [call('heroku addons:add papertrail:choklad --app pubweb-staging')
            , call('heroku addons:add newrelic:standard --app pubweb-staging')]
    heroku.local.assert_has_calls(calls)

def test_addon_cmd_and_args(heroku_cmds):
    heroku_cmds.addon('add', 'Darth:Vader')
    heroku.local.assert_called_once_with('heroku addons:add Darth:Vader --app pubweb-staging')

def test_push(heroku_cmds):
    heroku_cmds.push()
    heroku.local.assert_called_once_with('git push heroku-staging test-branch:master')

def test_push_with_force(heroku_cmds):
    heroku_cmds.push('force')
    heroku.local.assert_called_once_with('git push heroku-staging test-branch:master --force')

def test_create(heroku_cmds):
    heroku.prompt = Mock(return_value='yes')
    heroku_cmds.create()
    calls = [call('heroku apps:create pubweb-staging --remote heroku-staging')
            , call('heroku config:set DEBUG=False SSL_ENABLED=False PRODUCTION=True --app pubweb-staging')
            , call('git push heroku-staging test-branch:master')
            , call('heroku addons:add papertrail:choklad --app pubweb-staging')
            , call('heroku addons:add newrelic:standard --app pubweb-staging')
            , call('heroku domains:add app1.pubvest.com --app pubweb-staging')
            , call('heroku domains:add app2.pubvest.com --app pubweb-staging')
            , call('heroku run "python djangoproj/manage.py syncdb" --app pubweb-staging')
            , call('heroku run "python djangoproj/manage.py migrate" --app pubweb-staging')]

    heroku.local.assert_has_calls(calls)

def test_run(heroku_cmds):
    heroku_cmds.run('python manage.py runserver')
    heroku.local.assert_called_once_with('heroku run "python manage.py runserver" --app pubweb-staging')

def test_domain_no_args(heroku_cmds):
    heroku_cmds.domain()
    heroku.local.assert_called_once_with('heroku domains --app pubweb-staging')

def test_domain_add_default(heroku_cmds):
    heroku_cmds.domain('add')
    calls = [call('heroku domains:add app1.pubvest.com --app pubweb-staging')
            , call('heroku domains:add app2.pubvest.com --app pubweb-staging')]
    heroku.local.assert_has_calls(calls)

def test_domain_cmd_and_args(heroku_cmds):
    heroku_cmds.domain('add', 'app3.pubvest.com')
    heroku.local.assert_called_once_with('heroku domains:add app3.pubvest.com --app pubweb-staging')

def test_migrate(heroku_cmds):
    heroku_cmds.migrate()
    heroku.local.assert_called_once_with('heroku run "python djangoproj/manage.py migrate" --app pubweb-staging')
