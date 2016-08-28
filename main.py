import argparse

from bootstrap import configure_passwordless_sudo, configure_locales, create_psql_db, delete_psql_db_and_user, \
    create_user, install_lets_encrypt, get_ssl_certificate, renew_ssl_certificates

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command to run")
    subparsers.required = True

    config_sudo_parser = subparsers.add_parser("config-sudo", help="Allow user to use sudo without password")
    config_sudo_parser.add_argument("username", help="Username to allow passwordless sudo")
    config_sudo_parser.set_defaults(func=configure_passwordless_sudo)

    locale_parser = subparsers.add_parser("config-locales", help="Configures all system locales to 'en_US.UTF-8'")
    locale_parser.set_defaults(func=configure_locales)

    psql_parser = subparsers.add_parser("create-database", help="Create PostgreSQL role and database")
    psql_parser.add_argument("db_name", help="Name of the database")
    psql_parser.add_argument("db_user", help="Username for the database user")
    psql_parser.add_argument("db_pass", help="Password for the database user")
    psql_parser.set_defaults(func=create_psql_db)

    psql_delete_parser = subparsers.add_parser("delete-database", help="Delete PostgreSQL role and database")
    psql_delete_parser.add_argument("db_name", help="Name of the database")
    psql_delete_parser.add_argument("db_user", help="Name of the database user")
    psql_delete_parser.set_defaults(func=delete_psql_db_and_user)

    create_user_parser = subparsers.add_parser("create-user", help="Creates the initial user, configures SSH and "
                                                                   "sets up firewall")
    create_user_parser.add_argument("username", help="Username for the initial user")
    create_user_parser.add_argument("public_key_path", help="Path of the public key to add as authorized key")
    create_user_parser.set_defaults(func=create_user)

    install_le_parser = subparsers.add_parser("install-letsencrypt", help="Clones and installs Let's Encrypt")
    install_le_parser.set_defaults(func=install_lets_encrypt)

    get_ssl_parser = subparsers.add_parser("get-ssl-certificate", help="Gets SSL certificate for domain")
    get_ssl_parser.add_argument("domain_name", help="Domain name")
    get_ssl_parser.set_defaults(func=get_ssl_certificate)

    renew_ssl_parser = subparsers.add_parser("renew-ssl-certificates", help="Renews all SSL certificates")
    renew_ssl_parser.set_defaults(func=renew_ssl_certificates)

    args = parser.parse_args()
    args.func(args)
