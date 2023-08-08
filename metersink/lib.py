import configparser
import logging
import re
from datetime import datetime, timedelta

from metersink.output_odoo import (
    get_odoo_version,
    odoo_get,
    get_odoo_user_id,
    odoo_create,
    odoo_update,
)
from metersink.output_textfile import output_file

from pprint import pformat


LOG = logging.getLogger(__name__)

def dump_config(cfg):
    """
    Emit a config dump to the DEBUG log level.
    """
    LOG.debug("Config dump")
    for section in cfg.sections():
        LOG.debug("Section %s", section)
        for option in cfg[section]:
            LOG.debug("[%s]  %s = %s", section, option, cfg.get(section, option))


def get_config(path):
    """
    retrieves the config from the config file
    :return: config
    """
    cfg = configparser.ConfigParser()
    cfg.read_file(open(path))
    dump_config(cfg)
    return cfg


def get_config_section(_config, section=None):
    defaults = _config.defaults()

    if section:
        section_dict = {}
        if _config.has_section(section):
            for option in _config.options(section):
                if option in defaults:
                    continue
                values = [
                    v for v in _config.get(section, option).splitlines() if v.strip()
                ]
                if len(values):
                    section_dict[option] = values
        return section_dict


def get_sinks(conf):
    section = "output"
    section_dict = get_config_section(conf, section=section)
    output_dict = {}
    for key, value in section_dict.items():
        if conf.has_option(section, key):
            if conf.get(section, key) not in ["false", "False"]:
                output_dict[key] = {"name": section_dict[key]}

    for sink_name, values in output_dict.items():
        sink_conf = get_config_section(conf, sink_name)
        for key, value in sink_conf.items():
            output_dict[sink_name][key] = value

    return output_dict


def get_time(param):
    if param == "month_start":
        _time = datetime.today().replace(day=1)
    elif param == "month_end":
        next_month = datetime.today().replace(day=28) + timedelta(days=4)
        _time = next_month - timedelta(days=next_month.day)
    else:
        _time = datetime.now()
    return _time


def calculate_cloud_time(value1, value2=None):
    if not value2:
        value2 = get_time("month_end")

    delta = value2 - datetime.strptime(value1, "%Y-%m-%dT%H:%M:%S")
    value = int(round(delta.total_seconds() / 60))

    return value


def parse_so_line_name(text):
    """
    id values timestamps
    :param text:
    :return:
    """
    pattern = "(?P<uuid>[0-9a-z-]+)\n\((?P<values>\S+)\)\n(?P<start>[\d.T:]+) - (?P<end>[\d.T:]+)"
    data_dict = re.search(pattern, text)
    return data_dict


def get_info_from_message(message):
    info = message
    return info


def get_info_from_name(display_name):
    data_dict = parse_so_line_name(display_name)
    return data_dict


def get_name_from_info(info):
    display_name = f"{info['uuid']}\n{info['name']}\n({info['values']})\n{info['start']} - {info['end']}"
    return display_name


def message_to_dict(message):
    traits = message["traits"]
    traits_dict = {}
    for trait in traits:
        traits_dict[trait[0]] = trait[2]
    data_dict = message
    data_dict["traits"] = traits_dict
    return data_dict


