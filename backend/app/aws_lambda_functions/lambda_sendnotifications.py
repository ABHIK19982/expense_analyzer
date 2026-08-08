import json
import boto3
import datetime

def lambda_handler(event, context):
    ddb = boto3.client('dynamodb')
    sns = boto3.client('sns')

    topics = sns.list_topics()
    topics = [i['TopicArn'] for i in topics['Topics']]
    if 'arn:aws:sns:ap-south-1:612549856437:sns_topic_cust_notify' not in topics :
        return json.dumps({
            'status': 400,
            'description': 'SNS topic not available',
            'response': topics
        })
    data = []
    records = event['Records']
    for rec in records:
        if rec['eventName'] != 'INSERT':
            return {'status': 200, 'description': f'No action required for {rec['eventName']} method'}
        if rec['eventSourceARN'].split('/')[1] != 'expense_table':
            return {'status': 400, 'description': f'No Trigger for expense_table'}
        
        p_key = rec['dynamodb']['Keys']
        vals = ddb.scan(ExpressionAttributeValues={
                ':ym': {
                    'S': p_key['year_month']['S']
                },
                ':id': {
                    'S': p_key['Pid']['S']
                }
            },
            FilterExpression='year_month = :ym and Pid = :id',
            ProjectionExpression='Purchase_date,CommodityName, Price, byr_name',
            TableName='expense_table')
        for i in vals['Items']:
            row = {}
            for j in i.keys():
                if 'S' in i[j].keys():
                    row[j] = i[j]['S']
                else:
                    row[j] = i[j]['N']
            data.append(row)
    message = {
        'default': 'Something went wrong',
        'EMAIL': f'Expense added in account {data[0]['byr_name']}\n'+ '\n'.join(
            [f'Purchase Date: {i['Purchase_date']} -- Commodity Name: {i['CommodityName']} -- Price: {i['Price']}' for i in data]) + '\n<<<< Notification from Expense analyzer. please do not reply >>>>',
        'SMS':f'Expense added in account {data[0]['byr_name']}.\n<<<< Notification from Expense analyzer. please do not reply >>>>'
    }
    resp = sns.publish(TopicArn = 'arn:aws:sns:ap-south-1:612549856437:sns_topic_cust_notify',
                    Message = json.dumps(message), 
                    Subject = 'Expense Analyzer - Expense added - {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%i:%s')),
                    MessageStructure = 'json')

    return {
        'status': 200,
        'description':json.dumps({'Response':resp })
    }
