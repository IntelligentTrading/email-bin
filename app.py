from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
import os, datetime, re
from urllib.parse import urlparse
import logging
logging.basicConfig()
from pymongo import MongoClient
from flask import Flask, request, Response

from access_control import crossdomain

EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}')
# domains allowed to invoke the XMLHttpRequest API
ALLOWED_DOMAINS = [
    'token-sale.intelligenttrading.org',
    'token-sale-test.intelligenttrading.org',
    'itt-token-sale-page.s3-website-us-east-1.amazonaws.com',
]

app = Flask(__name__)

@app.route('/signup', methods=['POST'])
@crossdomain(origin=ALLOWED_DOMAINS)
def signup():
    eth_amount = request.form['ethereum-amount']
    eth_address = request.form['ethereum-address']
    email = request.form['ethereum-email']
    if email and re.match(EMAIL_REGEX, email):
        signup = {
            'email': email,
            'eth_amount': eth_amount,
            'eth_address': eth_address,
            'ip': request.access_route[0],
            'time': datetime.datetime.utcnow(),
        }
        app.database.signups.insert_one(signup)
        return Response("Thanks for signing up!", status=201)
    else:
        return Response("Sorry, your email address is invalid.", status=400)

@app.route('/healthcheck', methods=['GET'])
@crossdomain(origin=ALLOWED_DOMAINS)
def healthcheck():
    count = app.database.signups.find().count()
    return Response("MongoDB ok.", status=200)


def connect_to_db():
    """Connect to database"""
    MONGOLAB_URI = os.environ.get('MONGOLAB_URI')
    # MONGODB_HOST = urlparse(MONGOLAB_URI).geturl()
    # MONGODB_PORT = urlparse(MONGOLAB_URI).port
    DATABASE_NAME = urlparse(MONGOLAB_URI).path[1:]

    client = MongoClient(MONGOLAB_URI)
    app.database = client[DATABASE_NAME]

if __name__ == '__main__':
    connect_to_db()
    port = int(os.environ.get('PORT', 5000))
    http_server = WSGIServer(('', port), app)
    http_server.serve_forever()
