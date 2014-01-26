import os
from subprocess import call, check_output, CalledProcessError
import sys

from clint.textui import puts, indent, colored

def abort(msg):
    puts("\nFatal error: %s" % str(msg))
    puts(colored.red("Aborting.\n"))
    sys.exit(1)

def local(command, collect_output=False, abort_on_stderr=True):
    try:
        if collect_output:
            return check_output(command, shell=True)
        else:
            retcode = call(command, shell=True)

            if retcode !=0:
                raise CalledProcessError(retcode, command)
    except CalledProcessError as e:
        msg = [ "local() encountered an error while executing '{0}'".format(command),
                "    Error: {0}".format(e.output or e),
                "    Exit Code: {0}".format(e.returncode) ]

        if not abort_on_stderr:
            return e.output

        abort('\n'.join(msg))

def prompt(text, default=''):

    # Set up default display
    default_str = ""
    if default != '':
        default_str = " [%s] " % str(default).strip()
    else:
        default_str = " "

    # Construct full prompt string
    prompt_str = text.strip() + default_str

    # Loop until we pass validation
    value = None
    while value is None:
        value = raw_input(prompt_str) or default

    return value

class cd(object):
    def __init__(self, new_path):
        self.new_path = new_path

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

