from collections import namedtuple
import datetime
from inspect import getmembers, ismodule, isclass
import os
import sys
import types

from blt.helpers import prompt, abort
from clint.textui import puts, indent
from clint.textui.colored import red, cyan, green

def iscommander(obj):
    """
    Determine if the provided value is a ``Command`` object.
    """
    # if we get the actual Commander class (e.g. not a subclass) we want
    # to ignore it and not include it in the command list
    if obj is Commander:
        return False

    try:
        return issubclass(obj, Commander)
    except TypeError:
        return False

def iscommandmethod(obj):
    if isinstance(obj, types.MethodType):

        # we skip any methods that begin with "_"
        if obj.__name__[0] == '_':
            return False

        return True
    return False

def prod_check(cmd):
    puts('****************************************')
    puts(red('         P R O D U C T I O N            '))
    puts('          woah there cowboy!            ')
    puts(red('               check                    '))
    puts('****************************************')
    puts('Command Called => %s\n' % cyan(cmd))
    proceed = prompt("Are you sure you want to do proceed?", default="no")

    if proceed.lower() != 'yes' and proceed.lower() != 'y':
        abort('change aborted!')

def import_file(filepath):
    if not os.path.isfile(filepath):
        if filepath == 'bltenv.py':
            raise IOError("bltenv.py not found in cwd, please create one.")
        else:
            raise IOError("bltenv.py not found on given path: %s" % filepath)

    directory, bltfile = os.path.split(filepath)

    # ensure that bltenv.py's directory is on PYTHONPATH, so we won't
    # have any troubles importing it
    sys.path.insert(0, directory)

    # perform the bltenv import (note that we must strip off the ".py")
    imported = __import__(os.path.splitext(bltfile)[0])

    # restore PYTHONPATH to its original state by removing the bltenv
    # directory insertion.
    del sys.path[0]

    return imported

# Module recursion cache
class _ModuleCache(object):
    """
    Set-like object operating on modules and storing __name__s internally.
    """
    def __init__(self):
        self.cache = set()

    def __contains__(self, value):
        return value.__name__ in self.cache

    def add(self, value):
        return self.cache.add(value.__name__)

    def clear(self):
        return self.cache.clear()


class Command(object):
    """
    Class that encapsulates a blt command.

    This is really just a method within a Commander class, blt does module and
    class introspection to figure out all of the defined methods on a Commander
    and creates a wrapped ``Command`` to easily be called during runtime.
    """
    def __init__(self, klass, name):
        """
        Initializes a Command object

        Args:
            klass: the Commander class the method belongs to
            name: a string representing the name of the method ("command" in
                blt parlence)
        """
        self.klass = klass
        self.name = name

    def execute(self, config, args=[]):
        # instantiate the class for the requested command
        class_instance = self.klass(config)

        # call the method requested
        getattr(class_instance, self.name)(*args)

    @property
    def summary_docstring(self):
        retstr = self.docstring or ''

        if retstr:
            retstr = [line for line in retstr.split('\n') if line != ''][0].strip()

        return retstr

    @property
    def docstring(self):
        return getattr(self.klass, self.name).__doc__ or ''


class Commander(object):
    def __init__(self, configuration):
        self.cfg = configuration


class CommandCenter(object):
    def __init__(self, env_file):
        self.module_cache = _ModuleCache()
        self.env_file = env_file
        self.loaded_env = import_file(self.env_file)
        self.commands = self._extract_commands(self.loaded_env)
        self.config = self._extract_config(self.loaded_env)

    def run(self, env_type, command, args=[]):
        self._precheck(env_type, command)
        cfg = self.config[env_type]

        # add in the environment we are using
        cfg['blt_envtype'] = env_type

        cmd = self.commands[command]

        # call the execute method on the Command class
        cmd.execute(cfg, args)

    def help(self, cmds=[]):
        """
        Provides detailed help for a specific command.

        This method pulls the docstrings for the passed in list of commmands
        and displays it to the user.

        Args:
            cmds: a list of strings representing the commands to get help on

        Usage:
            blt help tool.command

        Examples:
            blt help aws.sync_s3 - prints out docstring for aws.sync_s3 command
            blt help aws.pull_s3 heroku.push - prints out docstring for both
                aws.pull_s3 and heroku.push
        """
        for command in cmds:
            cmd = self.commands[command]
            puts(green('[' + command +']'))
            puts(cmd.docstring)

    def list(self, tool=None):
        """
        Prints out a list of commands and their descriptions.

        If passed a tool name, the list method will apply a filter to only show
        those commands. If no tool is passed it will display all commands
        available from the bltenv file. It will also group them by tool.

        Args:
            tool: string of a particular tool to filter on (optional)
        """

        prev_tool = None
        toolgroups = group_commands(tool, self.commands)

        for tool, short_cmd, command_name in group_commands(tool, self.commands):
            if prev_tool != tool:
                prev_tool = tool
                puts(green('\n[' + tool +']'))

            # get the summarized docstring
            summary = self.commands[command_name].summary_docstring

            with indent(2):
                puts("- {0:30} {1}".format(short_cmd,summary))

        puts('\n')

    def _precheck(self, env_type, command):
        if env_type == 'production':
            prod_check(command)

        if env_type not in self.config:
            abort('environment [%s] not defined in your beltenv file.'
                    % env_type)

        if not command:
            abort('you did not specify a command, try again.')

        if command not in self.commands:
            abort('command [%s] not found in your beltenv file.'
                    % command)


    def _extract_config(self, imported_python):
        # make sure that:
        # a) CONFIG is defined on imported file, and
        # b) the environment is a key
        #
        # an exception will be thrown if not
        cfg = imported_python.CONFIG
        cfg.update({
            "blt": {
                  "env_file": self.env_file
                , "updated": datetime.datetime.now()
            }
        })

        return cfg

    def _extract_commands(self, imported_python, base_name=''):
        loaded_commands = {}
        modules = getmembers(imported_python, ismodule)
        cmd_classes = getmembers(imported_python, iscommander)

        for module_name, module in modules:
            if module not in self.module_cache:
                self.module_cache.add(module)
                new_base = base_name + module_name + '.'
                commands = self._extract_commands(module, new_base)

                loaded_commands.update(commands)
                # for command_name, command_tup in commands.items():
                #     if module_name not in loaded_commands:
                #         loaded_commands[module_name] = {}

                #     loaded_commands[module_name][command_name] = command_tup

        for klass_name, klass in cmd_classes:
            # get all of the methods in the class
            commands = getmembers(klass, iscommandmethod)

            # need to create a generator here...
            for name, method in commands:
                command_name = ''.join([base_name, name])
                loaded_commands[command_name] = Command(klass, name)

        return loaded_commands

def group_commands(toolname, commands):
    for command in sorted(commands):
        cmdsplit = command.split('.')
        tool = cmdsplit[0]
        short_cmd = ''.join(cmdsplit[1:])

        if not toolname or toolname[0] == tool:
            # handle the case where we have commands defined on the bltenv file
            # and, as such, will not have a tool grouping
            if len(cmdsplit) == 1:
                short_cmd = tool
                tool = 'local - no tool prefix'

            yield (tool, short_cmd, command)


