import os
import sys
from StringIO import StringIO

import argh

from systest import configuration
from systest import commands


def main():
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        try:
            commands.script(configuration=configuration.CURRENT_CONFIGURATION,
                            script_path=sys.argv[1],
                            script_args=sys.argv[2:])
        except argh.CommandError as e:
            sys.exit('error: {0}'.format(e))
    else:
        parser = argh.ArghParser()
        parser.add_commands(commands.app.commands)
        errors = StringIO()
        parser.dispatch(errors_file=errors)
        errors_value = errors.getvalue()
        if errors_value:
            errors_value = errors_value.replace('CommandError',
                                                'error').strip()
            sys.exit(errors_value)

if __name__ == '__main__':
    main()
