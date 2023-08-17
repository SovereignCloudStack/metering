import argparse
import logging
from pprint import pformat

from fastapi import FastAPI
# from typing import Optional
# from pydantic import BaseModel, BaseSettings
from flask import Flask, request, json

# from .config import settings
from metersink.lib import *

app = Flask(__name__)


NAME = "billing_api"


def _init_logger():
    logger = logging.getLogger(NAME)
    logger.setLevel(logging.INFO)


_init_logger()
LOG = logging.getLogger(NAME)

CONFIG = None

# class Settings(BaseSettings):
#     app_name: str = "Awesome API"
#     admin_email: str
#     items_per_user: int = 50
#
# class Message(BaseModel):
#     name: str
#     content_type: str | None = None

#settings = Settings()
#app = FastAPI()

#@app.post("/post_json")
# def process_json(item: Message):
#     LOG.debug("message:", item)
#     content_type = request.headers.get("Content-Type")
#     if content_type == "application/json":
#         json_data = request.json
#         LOG.debug("%s", pformat(json_data))
#         data = json.loads(request.data)
#         for message in data:
#             LOG.debug("message: %s", pformat(message))
#             push_to_sinks(CONFIG, message)
#         return json_data, 202
#     else:
#         return "Content-Type not supported!", 204


@app.route("/post_json", methods=["POST"])
def process_json():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        json_data = request.json
        LOG.debug("### the request ###############################################################")
        LOG.debug("json_body: %s", pformat(json_data))
        data = json.loads(request.data)
        for message in data:
            LOG.debug("message: %s", pformat(message))
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
        # type=argparse.FileType('r'),
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
