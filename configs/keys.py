import os
import sys

SECRET_KEY_GEN = lambda: os.urandom(24).hex()
AWS_SECRET_KEY = ''
AWS_ACCESS_KEY = ''
DB_REGION = 'ap-south-1'
TABLE_NAME = 'expense_table'

GRAPH1_COMM_TYPES = ['Bills','Rents','Transportation','Others']
GRAPH2_COMM_TYPES = ['Grocery','Green-Grocery','Food','Entertainment','Clothes','Miscellaneous']