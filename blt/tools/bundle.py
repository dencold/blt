"""
Toolset module for migrating content bundles between django environments.

This tool provides several helpers around Heston's content management system
for deal offerings on the platform. In order to make deals portable between
environments, blt interfaces with a set of custom django management commands
to dump/load/delete deals on the system.

Author: @dencold (Dennis Coldwell)
"""
from blt.environment import Commander
from blt.helpers import local, prompt, cd, abort, puts

from os import environ, makedirs, path


class BundleCommands(Commander):
    """Commander class for content bundles."""

    def dump(self, deal_slug, database):
        """
        Dumps a given deal out to a fixture file.

        This makes use of the custom django management command which
        encapsulates the logic to pull out all of the important model data for
        a deal. It uses the passed "database" arg to pull the appropriate
        DATABASE_URL from the bltenv settings. It outputs the fixture to the
        configured BUNDLE_ROOT.

        Args:
            deal_slug: the unique slug for the deal
            database: the database to dump from

        Usage:
            blt bundle.dump (deal_slug) (database)

        Examples:
            blt bundle.dump blumhouse-productions STAGING
        """
        environ['DATABASE_URL'] = self.cfg['bundle'][database]
        fixture_file = self._fixture_file(deal_slug)
        self._prep_bundle_dir(path.split(fixture_file)[0])

        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('python manage.py bundle dump %s %s' % (deal_slug,
                                                          fixture_file))

    def load(self, deal_slug, database):
        """
        Loads a deal from a fixture file.

        This will load the fixture located in the BUNDLE_ROOT directory to the
        passed in database target. Special care has been taken to allow this
        command to detect previously loaded data and can be run multiple times
        without affecting existing database entries. If you need to push a fresh
        update, use the ``delete`` command to start with a fresh slate.

        Args:
            deal_slug: the unique slug for the deal
            database: the database to load into

        Usage:
            blt bundle.load (deal_slug) (database)

        Examples:
            blt bundle.load blumhouse-productions PRODUCTION
        """
        environ['DATABASE_URL'] = self.cfg['bundle'][database]
        fixture_file = self._fixture_file(deal_slug)

        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('python manage.py bundle load %s' % fixture_file)

    def delete(self, deal_slug, database):
        """
        Deletes a deal on the platform.

        This will completely delete the deal and all related objects on the
        passed in database. Because we view bundles as atomic units and never
        overwrite any existing entries on the database, you are required to
        run this command if you want update anything in the db.

        Args:
            deal_slug: the unique slug for the deal
            database: the database to delete from

        Usage:
            blt bundle.delete (deal_slug) (database)

        Examples:
            blt bundle.delete blumhouse-productions STAGING
        """
        environ['DATABASE_URL'] = self.cfg['bundle'][database]

        with cd(self.cfg['django']['DJANGO_ROOT']):
            local('python manage.py bundle delete %s' % (deal_slug))

    def _fixture_file(self, deal_slug):
        """
        Determines the full path to the deal's fixture file.

        Given a deal slug, this method will determine the path to the
        fixture.xml file using the BUNDLE_ROOT.

        Args:
            deal_slug: the unique slug for the deal

        Returns:
            A string representing the absolute path to the deal's fixture file
        """
        return path.join(self.cfg['bundle']['BUNDLE_ROOT'],
                         deal_slug,
                         'db',
                         'fixture.xml')

    def _prep_bundle_dir(self, dir):
        """
        Sets up the bundle dir from blt configuration

        Checks if the path exists and if not, creates the full directory
        structure.

        Args:
            dir: the directory path to create
        """
        try:
            if not path.isdir(dir):
                makedirs(dir)
                puts("Created bundle db dir: %s" % dir)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and path.isdir(dir):
                pass
            else:
                raise

