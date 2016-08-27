import pwd
import os


def get_uid(username):
    pw_record = pwd.getpwnam(username)
    return pw_record.pw_uid


def get_gid(username):
    pw_record = pwd.getpwnam(username)
    return pw_record.pw_gid


def demote(user_uid, user_gid):
    def set_ids():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return set_ids
