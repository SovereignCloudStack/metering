"""
Library to find odoo related functions
"""
import logging
import xmlrpc.client
from datetime import datetime
from pprint import pformat

LOG = logging.getLogger(__name__)


def get_client(odoo, client="common"):
    """returns the client"""
    if "url" in odoo:
        url = odoo["url"]
    else:
        url = odoo
    if client == "models":
        client = "object"
    client = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{client}")
    return client


def get_odoo_version(url):
    """gets the odoo version"""
    try:
        common = get_client(url)
        version = common.version()
        return version
    except xmlrpc.client.ProtocolError:
        LOG.exception("failed to obtain odoo version")
    return None


def odoo_get(odoo, model, mode="ids", filter_list=None, projection_dict=None):
    """
    returns matching records
    """

    if not filter_list:
        filter_list = [[]]

    if mode == "records":
        mode = "search_read"
    elif mode == "fields":
        mode = "fields_get"
        projection_dict = {"attributes": ["string", "help", "type"]}
    elif mode == "ids":
        mode = "search"
    elif mode == "rights":
        mode = "check_access_rights"
    elif mode == "read":
        pass

    models = get_client(odoo, client="models")

    # todo make that less ugly
    if not projection_dict:
        records = models.execute_kw(
            odoo["db"], odoo["user_id"], odoo["password"], model, mode, filter_list
        )
        # projection_dict = {}
    else:
        records = models.execute_kw(
            odoo["db"],
            odoo["user_id"],
            odoo["password"],
            model,
            mode,
            filter_list,
            projection_dict,
        )
    return records

def odoo_get_contact_from_tag(odoo, tag):
    filter_list = [
        [
            ["category_id", "=", tag],
        ]
    ]

    projection_dict = {
        "fields": [
            "active",
            "category_id",
            "id",
            "comment",
            "company_name",
            "currency_id",
            "customer_rank",
            "employee",
            "invoice_ids",
            "is_company",
            "name",
            "parent_id",
            "phone",
            "sale_order_ids",
            "sla_ids"
        ],
        "limit": 1,
    }
    contact = get_odoo_partner(odoo, filter_list=filter_list, projection_dict=projection_dict)
    if not contact:
        LOG.info("No contact found for tag: %s", tag)
    else:
        LOG.debug("found contact: %s", pformat(contact))
    return contact


def odoo_get_customer_from_project(odoo, project_id):
    tag = f"project={project_id}"
    customer = odoo_get_contact_from_tag(odoo, tag)
    if not customer:
        LOG.info("No customer found for project: %s", project_id)
    else:
        LOG.debug("found customer: %s", pformat(customer))
    return customer


def get_sales_orders(odoo, mode="ids", filter_list=None, projection_dict=None):
    sale_orders = odoo_get(
        odoo,
        "sale.order",
        mode=mode,
        filter_list=filter_list,
        projection_dict=projection_dict,
    )
    return sale_orders

def odoo_get_sales_order(odoo, filter):
    pass

def show_sales_order_fields(odoo):
    LOG.debug(
        "%s", pformat(odoo_get(odoo, "sale.order", mode="fields"))
    )
    LOG.debug(
        "%s",
        pformat(odoo_get(odoo, "sale.order.line", mode="fields")),
    )


def odoo_create(odoo, model, record_list):
    """
    creates a record in odoo and returns its id
    """
    models = get_client(odoo, client="models")
    record_id = models.execute_kw(
        odoo["db"], odoo["user_id"], odoo["password"], model, "create", record_list
    )
    return record_id


def odoo_update(odoo, model, record_id, data_dict):
    """
    updates an odoo record
    :param odoo:
    :param model:
    :param record_id:
    :param data_dict:
    :return: record_id
    """
    models = get_client(odoo, client="models")
    record_id = models.execute_kw(
        odoo["db"],
        odoo["user_id"],
        odoo["password"],
        model,
        "write",
        [[record_id], data_dict],
    )
    return record_id


def get_odoo_user_id(odoo):
    """
    Takes the odoo config and tries to claim the user_id from the odoo user
    """
    try:
        common = get_client(odoo)
        user_id = common.authenticate(
            odoo["db"], odoo["user_name"], odoo["password"], {}
        )
        return user_id
    except (OSError, xmlrpc.client.ProtocolError):
        LOG.exception("failed to get user ID from odoo")
    return None


def get_odoo_partner(odoo, filter_list=None, projection_dict=None):

    LOG.debug(
        "partner %s",
        pformat(odoo_get(odoo, "res.partner", mode="fields")),
    )
    if not filter_list:
        filter_list = []
    partner = odoo_get(
        odoo, "res.partner", mode="records", filter_list=filter_list, projection_dict=projection_dict
    )
    return partner
