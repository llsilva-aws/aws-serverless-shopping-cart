import json
import os
import decimal
import boto3

from aws_lambda_powertools import Logger, Tracer
from boto3.dynamodb.conditions import Key
from collections.abc import Mapping, Iterable
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, Mapping):
            return '{' + ', '.join(f'{self.encode(k)}: {self.encode(v)}' for (k, v) in obj.items()) + '}'
        if isinstance(obj, Iterable) and (not isinstance(obj, str)):
            return '[' + ', '.join(map(self.encode, obj)) + ']'
        if isinstance(obj, Decimal):
            return f'{obj.normalize():f}'  # using normalize() gets rid of trailing 0s, using ':f' prevents scientific notation
        return super().encode(obj)

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("products")

"""with open('product_list.json', 'r') as product_list:
    product_list = json.load(product_list)
"""
logger.info("Fetching Products from DB")
response = table.scan()
items = response['Items']

logger.info("Products in the table: " + str(len(response['Items'])))

while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response['Items'])
    
product_list = json.dumps(items, cls=DecimalEncoder)

HEADERS = {
    "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN"),
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Return list of all products.
    """
    logger.debug("Fetching product list")

    return {
        "statusCode": 200,
        "headers": HEADERS,
        "body": json.dumps({"products": product_list}),
    }
