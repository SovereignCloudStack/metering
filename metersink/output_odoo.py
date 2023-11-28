"""
Library to find odoo related functions
"""
import logging
import xmlrpc.client
from datetime import datetime
from pprint import pformat

from metersink.lib import (
    calculate_cloud_time,
    get_name_from_info,
    message_to_dict,
    get_config_section,
)

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

def get_projection_dict(model=None, limit=None) -> dict:
    """Provides mapping for viewable fields based on their model."""
    projection_dict = {}
    if limit:
        projection_dict["limit"] = limit
    if not model:
        pass
    elif model == "sale.order":
        projection_dict["fields"] = [
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
        ]

    elif model == "sale.order.line":
        projection_dict["fields"] = [
            "id",
            'product_id',
            'display_name',
            'product_uom_qty',
            'order_id',
        ]

    elif model == "res.partner":
        projection_dict["fields"] = [
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
                "sla_ids",
            ]

    return projection_dict

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

def odoo_get_contact_from_tag(odoo, tag_list, limit=None) -> list:
    """is looking for a res partner, that has special tags"""
    filter_list = [
        [
            ["category_id", "in", tag_list],
        ]
    ]

    projection_dict = get_projection_dict(model="res.partner", limit=limit)
    contact_list = get_odoo_partner(odoo, filter_list=filter_list, projection_dict=projection_dict)
    if not contact_list:
        LOG.info("No contact found for tags: %s", tag_list)
    else:
        LOG.debug("found contact: %s", pformat(contact_list))
    return contact_list

def get_sale_orders(odoo, mode="ids", filter_list=None, projection_dict=None):
    """
    returns SOs by filter
    """
    sale_orders = odoo_get(
        odoo,
        "sale.order",
        mode=mode,
        filter_list=filter_list,
        projection_dict=projection_dict,
    )
    return sale_orders

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
    """
    returns a res.partner record
    """
    show_fields(odoo, "res.partner")

    if not filter_list:
        filter_list = []
    partner = odoo_get(
        odoo, "res.partner",
        mode="records",
        filter_list=filter_list,
        projection_dict=projection_dict
    )
    return partner

def setup_odoo_object(url, odoo_settings, settings_position):
    """returns odoo client information"""
    odoo = {
        "url": url,
        "db": odoo_settings["odoo_db"][settings_position],
        "user_name": odoo_settings["odoo_user_name"][settings_position],
        "password": odoo_settings["odoo_api_key"][settings_position],
        }
    odoo["user_id"] = get_odoo_user_id(odoo)
    return odoo

def create_sale_order(odoo, customer, tag_list):
    """creates a new SO for customer with tags"""
    record_list = [
                {
                    "partner_id": customer['id'],
                    "category_ids": tag_list
                }
            ]
    new_id = odoo_create(odoo, "sale.order", record_list)
    return new_id

def create_sale_order_line(odoo, order_id, product_id, display_name, product_uom_qty):
    """creates a new so line and returns its id"""
    record_list = [
        {
            "order_id": order_id,
            "product_id": product_id,
            "display_name": display_name,
            "product_uom_qty": product_uom_qty,
        }
    ]
    new_id = odoo_create(odoo, "Sale.order.line", record_list)
    return new_id

def get_sale_order_id(odoo, tag_list):
    """
    Returns the id of a Sale_order to further work on if the Customer is known.
    Else it gives nothing back.
    """
    # project_tag = f"project={project_id}"

    [customer] = odoo_get_contact_from_tag(odoo,tag_list, limit=1)
    if customer:
        LOG.debug("%s",pformat(customer))
        LOG.debug("%s",customer["sale_order_ids"])

        if LOG.isEnabledFor(logging.DEBUG):
            show_sale_order_fields(odoo)
        filter_list = [
            #"|",
            ["customer_id" , "=", customer["id"]],
            #["category_ids", "=", project_tag]
        ]
        projection_dict = get_projection_dict()
        [sale_order_id] = odoo_get(
            odoo,
            "sale.order",
            mode="ids",
            filter_list=filter_list,
            projection_dict=projection_dict,
        )

        if not sale_order_id:
            # create new sale order
            sale_order_id = create_sale_order(odoo, customer, tag_list)
        return sale_order_id
    return None

def get_sale_order_line(odoo, filter_list, create=True):
    """returns a so line"""
    line_record = odoo_get(
            odoo,
            "sale.order.line",
            mode="search_read",
            filter_list=filter_list,
        )
    if not line_record and create:
        line_record = odoo_create(odoo, "sale.order.line", [
            {}
        ])
    return line_record

def get_product_id(odoo, product_name, create=True):
    """this is looking for the corresponding product_id in odoo"""
    product_id = odoo_get(odoo,
                          "res.product",
                          mode="ids",
                          filter_list=[["display_name", "=", product_name]],
                          projection_dict={"limit": 1},
                          )
    if not product_id and create:
        product_id = odoo_create(odoo, "res.product", [
            {"display_name": product_name}
        ])
    else:
        LOG.debug("There is no product %s",product_name)
    return product_id

