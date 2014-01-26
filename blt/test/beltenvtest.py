from blt.environment import Commander
import importedtest


class TestCommands(Commander):

    def standard_command(self):
        pass

    def default_command(self):
        pass

    def some_really_long_aliased_command(self):
        pass

    def command_with_aliases(self):
        pass


CONFIG = {
    "staging": {
        "heroku": {
              "app": "pubweb-staging"
            , "git_remote": "heroku-staging"
            , "git_branch": "master"
            , "addons": {
                  "papertrail": "choklad"
                , "newrelic": "standard"
            }
            , "config": {
                  "DEBUG": "False"
                , "PRODUCTION": "True"
                , "SSL_ENABLED": "False"
                , "DEFAULT_FROM_EMAIL": "registration-staging@pubvest.com"
                , "CONSOLE_LOG_LEVEL": "ERROR"
                , "BASIC_WWW_AUTHENTICATION": "False"
                , "SITE_URL": "http://pubweb-staging.herokuapp.com"
                , "STATIC_URL": "http://538927538.cloudfront.net/static/"
            }
            , "post_deploy": [
                  "python djangoproj/manage.py syncdb"
                , "python djangoproj/manage.py migrate"
                , "python djangoproj/manage.py loaddata dev_data"
            ]
        }
    }
    , "production": {
        "heroku": {
              "app": "pubweb-production"
            , "git_remote": "heroku-production"
            , "git_branch": "master"
            , "addons": {
                  "papertrail": "choklad"
                , "newrelic": "standard"
            }
            , "config": {
                  "DEBUG": "False"
                , "PRODUCTION": "True"
                , "SSL_ENABLED": "True"
                , "DEFAULT_FROM_EMAIL": "registration@pubvest.com"
                , "CONSOLE_LOG_LEVEL": "ERROR"
                , "BASIC_WWW_AUTHENTICATION": "False"
                , "SITE_URL": "https://pubvest.com"
                , "STATIC_URL": "http://58912221828.cloudfront.net/static/"
            }
            , "post_deploy": [
                  "python djangoproj/manage.py syncdb"
                , "python djangoproj/manage.py migrate"
                , "python djangoproj/manage.py loaddata dev_data"
            ]
        }
    }
}
