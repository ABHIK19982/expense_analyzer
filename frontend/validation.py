import sys
import re
import os
from flask import request
import time

def validate_form(req:request) -> bool:
    rules = {'username': r'^[a-zA-Z0-9_]{8,}$',
             'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'}
    if 'username' in req.form and req.form['username'] == 'admin':
        if 'password' in req.form and req.form['password'] == '1234':
            return True
    for key in rules:
        if key not in req.form:
            return False
        if not re.match(rules[key], req.form[key]):
            return False
        if not req.form[key]:
            return False
        if req.form[key] == ' ':
            return False
    return True