def is_supported() -> tuple:
    """
    this returns a tuple of supported resources
    """
    supported_resource_list = [
        "volume",
        # "image",
        "compute",
        # "scheduler",
        # "port",
    ]
    supported_resources = tuple(supported_resource_list)
    return supported_resources

def odoo_handle_os_resource(odoo, data):
    """
    reads and writes into odoo sale-order
    """
    if LOG.isEnabledFor(logging.DEBUG):
        show_fields(odoo, "sale.order")
        show_fields(odoo, "sale.order.line")

    project_id = data["traits"]["project_id"]
    tag_list = [f"project={project_id}"]
    sale_order_id = get_sale_order_id(odoo, tag_list)
    LOG.debug("so id %s", sale_order_id)

    product_name = "noname"
    value_list = []

    if data["event_type"].startswith("volume"):
        product_name = "volume"
        value_list = [str(data["traits"]["size"])]
    elif data["event_type"].startswith("compute"):
        product_name = "compute"
        value_list = [data["traits"]["flavor_name"]]
    elif data["event_type"].startswith("image"):
        # todo to be implemented
        # image.send
        pass
    elif data["event_type"].startswith("scheduler"):
        # todo to be implemented
        # scheduler.select_destinations.start
        # scheduler.select_destinations.end
        pass
    elif data["event_type"].startswith("port"):
        # todo to be implemented
        # port.create.start
        # port.create.end
        # port.update.start
        # port.update.end
        pass

    product_id = get_product_id(odoo, product_name)
    end_date = datetime.now()
    time_calc = calculate_cloud_time(
        data["traits"]["created_at"], end_date
    )

    info_dict = {
            "uuid": data["traits"]["resource_id"],
            "name": data["traits"]["display_name"],
            "values": value_list,
            "start": data["traits"]["created_at"],
            "end": end_date,
        }
    display_name = get_name_from_info(info_dict)

    filter_list = [
                [
                    ["order_id", "=", sale_order_id],
                    ["product_id", "=", product_id],
                ]
            ]

    line_record = get_sale_order_line(odoo, filter_list, create=False)
    if line_record:
        # we are reading the last state of the line and
        # calculate the time between this line and the update message.
        LOG.debug("%s", pformat(line_record))
        time_calc = calculate_cloud_time(line_record["name"])

        odoo_update(
            odoo,
            "sale.order.line",
            line_record["id"],
            {"product_uom_qty": time_calc},
        )

    else:
        # If there is no line already for the ressource, create it.
        line_id = create_sale_order_line(odoo,
                                         sale_order_id,
                                         product_id,
                                         display_name,
                                         time_calc,
                                         )
        LOG.debug("%s", line_id)

def odoo_handle(odoo_sinks, conf, data):
    """
    handle multiple odoo instances and pipeline events and polling
    """
    for index, sink_name in enumerate(odoo_sinks["name"]):
        odoo_version = get_odoo_version(sink_name)
        if not odoo_version:
            raise xmlrpc.client.Error("The odoo endpoint could not be found.")
        LOG.debug("Odoo version is %s", odoo_version)
        odoo_conf = get_config_section(conf, section="odoo")

        odoo = setup_odoo_object(sink_name, odoo_conf, index)

        data = message_to_dict(data)
        supported_resources = is_supported()

        if data.get("event_type"):
            LOG.debug("### Event %s", data["event_type"])

            if data["event_type"].startswith(supported_resources):
                odoo_handle_os_resource(odoo, data)
            else:
                LOG.info("### Event %s is not supported", data["event_type"])

        else:
            LOG.debug("### Polling %s", data["name"])
            # todo to be implemented
            # polling in observed chronological order
            # image.serve
            # disk.ephemeral.size
            # network.incoming.bytes.delta
            # network.outgoing.bytes.delta
            # memory.swap.in
            # memory.usage
            # memory.swap.out
            # cpu
            # memory.resident
            # image.size
            # network.incoming.packets
            # network.outgoing.packets
            # disk.device.read.latency
            # network.incoming.bytes
            # volume.size
            # network.incoming.packets.drop
            # disk.device.capacity
            # disk.device.usage
            # network.outgoing.bytes
            # disk.device.read.requests
            # disk.device.write.bytes
            # disk.device.read.bytes
            # disk.device.allocation
            # network.incoming.packets.error
            # network.outgoing.packets.error
            # network.outgoing.packets.drop
            # disk.device.write.latency
            # disk.device.write.requests

### debug helper functions ####################################################
def show_fields(odoo, model):
    """
    for debugging purpose
    """
    LOG.debug(
        "%s %s", model ,pformat(
            odoo_get(odoo, model, mode="fields")
        )
    )

def show_sale_order_fields(odoo):
    """
    This is for debugging or getting information about special models in odoo
    The Sale-Order and Sale-Order Line Model
    """
    show_fields(odoo, "sale.order")
    show_fields(odoo, "sale.order.line")

###############################################################################
