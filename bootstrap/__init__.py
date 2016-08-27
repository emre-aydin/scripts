import os
import sys


def configure_passwordless_sudo(args):
    username = args.username
    if os.geteuid() != 0:
        sys.exit("Need to run as root")

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
