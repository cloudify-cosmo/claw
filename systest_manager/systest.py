import argh

from commands import commands


def main():
    argh.dispatch_commands(commands)

if __name__ == '__main__':
    main()
