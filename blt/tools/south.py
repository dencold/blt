"""
Toolset module for interfacing with South.

South is a great tool for django migrations, but it has a rather unfriendly API
when doing anything but the simple migration workflow. This module hopes to
resolve that by wrapping into a set of normalized commands.

Author: @dencold (Dennis Coldwell)
"""
from blt.environment import Commander
from blt.helpers import local, prompt, cd, abort
from clint.textui import puts, indent

class SouthCommands(Commander):
    """Commander class for South."""

    def status(self, app=None):
        """
        Check the status of outstanding database migrations.

        Sadly, south gives us no easy api access to get status of what models
        have changed on an app. It only spits out the summary of changes to
        stderr and the actual Migration classes to stdout. The status command
        tries to encapsulate and parse this out to be helpful, but it is
        obviously brittle and should be tested whenever we upgrade the south
        library.

        Args:
            app: django app to check status for

        Usage:
            blt south.status (app)

        Examples:
            blt south.status invest - displays status for the invest app
        """
        if not app:
            msg = ("\nsouth status requires an *app* to check. for example:\n"
                    , "    blt south.status my_app\n"
                    , "To check which apps have had model changes run:\n"
                    , "    git status | grep models.py")
            abort("\n".join(msg))

        with cd(self.cfg['django']['DJANGO_ROOT']):
            puts("-- Model Check -----------------------------------------------------------")
            out = local('python manage.py schemamigration %s --auto --stdout 2>&1' % app,
                collect_output=True, abort_on_stderr=False)

            if out.strip() == 'Nothing seems to have changed.':
                puts("Model is in sync with migrations")
            else:
                puts("Model changes found:\n\n%s" % out)
                puts("\n==> Run `blt south.delta %s` to create a migration set." % app)

            puts("\n-- Unapplied Migrations --------------------------------------------------")
            out = local('python manage.py migrate %s --list | grep -v "*" 2>&1' % app,
                collect_output=True)

            if out.strip() == app:
                puts("All migrations have been applied to db")
            else:
                puts("Migrations need to be applied to db:\n%s" % out.strip())
                puts("\n==> Run `blt south.apply` to push to the database\n")

    def delta(self, *apps):
        """
        Creates a new schema changeset for an app.

        Unfortunately, south doesn't allow project-wide schemamigrations, you
        have to provide a specific app name.

        Args:
            apps: a list of apps to create changesets for

        Usage:
            blt south.delta (apps)

        Examples:
            blt south.delta invest payment - creates deltas for invest and
                payment apps
        """
        if not apps:
            abort('\n\nPlease provide an app name, e.g. \n    blt south.delta my_app')

        with cd(self.cfg['django']['DJANGO_ROOT']):
            for app in apps:
                local('python manage.py schemamigration %s --auto' % app)

    def migrate(self, *apps):
        """
        Applies all outstanding deltas to the database.

        Here the south API is a little friendlier and you can apply migrations
        to the entire django project. Or, if you so desire, you can apply only
        to specific apps. Just pass the list as an argument.

        Args:
            apps: list of apps to apply migrations, if none given, will run
                migrations across the entire project

        Usage:
            blt south.migrate [apps]

        Examples:
            blt south.migrate - default, runs all migrations
            blt south.migrate invest payment - runs migrations for invest and
                payment apps
        """
        with cd(self.cfg['django']['DJANGO_ROOT']):
            if not apps:
                local('python manage.py migrate')
            else:
                for app in apps:
                    local('python manage.py migrate %s' % app)
