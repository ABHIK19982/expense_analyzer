
import boto3
from datetime import date
from calendar import month_name
import configs.keys
import pandas as pd
import numpy as np

from scripts.analytics_functions import *

months = {'january': 1,
          'february': 2,
          'march': 3,
          'april': 4,
          'may': 5,
          'june': 6,
          'july': 7,
          'august': 8,
          'september': 9,
          'october': 10,
          'november': 11,
          'december': 12}

def query_dynamodb(data):
    db = boto3.client('dynamodb',
                      region_name=configs.keys.DB_REGION,
                      aws_access_key_id=configs.keys.AWS_ACCESS_KEY,
                      aws_secret_access_key=configs.keys.AWS_SECRET_KEY
                      )
    if configs.keys.TABLE_NAME not in db.list_tables()['TableNames']:
        print('DB resource not available. Exiting process')
        return -1
    response = []
    if isinstance(data, str):
        month = months[data.lower()]
        current_year = date.today().year
        data = '{}{:02d}'.format(current_year, month)
        response = db.scan(ExpressionAttributeValues={
            ':ym': {
                'S': data
            }
        },
            FilterExpression='year_month = :ym',
            ProjectionExpression='Pid, CommodityName, Price, Purchase_date, CommodityType',
            TableName=configs.keys.TABLE_NAME
        )
    else:
        response = db.scan(ExpressionAttributeValues={
            ':sd': {
                'S': data['start_date']
            },
            ':ed': {
                'S': data['end_date']
            }
        },
            FilterExpression='Purchase_date BETWEEN :sd and :ed',
            ProjectionExpression='Pid, CommodityName, Price, Purchase_date, CommodityType',
            TableName=configs.keys.TABLE_NAME
        )
    if response['Count'] == 0:
        print('No records found for the given date range')
        return -1
    cols = list(response['Items'][0].keys())
    data = []
    for i in response['Items']:
        row = []
        for j in cols:
            if 'S' in i[j].keys():
                row.append(i[j]['S'])
            else:
                row.append(i[j]['N'])
        data.append(row)
    df = pd.DataFrame(data, columns=cols)
    df['Price'] = df['Price'].astype(np.float64)
    df['Purchase_date_datetime'] = pd.to_datetime(df['Purchase_date'])
    df = df.sort_values(by='Purchase_date_datetime', ascending=False)
    df = df.drop(['Purchase_date_datetime', 'Pid'], axis=1)
    new_df = pd.DataFrame([['', np.sum(df['Price'].to_list()), '', 'Total Amount'],
                           ['', df.shape[0], '', 'Total Quantity']],
                          columns=['CommodityName', 'Price', 'Purchase_date', 'CommodityType'])
    df = pd.concat([df, new_df], ignore_index=True)

    df = df[['Purchase_date', 'CommodityName', 'CommodityType', 'Price']]
    db.close()
    return df




def push_to_dynamodb(data):
    db = boto3.client('dynamodb',
                      region_name=configs.keys.DB_REGION,
                      aws_access_key_id=configs.keys.AWS_ACCESS_KEY,
                      aws_secret_access_key=configs.keys.AWS_SECRET_KEY
                      )
    if configs.keys.TABLE_NAME not in db.list_tables()['TableNames']:
        print('DB resource not available. Exiting process')
        return -1
    pids = db.scan(ExpressionAttributeNames={'#P': 'Pid'},
                   ExpressionAttributeValues={
                       ':ym': {
                           'S': data['expense_date'].replace('-', '')[0:6]
                       }
                   },
                   FilterExpression='year_month = :ym',
                   ProjectionExpression='#P',
                   TableName=configs.keys.TABLE_NAME
                   )
    if pids['Count'] == 0:
        current_pid = 1
    else:
        pid_list = [int(i['Pid']['S']) for i in pids['Items']]
        last_pid = max(pid_list)
        current_pid = last_pid + 1

    response = db.put_item(TableName=configs.keys.TABLE_NAME,
                           Item={'Pid': {'S': str(current_pid).rjust(4)},
                                 'year_month': {'S': data['expense_date'].replace('-', '')[0:6]},
                                 'CommodityName': {'S': data['commodity']},
                                 'Price': {'N': data['price']},
                                 'Purchase_date': {'S': data['expense_date']},
                                 'CommodityType': {'S': data['type']}},
                           ReturnConsumedCapacity='TOTAL',
                           ReturnItemCollectionMetrics='SIZE'
                           )
    print(response)
    db.close()


def get_last_three_months():
    current_month_idx = date.today().month - 1
    months = []

    for i in range(3):
        month_idx = (current_month_idx - i) % 12
        month = month_name[month_idx + 1]
        months.append(month)

    return months


if __name__ == '__main__':
    df = query_dynamodb({'start_date': '2025-03-01','end_date': '2025-03-31'})
    print(df.head())
    graphs = generate_graphs(df,{'start_date': '2025-03-01','end_date': '2025-03-31'})
