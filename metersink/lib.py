"""The basic library for the metering tool"""

import configparser
import logging
import re
from datetime import datetime, timedelta

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


def get_config_section(_config, section):
    """returns the config in a special section as dict"""
    defaults = _config.defaults()
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
    """returns the configured sinks from the settings"""
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
    """returns a timestamp now, start or end of the current month"""
    if param == "month_start":
        _time = datetime.today().replace(day=1)
    elif param == "month_end":
        next_month = datetime.today().replace(day=28) + timedelta(days=4)
        _time = next_month - timedelta(days=next_month.day)
    else:
        _time = datetime.now()
    return _time


def calculate_cloud_time(value1, value2=None):
    """returns the time between value1 and now or value2 in minutes"""
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
    pattern = r"(?P<uuid>[0-9a-z-]+)\n\((?P<values>\S+)\)\n(?P<start>[\d.T:]+) - (?P<end>[\d.T:]+)"
    data_dict = re.search(pattern, text)
    return data_dict


def get_info_from_name(display_name):
    """
    returns some dict like object, created from the so display_name
    """
    data_dict = parse_so_line_name(display_name)
    return data_dict


def get_name_from_info(info) -> str:
    """
    returns the so line display_name
    """
    display_name = (f"{info['uuid']}\n"
                    f"{info['name']}\n"
                    f"({info['values']})\n"
                    f"{info['start']} - {info['end']}")
    return display_name


def message_to_dict(message) -> dict:
    """turns the ceilometer message into a python dict"""
    traits = message["traits"]
    traits_dict = {}
    for trait in traits:
        traits_dict[trait[0]] = trait[2]
    data_dict = message
    data_dict["traits"] = traits_dict
    return data_dict
