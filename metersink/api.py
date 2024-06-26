"""describes the api endpoint of the metering tool"""
import argparse
import logging
from pprint import pformat
from flask import Flask, request, json

from metersink.lib import get_config, get_sinks
from metersink.output_odoo import odoo_handle
from metersink.output_textfile import output_file

app = Flask(__name__)
NAME = "billing_api"

def _init_logger():
    logger = logging.getLogger(NAME)
    logger.setLevel(logging.INFO)

_init_logger()
LOG = logging.getLogger(NAME)


def push_to_sinks(conf, data):
    """puts received metering data to the configured billing sinks"""
    # LOG.debug('%s', conf)
    sinks = get_sinks(conf)
    LOG.debug("pushing to sinks: %s", sinks)
    for sink_type, sink_values in sinks.items():
        if sink_type == "file":
            for sink_name in sink_values["name"]:
                # maybe we want to differ between events and polls here
                # for now we put all incoming into the file
                output_file(sink_name, data)
        elif sink_type == "odoo":
            odoo_handle(sink_values, conf, data)


@app.route("/post_json", methods=["POST"])
def process_json():
    """Endpoint for json requests"""
    content_type = request.headers.get("Content-Type")
    if not content_type == "application/json":
        err_msg = f"Content-Type {content_type} not supported!"
        return err_msg, 204

    json_data = request.json
    LOG.debug("### the request ###############################################################")
    LOG.debug("json_body: %s", pformat(json_data))
    data = json.loads(request.data)
    for message in data:
        push_to_sinks(app.config['conf'], message)
    return json_data, 202


def main():
    """the main function"""
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

    config = get_config(args.config_file)
    app.config['conf'] = config

    if args.verbose or config.get("DEFAULT", "log_level") == "DEBUG":
        LOG.setLevel(logging.DEBUG)
        logging.getLogger("metersink.lib").setLevel(logging.DEBUG)


    logging.info("starting the billing api server")

    app.run(
        port=8088,
        debug=True,
    )
