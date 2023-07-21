import os
import sys
import argparse
import logging

from flask import Flask, request, jsonify, json
# from flask_restful import Api

# from rabbitmq_lib import get_messages
# from ceilometer_lib import ensure_config

from pprint import pprint, pformat

from metersink.lib import *

app = Flask(__name__)
NAME = 'billing_api'


def _init_logger():
    logger = logging.getLogger(NAME)
    logger.setLevel(logging.INFO)

_init_logger()
LOG = logging.getLogger(NAME)

CONFIG = None


@app.get('/customer/<string:customer_id>')
def get_customer(customer_id):
    projects = get_projects(customer_id)
    json = jsonify({'customer': customer_id,
                    'projects': projects})
    return json

@app.get('/project/<string:project_id>')
def get_project(project_id):
    json = jsonify({'project': project_id})
    return json


def get_projects(source="keystone", customer=None):
    """here we would have to ask odoo or something like that. out of scope"""
    return jsonify({})


def _get_servers(project):
    return {}


def _get_volumes(project):
    return {}


def _get_attached_volumes(server):
    return {}


def _get_floating_ips(project):
    return {}


def _get_images(project):
    return {}


def push_json(data):
    json = jsonify(data)
    return True


@app.route('/post_json', methods=['POST'])
def process_json():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.json
        LOG.debug('%s', pformat(json_data))
        data = json.loads(request.data)
        for message in data:

            LOG.debug('message: %s', pformat(message))

            push_to_sinks(CONFIG, message)



        return json_data, 202
    else:
        return 'Content-Type not supported!', 204


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c',
                        # type=argparse.FileType('r'),
                        dest='config_file',
                        default='settings.conf',
                        help='The config file to use'
                        )
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    args = parser.parse_args()
    if args.verbose:
        LOG.setLevel(logging.DEBUG)

    CONFIG = get_config(args)
    logging.info('starting the billing api server')
    app.run(
        port=8088,
        debug=True,
    )
