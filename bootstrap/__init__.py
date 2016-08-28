import os
import sys
from subprocess import call
import pwd

from util import get_uid, get_gid, demote


def configure_passwordless_sudo(args):
    _ensure_root_user()

    _allow_passwordless_sudo(args.username)


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


def create_user(args):
    _ensure_root_user()

    if not os.path.exists(args.public_key_path) or not os.path.isfile(args.public_key_path):
        sys.exit("Public key not found")

    home_dir, ssh_dir = _create_user(args.username)

    _add_public_key(args.username, args.public_key_path, home_dir, ssh_dir)

    _allow_passwordless_sudo(args.username)

    _configure_ssh()

    _setup_firewall()

    ret_code = call(["service", "ssh", "restart"])
    if ret_code != 0:
        sys.exit("Failed to restart SSH service!")


def install_lets_encrypt(args):
    _ensure_root_user()

    install_dir = "/opt/letsencrypt"
    if os.path.exists(install_dir):
        sys.exit("Already installed")

    ret_code = call(["git", "clone", "https://github.com/letsencrypt/letsencrypt", install_dir])
    if ret_code != 0:
        sys.exit("Failed to clone Let's Encrypt repository")

    call([os.path.join(install_dir, "letsencrypt-auto")])


def get_ssl_certificate(args):
    _ensure_root_user()

    call(["service", "nginx", "stop"])

    ret_code = call(["/opt/letsencrypt/letsencrypt-auto", "certonly", "--standalone", "-d", args.domain_name])
    if ret_code != 0:
        sys.exit("Failed to get SSL certificate")

    call(["service", "nginx", "start"])


def renew_ssl_certificates(args):
    _ensure_root_user()

    ret_code = call(["/opt/letsencrypt/letsencrypt-auto", "renew", "--standalone", "--pre-hook",
                     "'service nginx stop'", "'service nginx stop'"])
    if ret_code != 0:
        sys.exit("Failed to renew SSL certificates")


def _add_public_key(username, public_key_path, home_dir, ssh_dir):
    authorized_keys_file = os.path.join(ssh_dir, "authorized_keys")
    with open(authorized_keys_file, "a") as fp, open(public_key_path) as pub_key_fp:
        fp.write(pub_key_fp.readline())
    os.chmod(authorized_keys_file, 400)
    ret_code = call(["chown", "%s.%s" % (username, username), home_dir, "-R"])
    if ret_code != 0:
        sys.exit("Failed to chown home directory for user")


def _create_user(username):
    if username not in [p.pw_name for p in pwd.getpwall()]:
        ret_code = call(["useradd", username])
        if ret_code != 0:
            sys.exit("Failed to create user")

    home_dir = os.path.join("/home", username)
    if not os.path.exists(home_dir):
        os.mkdir(home_dir)

    ssh_dir = os.path.join(home_dir, ".ssh")
    if not os.path.exists(ssh_dir):
        os.mkdir(ssh_dir)

    ret_code = call(["chmod", "700", ssh_dir])
    if ret_code != 0:
        sys.exit("Failed to chmod .ssh dir")

    ret_code = call(["usermod", "-s", "/bin/bash", username])
    if ret_code != 0:
        sys.exit("Failed to set shell for user")
    return home_dir, ssh_dir


def _setup_firewall():
    def _allow_port(port):
        ret_code = call(["ufw", "allow", str(port)])
        if ret_code != 0:
            sys.exit("Failed to allow port %s" % port)

    _allow_port(22)
    _allow_port(80)
    _allow_port(443)

    ret_code = call(["ufw", "disable"])
    if ret_code != 0:
        sys.exit("Failed to disable ufw")

    ret_code = call(["ufw", "--force", "enable"])
    if ret_code != 0:
        sys.exit("Failed to enable ufw")


def _configure_ssh():
    lines = []
    sshd_config_file = "/etc/ssh/sshd_config"
    with open(sshd_config_file) as fp:
        for cur_line in fp:
            if cur_line.startswith("PermitRootLogin "):
                lines.append("PermitRootLogin no\n")
            elif cur_line.startswith("PasswordAuthentication "):
                lines.append("PasswordAuthentication no\n")
            else:
                lines.append(cur_line)

    with open(sshd_config_file, "w") as fp:
        fp.writelines(lines)


def _allow_passwordless_sudo(username):
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


def _ensure_root_user():
    if os.geteuid() != 0:
        sys.exit("Need to run as root")

