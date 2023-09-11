import argparse
import logging
from pprint import pformat
from flask import Flask, request, json

from metersink.lib import *
from metersink.output_odoo import odoo_handle

app = Flask(__name__)


NAME = "billing_api"


def _init_logger():
    logger = logging.getLogger(NAME)
    logger.setLevel(logging.INFO)


_init_logger()
LOG = logging.getLogger(NAME)

CONFIG = None

def push_to_sinks(conf, data):
    # LOG.debug('%s', conf)
    sinks = get_sinks(conf)
    LOG.debug("pushing to sinks: %s", sinks)
    for sink_type, sink_values in sinks.items():
        if sink_type == "file":
            for index, sink_name in enumerate(sinks["file"]["name"]):
                # ToDo maybe we want to differ between events and polls here
                # for now we put all incoming into the file
                output_file(sink_name, data)
        elif sink_type == "odoo":
            odoo_handle(sinks['odoo'], conf, data)


@app.route("/post_json", methods=["POST"])
def process_json():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        json_data = request.json
        LOG.debug("### the request ###############################################################")
        LOG.debug("json_body: %s", pformat(json_data))
        data = json.loads(request.data)
        for message in data:
            push_to_sinks(CONFIG, message)
        return json_data, 202
    else:
        return "Content-Type not supported!", 204


def main():
    global CONFIG
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        "-c",
        dest="config_file",
        default="settings.conf",
        help="The config file to use",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="increase output verbosity",
    )
    args = parser.parse_args()
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
        logging.getLogger("metersink.lib").setLevel(logging.DEBUG)

    CONFIG = get_config(args.config_file)
    logging.info("starting the billing api server")
    app.run(
        port=8088,
        debug=True,
    )
