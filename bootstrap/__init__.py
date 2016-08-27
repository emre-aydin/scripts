import os
import sys
from subprocess import call

from util import get_uid, get_gid, demote


def configure_passwordless_sudo(args):
    _ensure_root_user()

    username = args.username

    cmd = "%s ALL=(ALL) NOPASSWD:ALL" % username
    file_path = os.path.join("/etc/sudoers.d", username)

    if os.path.exists(file_path):
        with open(file_path, mode='r') as fp:
            for line in fp:
                if line.startswith(username):
                    print("Already contains entry for user %s" % username)
                    return

    with open(file_path, mode='a') as fp:
        fp.write(cmd)
        print("Allowed passwordless sudo access for %s" % username)


def configure_locales(args):
    _ensure_root_user()

    with open("/etc/default/locale", mode="w") as fp:
        fp.write("""LANG="en_US.UTF-8"
LANGUAGE="en_US.UTF-8"
LC_CTYPE="en_US.UTF-8"
LC_NUMERIC="en_US.UTF-8"
LC_TIME="en_US.UTF-8"
LC_COLLATE="en_US.UTF-8"
LC_MONETARY="en_US.UTF-8"
LC_MESSAGES="en_US.UTF-8"
LC_PAPER="en_US.UTF-8"
LC_NAME="en_US.UTF-8"
LC_ADDRESS="en_US.UTF-8"
LC_TELEPHONE="en_US.UTF-8"
LC_MEASUREMENT="en_US.UTF-8"
LC_IDENTIFICATION="en_US.UTF-8"
LC_ALL="en_US.UTF-8"
""")

    print("Log out and log back in for the changes to take effect")


def create_psql_db(args):
    _ensure_root_user()

    postgres_uid = get_uid("postgres")
    postgres_gid = get_gid("postgres")

    ret_code = call(["psql", "-c", "CREATE ROLE %s LOGIN PASSWORD '%s'" % (args.db_user, args.db_pass)],
                    preexec_fn=demote(postgres_uid, postgres_gid))
    if ret_code != 0:
        sys.exit("Failed to create database role")

    ret_code = call(["psql", "-c", "CREATE DATABASE %s OWNER %s" % (args.db_name, args.db_user)],
                    preexec_fn=demote(postgres_uid, postgres_gid))
    if ret_code != 0:
        sys.exit("Failed to create database")


def delete_psql_db_and_user(args):
    _ensure_root_user()

    postgres_uid = get_uid("postgres")
    postgres_gid = get_gid("postgres")

    ret_code = call(["psql", "-c", "DROP DATABASE IF EXISTS %s" % args.db_name],
                    preexec_fn=demote(postgres_uid, postgres_gid))
    if ret_code != 0:
        sys.exit("Failed to delete database")

    ret_code = call(["psql", "-c", "DROP ROLE IF EXISTS %s" % args.db_user],
                    preexec_fn=demote(postgres_uid, postgres_gid))
    if ret_code != 0:
        sys.exit("Failed to delete role")


def _ensure_root_user():
    if os.geteuid() != 0:
        sys.exit("Need to run as root")

