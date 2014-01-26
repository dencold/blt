"""
Toolset module for interfacing with Heroku.

Makes heavy use of the heroku toolbelt and makes several of the common
operations more user friendly and intuitive.

Author: @dencold (Dennis Coldwell)
"""
from clint.textui.colored import blue, red, green

from blt.environment import Commander
from blt.helpers import local, prompt, abort


class HerokuCommands(Commander):
    """Commander class for Heroku"""
    def info(self):
        """
        Shows the info for your current heroku environment

        Usage:
            blt e:[env] heroku.info
        """
        local('heroku apps:info --app %s' % self.cfg['heroku']['app'])

    def create(self):
        """
        Provisions a fully configured heroku app from scratch.

        Behind the scenes, you're getting the following:
        - heroku apps:create
        - git push heroku
        - heroku config
        - heroku addons
        - heroku domains
        - all post deploy hooks

        The command will handle creating a special git remote for the
        environment and can push from a non-master branch, things which are not
        easily accomplished with the heroku toolbelt. This is driven from the
        bltenv configuration.

        Usage:
            blt e:[env] heroku.create
        """
        print "******** Creating New Heroku App ********"
        print "App Name: " + green(self.cfg['heroku']['app'])
        print "Environment: " + green(self.cfg['blt_envtype'])
        print "Branch: " + green(self.cfg['heroku']['git_branch'])
        proceed = prompt("\nLook good? ==>", default='no')

        if proceed.lower() != 'yes' and proceed.lower() != 'y':
            abort('Aborting heroku creation.')

        local('heroku apps:create %s --remote %s' % (self.cfg['heroku']['app']
                                            , self.cfg['heroku']['git_remote']))
        self.config('set')
        self.push()
        self.addon('add')

        # if we have domains configured, add them
        if 'domains' in self.cfg['heroku']:
            self.domain('add')

        # handle post deploy steps
        self.run(*self.cfg['heroku']['post_deploy'])

        print '\nHeroku Deploy Complete!'
        url = '==> http://%s.herokuapp.com/' % self.cfg['heroku']['app']
        print url

    def destroy(self):
        """
        Destroys a heroku app.

        The heroku toolbelt will verify this operation before executing.

        Usage:
            blt e:[env] heroku.destroy
        """
        local('heroku apps:destroy %s' % self.cfg['heroku']['app'])

    def push(self, git_arg=''):
        """
        Pushes your local git branch to heroku.

        We handle pushing from a non-master branch for you, just set
        ``git_branch`` in your beltenv configuration.

        Args:
            git_arg: any valid argument to git push (optional)

        Usage:
            blt e:[env] heroku.push [arg]

        Examples:
            blt e:s heroku.push - pushes branch to heroku staging environment
            blt e:s heroku.push force - forces a push to heroku staging
            blt e:p heroku.push verbose - pushes to production in verbose mode
        """
        if git_arg:
            local('git push %s %s:master --%s' % (self.cfg['heroku']['git_remote']
                                                    , self.cfg['heroku']['git_branch']
                                                    , git_arg))
        else:
            local('git push %s %s:master' % (self.cfg['heroku']['git_remote']
                                            , self.cfg['heroku']['git_branch']))

    def config(self, action='', *configs):
        """
        Executes a set/get/unset action to the remote heroku config.

        Args:
            action: string config action. either set, get, or unset
            configs: list of configurations

        Usage:
            blt e:[env] heroku.config [set|get|unset] ["Key=Value"]

        Examples:
            blt e:s heroku.config - default lists the current config on staging
            blt e:s heroku.config set - sets *ALL* config defined in beltenv
                configuration file on heroku
            blt e:p heroku.config set "SSL_ENABLED=True" - sets the SSL_ENABLED
                config setting to True in production
            blt e:p heroku.config unset SSL_ENABLED - unsets the SSL_ENABLED
                config setting
        """
        if not action:
            local('heroku config --app %s' % self.cfg['heroku']['app'])
        else:
            if not configs:
                # if we don't have any runtime configs from the commandline,
                # we want to run a list comprehension to convert all of the
                # items in the beltenv configuration dict into a list of
                # "key=value" strings:
                configs = [''.join([k,'=',v])
                    for k,v in self.cfg['heroku']['config'].iteritems()]

            local('heroku config:%s %s --app %s' % (action
                                                    , ' '.join(configs)
                                                    , self.cfg['heroku']['app']))

    def addon(self, action='', *addons):
        """
        Executes an add/remove/upgrade action to the remote heroku addons.

        Args:
            action: string addon action. either add, remove, or upgrade
            addons: list of addons

        Usage:
            blt e:[env] heroku.addon [add|remove|upgrade] ["addon:level"]

        Examples:
            blt e:s heroku.addon - default lists the current addons on staging
            blt e:s heroku.addon add - adds *ALL* addons defined in beltenv
                configuration file
            blt e:p heroku.addon add "newrelic:standard" - adds the standard
                version of newrelic in production
            blt e:p heroku.addon remove newrelic - removes newrelic from prod
        """
        if not action:
            local('heroku addons --app %s' % self.cfg['heroku']['app'])
        else:
            if not addons:
                # much like the "config" command above, we want to convert the
                # configured addons to a list of "addon:level" pairs
                addons = [''.join([k,':',v])
                    for k,v in self.cfg['heroku']['addons'].iteritems()]

            for addon in addons:
                local('heroku addons:%s %s --app %s' % (action,
                                                        addon,
                                                        self.cfg['heroku']['app']))

    def domain(self, action=None, *domains):
        """
        Executes an add/clear/remove action to the remote heroku domains.

        Args:
            action: domain action. either add, clear, or remove
            domains: list of domains

        Usage:
            blt e:[env] heroku.domain [add|clear|remove] [domain]

        Examples:
            blt e:s heroku.domain - default, lists the current domains on staging
            blt e:s heroku.domain add - adds *ALL* domains defined in beltenv
                configuration file
            blt e:p heroku.domain add "matter.com" - adds the "matter.com"
                domain to the production heroku app
            blt e:p heroku.domain clear - clears all domains in production
        """
        if not action:
            local('heroku domains --app %s' % self.cfg['heroku']['app'])
        else:
            if not domains:
                domains = self.cfg['heroku']['domains']

            for domain in domains:
                local('heroku domains:%s %s --app %s' % (action,
                                                        domain,
                                                        self.cfg['heroku']['app']))

    def run(self, *commands):
        """
        Runs a given command on heroku.

        Args:
            commands: list of shell commands to be run on the heroku instance

        Usage:
            blt e:[env] heroku.run "command"

        Examples:
            blt e:s heroku.run bash - opens a bash session on heroku staging
            blt e:p heroku.run "ls -altr" - runs ls -altr on heroku prod
        """

        for command in commands:
           local('heroku run "%s" --app %s' % (command
                                            , self.cfg['heroku']['app']))

    def migrate(self):
        """
        Runs a database migration on heroku.

        The logic for migration is set via the beltenv configuration as
        different apps/databases could have different ways to run a migration.

        Usage:
            blt e:[env] heroku.migrate
        """
        self.run(*self.cfg['heroku']['migrate'])



