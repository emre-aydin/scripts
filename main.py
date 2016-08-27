import argparse

from bootstrap import configure_passwordless_sudo, configure_locales

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command to run")
    subparsers.required = True

    config_sudo_parser = subparsers.add_parser("config-sudo", help="Allow user to use sudo without password")
    config_sudo_parser.add_argument("username", help="Username to allow passwordless sudo")
    config_sudo_parser.set_defaults(func=configure_passwordless_sudo)

    locale_parser = subparsers.add_parser("config-locales", help="Configures all system locales to 'en_US.UTF-8'")
    locale_parser.set_defaults(func=configure_locales)

    args = parser.parse_args()
    args.func(args)
