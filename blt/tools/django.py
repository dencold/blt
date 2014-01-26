"""
Toolset module for django commands.

Author: @dencold (Dennis Coldwell)
"""
from os import environ

from blt.environment import Commander, import_file
from blt.helpers import local, prompt, cd, abort


class DjangoCommands(Commander):
    """Commander class for Django commands"""

    def up(self):
        """
        Update a django environment with latest settings.

        This command does everything required to get a django project running.
        These are the steps that will be executed when the command is issued:

        1. pip install requirements
        2. syncdb
        3. migrate
        4. loaddata initial
        5. collectstatic
        6. assets build

        It has been designed with rerunning in mind and can be safely executed
        without any unwelcome side affects. For example, any pip packages that
        have already been installed will be skipped on rerun. Any database
        tables will be preserved (no dropping data), etc.

        Note that this must be run in a virtualenv. blt will detect if you are
        not using one and will barf with a helpful error.

        Usage:
            blt django.up
        """
        django_root = self.cfg['django']['DJANGO_ROOT']

        # install packages from pip's requirements.txt
        local('pip install -r requirements.txt')

        with cd(django_root):
            try:
                local('python manage.py syncdb')
                local('python manage.py migrate')
            except:
                msg = '\n'.join(["ERROR: Python couldn't find django.  Are you in a virtualenv?"
                                , "Try workon MY_SWEET_VIRTENV_HERE"])
                abort(msg)

        with cd(django_root):
            # Load dev data
            local('python manage.py loaddata initial')

            # collect static files
            local('python manage.py collectstatic --noinput')

            # Compile static asset bundles
            local('python manage.py assets build')

    def runserver(self, ip='127.0.0.1', port='8000'):
        """
        Runs django's development http server

        Args:
            ip: the ip address to host on, default is 127.0.0.1
            port: the port on host server, default is 8000

        Usage:
            blt django.runserver [ip] [port]

        Examples:
            blt django.runserver - default, runs on 127.0.0.1:8000
            blt django.runserver 10.1.156.3 - runs on 10.1.156.3:8000
            blt django.runserver 10.1.156.3 8888 - runs on 10.1.156.3:8888
        """
        with cd(self.cfg['django']['DJANGO_ROOT']):
            print "Setting ASSETS_DEBUG=True"
            environ['ASSETS_DEBUG'] = "True"
            local('python manage.py runserver %s:%s' % (ip, port))

    def gunicorn_server(self, *args):
        "Runs Gunicorn server for pseudo-production testing."
        project = self.cfg['django']['PROJECT_DIR']
        args_str = ''.join(args)

        with cd(self.cfg['django']['DJANGO_ROOT']):
            flag_str = '%s --access-logfile=- --error-logfile=-' % args_str
            local('gunicorn %s %s.wsgi:application' % (flag_str, project))

    def collectstatic(self):
        """Runs django's collectstatic and the webassets build in one command"""
        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('python manage.py collectstatic --noinput')
            local('python manage.py assets build')

    def shell(self):
        """Opens a session to django's shell"""
        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('python manage.py shell')

    def test(self, *apps):
        """
        Runs py.test for the django project.

        If <apps> is empty, all tests will be run. Otherwise, tests may be specified in the
        following way: <appname>[.<search_phrase_1>[.<search_phrase_2>...<search_phrase_n>]].

        For example, given an app named "my_app" and a test defined by unittest as
        "MyTestCase.test_something" the following command would run just that test:
        "blt django.test my_app.MyTestCase.test_something". To run every test in the test case:
        "blt django.test my_app.MyTestCase". Or, to run every test for the app:
        "blt django.test my_app".

        Specifying multiple apps is also possible: "blt django.test my_app,my_other_app,your_app".
        However, due to the way test searching is performed by py.test, it is not recommended
        to use search phrases when testing multiple apps.

        Usage:
            blt django.test [apps]

        Examples:
            blt django.test - default, runs all tests in the project
            blt django.test my_app1 my_app2 - runs all tests for my_app1 and my_app2
            blt django.test my_app.test_case - runs the test_case in my_app
        """
        project = self.cfg['django']['PROJECT_DIR']

        # first clear out any .pyc files.  these are cached and could provide
        # bad test results.  example: you import a module in your test case,
        # but have deleted it on the filesystem.  if the .pyc file still
        # exists, the test will still pass.
        local('find . -name "*.pyc" -exec rm -f {} \;')

        test_names = []
        app_names = []
        flags = []
        args = []

        for n in apps:
            if n.startswith('-'):
                flags.append(n)
            elif '.' in n:
                a, t = n.split('.', 1)
                app_names.append(a)
                test_names += t.split('.')
            else:
                app_names.append(n)

        args.append(' '.join(flags))
        args.append(' '.join(app_names))
        args.append('-k "%s"' % ' and '.join(test_names) if len(test_names) else '')
        command = 'py.test --ds {0}.settings {1}'.format(project,
                                                         ' '.join(args)).strip()

        with cd(self.cfg['django']['DJANGO_ROOT']):
            local(command)

    def cov(self, *apps):
        """
        Runs coverage for the django project.

        Note that this command will run the py.test suite first as it is required
        for generating the coverage report. If you'd like to filter to a specific
        set of apps, you can pass it into this command.

        Usage:
            blt django.cov [apps] [flags]

        Examples:
            blt django.cov - default, runs coverage for the entire project
            blt django.cov my_app1 my_app2 - runs coverage for my_app1 and my_app2
        """
        project = self.cfg['django']['PROJECT_DIR']

        # first clear out any .pyc files.  these are cached and could provide
        # bad test results.  example: you import a module in your test case,
        # but have deleted it on the filesystem.  if the .pyc file still
        # exists, the test will still pass.
        local('find . -name "*.pyc" -exec rm -f {} \;')

        app_names = []
        flags = []
        pytest_args = []
        cov_args = []

        for n in apps:
            if n.startswith('-'):
                flags.append(n)
            else:
                app_names.append(n)

        # setup py.test args
        pytest_args = ' '.join(app_names)
        cov_args = ','.join(app_names)

        if app_names:
            cmd = 'coverage run --source {0} {1} -m py.test --ds {2}.settings {3}'.format(
                cov_args,
                ' '.join(flags),
                project,
                pytest_args).strip()
        else:
            cmd = 'coverage run {0} -m py.test --ds {1}.settings'.format(
                ' '.join(flags),
                project).strip()


        with cd(self.cfg['django']['DJANGO_ROOT']):
            local(cmd)
            local('coverage report')
            local('coverage html -d coverage_html')

    def covrpt(self):
        """
        This will open the html version of the coverage report in your browser.

        Usage:
            blt django.covrpt
        """
        project = self.cfg['django']['PROJECT_DIR']

        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('open coverage_html/index.html')
