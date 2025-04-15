import os
import sys

MYSQL_HOST = "expenseanalyzer.mysql.pythonanywhere-services.com"
MYSQL_USER = 'expenseanalyzer'
MYSQL_PASSWORD = ''
MYSQL_DB = 'expenseanalyzer$metastore'
PASS_EXPIRY = 30
MAX_PASS_HISTORY = 3

SECRET_KEY_GEN = lambda: os.urandom(24).hex()
AWS_SECRET_KEY = ''
AWS_ACCESS_KEY = ''
DB_REGION = 'ap-south-1'
TABLE_NAME = 'expense_table'

GRAPH1_COMM_TYPES = ['Bills','Rents','Transportation','Others']
GRAPH2_COMM_TYPES = ['Grocery','Green-Grocery','Food','Entertainment','Clothes','Miscellaneous']