def push_to_sinks(conf, data):
    sinks = get_sinks(conf)
    LOG.debug("pushing to sinks: %s", sinks)
    for sink_type, sink_values in sinks.items():
        if sink_type == "file":
            for index, sink_name in enumerate(sinks["file"]["name"]):
                output_file(sink_name, data)
        elif sink_type == "odoo":
            for index, sink_name in enumerate(sinks["odoo"]["name"]):
                odoo_version = get_odoo_version(sink_name)
                if not odoo_version:
                    raise Exception("The odoo endpoint could not be found.")
                LOG.debug("Odoo version is %s", odoo_version)
                odoo_conf = get_config_section(conf, section="odoo")

                odoo = {
                    "url": sink_name,
                    "db": odoo_conf["odoo_db"][index],
                    "user_name": odoo_conf["odoo_user_name"][index],
                    "password": odoo_conf["odoo_api_key"][index],
                }
                odoo["user_id"] = get_odoo_user_id(odoo)

                if data["event_type"].startswith("volume"):
                    if LOG.isEnabledFor(logging.DEBUG):
                        LOG.debug(
                            "%s", pformat(odoo_get(odoo, "sale.order", mode="fields"))
                        )
                        LOG.debug(
                            "%s",
                            pformat(odoo_get(odoo, "sale.order.line", mode="fields")),
                        )

                    # traits = data['traits']
                    # traits_dict = {}
                    # for trait in traits:
                    #     traits_dict[trait[0]] = trait[2]

                    data_dict = message_to_dict(data)

                    # project_id = traits_dict['project_id']
                    project_id = data_dict["traits"]["project_id"]
                    filter_list = [
                        [["client_order_ref", "=", project_id], ["state", "=", "sale"]]
                    ]
                    projection_dict = {
                        "fields": [
                            "id",
                            "user_id",
                            "type_name",
                            "visible_project",
                            "tag_ids",
                            "state",
                            "require_signature",
                            "require_payment",
                            "reference",
                            "project_ids",
                            "pricelist_id",
                            "partner_id",
                            "origin",
                            "order_line",
                            "name",
                            "id",
                            "display_name",
                            "create_uid",
                            "client_order_ref",
                            "invoice_ids",
                        ],
                        "limit": 1,
                    }

                    [sale_orders] = odoo_get(
                        odoo,
                        "sale.order",
                        mode="records",
                        filter_list=filter_list,
                        projection_dict=projection_dict,
                    )
                    if not sale_orders:
                        line_dict = {
                            "partner_id": 75,
                            "client_order_ref": project_id,
                            "require_payment": False,
                            "require_signature": False,
                            "tag_ids": ["cloud", project_id],
                        }

                        sale_order_id = odoo_create(odoo, "sale.order", [line_dict])

                        end_date = datetime.now()
                        time_calc = calculate_cloud_time(
                            data_dict["traits"]["created_at"], end_date
                        )
                        value_list = [str(data_dict["traits"]["size"])]

                        info_dict = {
                            "uuid": data_dict["traits"]["resource_id"],
                            "name": data_dict["traits"]["display_name"],
                            "values": value_list,
                            "start": data_dict["traits"]["created_at"],
                            "end": end_date,
                        }
                        display_name = get_name_from_info(info_dict)

                        line_dict = {
                            "product_id": 36,
                            "display_name": display_name,
                            "product_uom_qty": time_calc,
                            "order_id": sale_order_id,
                        }
                        line_id = odoo_create(odoo, "sale.order.line", [line_dict])

                    else:
                        if LOG.isEnabledFor(logging.DEBUG):
                            LOG.debug("%s", pformat(sale_orders))

                        display_name = f"{data_dict['traits']['resource_id']} ({data_dict['traits']['size']}GB)"

                        # line_ids = sale_orders['order_line']
                        projection_dict = {
                            "fields": [
                                "id",
                                #'product_id',
                                #'display_name',
                                #'product_uom_qty',
                                #'order_id'
                            ]
                        }

                        # line_records = odoo_get(odoo, 'sale.order.line',
                        #                         mode='read',
                        #                         filter_list=[line_ids],
                        #                         # projection_dict=projection_dict
                        #                         )

                        line_record = odoo_get(
                            odoo,
                            "sale.order.line",
                            mode="search_read",
                            filter_list=[
                                [
                                    ["order_id", "=", sale_orders["id"]],
                                    ["product_id", "=", 36],
                                ]
                            ],
                            # projection_dict=projection_dict
                        )
                        if line_record:
                            # todo update
                            """
                            we are reading the last state of the line and calculate the time
                             between this line and the update message.
                            """

                            if LOG.isEnabledFor(logging.DEBUG):
                                LOG.debug("%s", pformat(line_record))

                            time_calc = calculate_cloud_time(line_record["name"])

                            quantity = 3000
                            odoo_update(
                                odoo,
                                "sale.order.line",
                                line_record["id"],
                                {"product_uom_qty": quantity},
                            )
                            pass
                        else:
                            """
                            If there is no line already for the ressource, create it.
                            """
                            time_calc = calculate_cloud_time(
                                data_dict["traits"]["created_at"]
                            )

                            line_dict = {
                                "product_id": 36,
                                "name": display_name,
                                "product_uom_qty": time_calc,
                                "order_id": sale_orders["id"],
                            }
                            line_id = odoo_create(odoo, "sale.order.line", [line_dict])
                            LOG.debug("%s", line_id)

    # LOG.debug('%s', conf)
    pass
