import sys
import logging

from blt.environment import CommandCenter
from clint.arguments import Args
from clint.textui import puts, indent
from clint.textui.colored import red, blue, cyan, white, green, yellow, magenta


DEFAULT_BLT_FILE = 'bltenv.py'
env_shortcut_map = {
      'p': 'production'
    , 's': 'staging'
    , 'l': 'local'
}

args = Args()

def usage():
    puts(white('\nGeneral blt usage:\n'))
    with indent(4):
        # we can't do a ''.join([]) here because of ColoredString not playing
        # friendly with strings.
        puts(white('blt e:' +
            magenta('[environment]') +
            green(' [tool]') +
            '.' +
            blue('[command]') +
            red(' [args]')))

    puts(white('\nExample:\n'))
    with indent(4):
        puts(white('blt e:production django.runserver 170.0.0.1 8888\n'))

    puts(white("Let's break that down:\n"))
    with indent(4):
        puts(white('blt e:' +
            magenta('production') +
            green(' django') +
            '.' +
            blue('runserver') +
            red(' 127.0.0.1 8888')))

        puts('{0:15} => {1}'.format('- environment', 'production'))
        puts('{0:15} => {1}'.format('- tool', 'django'))
        puts('{0:15} => {1}'.format('- command', 'runserver'))
        puts('{0:15} => {1}'.format('- args', '127.0.0.1, 8888'))

    puts(white('\nSpecial blt commands:\n'))
    with indent(4):
        puts('blt help - this screen')
        puts('blt help [command] - detailed command help')
        puts('blt list - list all available commands')

    puts(white('\nHelpful hints:\n'))
    with indent(4):
        puts('- Environment is optional, will default to local if none given.')
        puts('- Environment shortcuts: (p)roduction, (s)taging, (l)ocal.')
        puts('- Tab completion works on tools/commands, give it a shot.')
        puts('- Now, go make yerself a sandwich!\n')

def determine_envtype():
    # find out if the environment was passed in, note that a call to
    # clint.args.get_with('e:') *should* work here, but sadly there is a bug
    # in clint and it doesn't handle when the argument is not passed correctly
    env_index = args.first_with('e:')

    # special note that we explicitly check against None here because the index
    # could be returned as zero, which would return false in a bool check.
    if env_index is None:
        puts("Environment not defined, defaulting to " + green('local'))
        return 'local'

    # remove it from the args list
    envtype = args.pop(env_index)

    # strip the 'e:' and check for shortcut values, we allow the following:
    # - (p)roduction
    # - (s)taging
    # - (l)ocal
    envtype = envtype.split('e:', 1)[1]

    if envtype in env_shortcut_map:
        envtype = env_shortcut_map[envtype]

    return envtype

def main():
    # take care of the new user trying to figure wtf is going on here
    if not args or args.get(0) == 'help' and len(args) == 1:
        usage()
        exit(0)

    try:
        center = CommandCenter(DEFAULT_BLT_FILE)
    except IOError as e:
        print red('[ERROR]') + ' %s' % e
        exit(1)

    # user is requesting help on a specific command
    if args.get(0) == 'help':
        # call the commandcenter help method, we skip past index 0 which
        # is just the "help" arg.
        center.help(args[1:])
        exit(0)

    # check if the user is requesting a list:
    if args.get(0) == 'list':
        center.list(args[1:])
    elif args.get(0) == 'completion':
        print '\n'.join(sorted(center.commands.keys()))
    else:
        envtype = determine_envtype()
        cmd = args.pop(0)
        try:
            center.run(envtype, cmd, args.all)
        except KeyboardInterrupt:
            print '\nCancelled.'

if __name__ == '__main__':
    main()


