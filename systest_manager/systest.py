import sys
from StringIO import StringIO

import argh

from commands import app


def main():
    parser = argh.ArghParser()
    parser.add_commands(app.commands)
    errors = StringIO()
    parser.dispatch(errors_file=errors)
    errors_value = errors.getvalue()
    if errors_value:
        errors_value = errors_value.replace('CommandError', 'error').strip()
        sys.exit(errors_value)

if __name__ == '__main__':
    main()
