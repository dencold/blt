import pytest
import os
from mock import patch, call, Mock, MagicMock

import blt.environment as env

class Commands(env.Commander):
    def visible_command(self):
        pass

    def _hidden_command(self):
        pass

# -- Set Fixtures -------------------------------------------------------------
@pytest.fixture
def cmd_center():
    filepath = os.path.abspath(os.path.dirname(__file__) + '/beltenvtest.py')
    return env.CommandCenter(filepath)

@pytest.fixture
def commander_class():
    return env.Commander

@pytest.fixture
def commander_subclass():
    return Commands

@pytest.fixture
def commander_instance():
    return Commands(None)

# -- Test Cases! --------------------------------------------------------------

def test_get_tool_config(cmd_center):
    assert cmd_center.config['staging']['heroku']['app'] == 'pubweb-staging'

def test_loaded_commands(cmd_center):
    # we should have the following commands:
    # - standard_command
    # - default_command
    # - command_with_aliases
    # - some_really_long_aliased_command
    # - siamese (alias to command_with_aliases)
    # - twin (alias to command_with_aliases)
    # - srl (alias to some_really_long_aliased_command)
    # - importedtest
    # == 7 total
    assert len(cmd_center.commands) == 7

    assert sorted(cmd_center.commands.keys()) == [ 'command_with_aliases'
                                                 , 'default_command'
                                                 , 'importedtest.imported_alias'
                                                 , 'importedtest.imported_command'
                                                 , 'importedtest.imported_default'
                                                 , 'some_really_long_aliased_command'
                                                 , 'standard_command'
                                                 ]

def test_iscommander(commander_subclass):
    assert env.iscommander(commander_subclass)

def test_iscommander_skips_commander_base(commander_class):
    assert env.iscommander(commander_class) == False

def test_iscommandmethod(commander_instance):
    assert env.iscommandmethod(commander_instance.visible_command)

def test_prod_check_run(cmd_center):
    env.prod_check = Mock()
    cmd_center.run('production', 'default_command')

    env.prod_check.assert_called_once_with('default_command')
