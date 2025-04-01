import textwrap

import boto3
from datetime import date, timedelta
from calendar import month_name
import calendar

from matplotlib.figure import Figure

import configs.keys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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


def generate_graphs(df,dates_range):
    df = df.iloc[:-2]
    df['CommodityTypeMod'] = df['CommodityType'].apply(lambda x: x if x in configs.keys.GRAPH1_COMM_TYPES else 'Rents' if x in ('House-rent','Other-rents') else 'Others')
    grp_df1 = df.groupby(['CommodityTypeMod']).agg({'Price': ['sum']})
    grp1_labels = list(grp_df1.index)
    grp_df1.columns = ['Total']
    grp1_expenses = grp_df1['Total'].to_list()
    #total = sum(total_expense)
    #total_expense = [round(i / total * 100, 2) for i in total_expense]
    grp_df2 = df.query("CommodityType in @configs.keys.GRAPH2_COMM_TYPES").groupby(['CommodityType']).agg(
        {'Price': ['sum']})
    grp2_labels = list(grp_df2.index)
    grp_df2.columns = ['Total']
    grp2_expenses = grp_df2['Total'].to_list()
    #total_count = sum(count_per_type)
    #count_per_type = [round(i / total_count * 100, 2) for i in count_per_type]

    grp1_labels = [textwrap.fill(text, width=20) for text in grp1_labels]
    grp1 = create_graph(y = grp1_expenses,layers = grp1_labels, graph_type = 'pie')

    grp2_labels = [textwrap.fill(text, width=20) for text in grp2_labels]
    grp2 = create_graph(y=grp2_expenses, layers=grp2_labels, graph_type='pie')


    grp3_df_dates = df['Purchase_date'].drop_duplicates().to_list()
    grp3_df_dates_missing = get_missing_dates(grp3_df_dates, dates_range)
    grp3_df = df.groupby(['Purchase_date']).agg({'Price': ['sum','count']})
    grp3_df.columns = ['Total','Count']
    grp3_df = grp3_df.reset_index()
    grp3_df_full = pd.concat((grp3_df, pd.DataFrame([{'Purchase_date': i, 'Total': 0, 'Count': 0} for i in grp3_df_dates_missing])))
    grp3_df_full = grp3_df_full.sort_values(by='Purchase_date', ascending=False)
    grp3_dates = list(range(0,grp3_df_full.shape[0]))
    grp3_dates_labels = list(grp3_df_full['Purchase_date'])
    grp3_expenses = tuple(zip(*list(grp3_df_full[['Total','Count']].values)))
    print(grp3_expenses , grp3_dates_labels, sep= '\n')
    grp3 = create_graph(x = grp3_dates, y = grp3_expenses, layers = grp3_dates_labels, graph_type = 'bar')

    return grp1, grp2, grp3


def get_missing_dates(dates, date_ranges):
    if isinstance(date_ranges,str):
        month = months[date_ranges.lower()]
        year = date.today().year
        month_days = calendar.monthrange(year, month)[1]
        report_month_dates = ['{:02d}-{:02d}-{:02d}'.format(year, month, i) for i in range(1, month_days+ 1)]
    else:
        start_date = date(int(date_ranges['start_date'].split('-')[0]),
                          int(date_ranges['start_date'].split('-')[1]),
                          int(date_ranges['start_date'].split('-')[2]))
        end_date = date(int(date_ranges['end_date'].split('-')[0]),
                          int(date_ranges['end_date'].split('-')[1]),
                          int(date_ranges['end_date'].split('-')[2]))
        date_difference = int((end_date - start_date).days)
        report_month_dates = [date.strftime(start_date + timedelta(days = i), '%Y-%m-%d') for i in range(0, date_difference+1)]

    return list(set(report_month_dates) - set(dates))

def create_graph(x=None,y=None,layers=None, graph_type='pie'):
    if y is None:
        y = []
    if x is None:
        x = []

    if graph_type == 'pie':
        fig = Figure(figsize=(5, 5))
        ax = fig.subplots(1, 1, )
        ax.pie(y,
               explode=[0.1 if i == 0 else 0 for i in range(len(layers))],
               labels=layers,
               autopct='%1.1f%%',
               shadow=True,
               startangle=90)
        ax.axis('off')
    elif graph_type == 'bar':
        fig = Figure(figsize=(25, 5))
        ax = fig.subplots(1, 1, )
        y_normal = ((np.array(y).T - np.min(y, axis = 1).T) / (np.max(y,axis = 1) - np.min(y,axis = 1)).T).T.tolist()
        ax.bar(x, y_normal[0], width = -0.25, align = 'edge', color = 'blue',label='Total Expense')
        ax.bar(x, y_normal[1], width = 0.25, align = 'edge', color= 'red', label='Total Quantity')
        # Add value labels on top of each bar
        for i in range(len(x)):
            ax.text(x[i]-0.25/2, y_normal[0][i], f'{y[0][i]:.0f}', ha='right', va='bottom', fontsize=6)
            ax.text(x[i]+0.25/2, y_normal[1][i], f'{y[1][i]:.0f}', ha='left', va='bottom', fontsize=6)

        ax.set_xticks(x, layers, fontsize = 6, horizontalalignment = 'center')
        ax.tick_params(axis = 'y', labelleft = False, direction = 'out')
        ax.legend()
        ax.set_xlabel('Expense Dates', loc = 'center',fontsize = 6)
        ax.set_ylabel('Total expense/ Total products',loc = 'center', fontsize = 6,rotation = 90)

    buf1 = BytesIO()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(buf1, format="png")
    fig.savefig(f'graphs/graph{graph_type}.png', format="png")
    data = base64.b64encode(buf1.getbuffer()).decode("ascii")
    return data


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
