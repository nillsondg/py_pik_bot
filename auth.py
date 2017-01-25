import hashlib

from bot import Group
from config import full_group_hex, sms_only_hex


def check_code_and_return_group(code):
    if hashlib.md5(code.encode('utf-8')).hexdigest() == full_group_hex:
        return Group.users
    elif hashlib.md5(code.encode('utf-8')).hexdigest() == sms_only_hex:
        return Group.users
    else:
        return None
