import simplejson
import os
import boto3

from aws_lambda_powertools import Logger, Tracer
from boto3.dynamodb.conditions import Key

from decimal import Decimal

def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("products")

"""with open('product_list.json', 'r') as product_list:
    product_list = json.load(product_list)
"""
logger.info("Fetching Products from DB")
response = table.scan()
    
product_list = simplejson.dumps(response['Items'])

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
