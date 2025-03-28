import os
import sys

SECRET_KEY_GEN = lambda: os.urandom(24).hex()
AWS_SECRET_KEY = 'pp1cMDvugf0ElcPuIW9H7E7TCEQQCPG0wcKsVLio'
AWS_ACCESS_KEY = 'AKIAY5HWRBS2UWQQAK4A'
DB_REGION = 'ap-south-1'
TABLE_NAME = 'expense_table'