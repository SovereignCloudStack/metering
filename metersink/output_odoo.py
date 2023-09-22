"""
Library to find odoo related functions
"""
import logging
import xmlrpc.client
from datetime import datetime
from pprint import pformat

from metersink.lib import *

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


def get_projection_dict(model=None, limit=None):
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

def odoo_get_contact_from_tag(odoo, tag_list, limit=None):
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


def odoo_get_customer_from_project(odoo, tag_list):
    """Is looking for a customer with given tag"""
    #tag = f"project={project_id}"
    customer_list = odoo_get_contact_from_tag(odoo, tag_list, limit=1)
    if not customer_list:
        LOG.info("No customer found for tags: %s", tag_list)
    else:
        LOG.debug("found customer: %s", pformat(customer_list))
    return customer_list


def get_sale_orders(odoo, mode="ids", filter_list=None, projection_dict=None):
    sale_orders = odoo_get(
        odoo,
        "sale.order",
        mode=mode,
        filter_list=filter_list,
        projection_dict=projection_dict,
    )
    return sale_orders


def show_sale_order_fields(odoo):
    """
    This is for debugging or getting information about special models in odoo
    The Sale-Order and Sale-Order Line Model
    """
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


def odoo_handle_os_volumes(odoo, data_dict):
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(
            "%s", pformat(odoo_get(odoo, "sale.order", mode="fields"))
        )
        LOG.debug(
            "%s",
            pformat(odoo_get(odoo, "sale.order.line", mode="fields")),
        )

    project_id = data_dict["traits"]["project_id"]

    # todo do we need this state and ref?
    filter_list = [
        [["client_order_ref", "=", project_id], ["state", "=", "sale"]]
    ]

    projection_dict = get_projection_dict(model="sale.order", limit=1)
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
        # projection_dict = get_projection_dict(model="sale.order.line")

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
            # we are reading the last state of the line and calculate the time between this line and the update message.

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
        else:
            # If there is no line already for the ressource, create it.

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

    [customer] = odoo_get_customer_from_project(odoo, tag_list)
    if customer:
        print(pformat(customer))
        print(customer["sale_order_ids"])

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


def get_sale_order_line():
    """to be implemented"""
    pass


def get_product_id(odoo, product_name):
    """this is looking for the corresponding product_id in odoo"""
    # fixme
    product_id = odoo_get(odoo,
                          "res.product",
                          mode="ids",
                          filter_list=[["display_name", "=", product_name]],
                          projection_dict={"limit": 1},
                          )
    return product_id


def odoo_handle_os_instances(odoo, data_dict):
    """
    handles instances
    """
    #LOG.debug("instance data: %s", pformat(data))
    # data_dict = message_to_dict(data)
    LOG.debug("instance data: %s", pformat(data_dict))
    project_id = data_dict["traits"]["project_id"]
    tag_list = [f"project={project_id}"]

    sale_order_id = get_sale_order_id(odoo, [tag_list])


    if sale_order_id:
        # if resource is already in a sale.order.line update it
        # if no such line exists, create it.


        # create
        if data_dict.get('event_type') == "compute.instance.create.end":
            LOG.debug("creating instance data: %s", data_dict)
        # update
        # delete


def odoo_handle(odoo_sinks, conf, data):
    for index, sink_name in enumerate(odoo_sinks["name"]):
        odoo_version = get_odoo_version(sink_name)
        if not odoo_version:
            raise xmlrpc.client.Error("The odoo endpoint could not be found.")
        LOG.debug("Odoo version is %s", odoo_version)
        odoo_conf = get_config_section(conf, section="odoo")

        odoo = setup_odoo_object(sink_name, odoo_conf, index)

        data = message_to_dict(data)

        if data.get("event_type"):
            LOG.debug("### Event %s", data["event_type"])

            if data["event_type"].startswith("volume"):
                # look for a sale_order to progress on
                odoo_handle_os_volumes(odoo, data)

            elif data["event_type"].startswith("image"):
                # image.send
                pass
            elif data["event_type"].startswith("scheduler"):
                # scheduler.select_destinations.start
                # scheduler.select_destinations.end
                pass
            elif data["event_type"].startswith("compute"):
                # compute.instance.update
                # compute.instance.create.start
                # compute.instance.create.end
                odoo_handle_os_instances(odoo, data)

            elif data["event_type"].startswith("port"):
                # port.create.start
                # port.create.end
                # port.update.start
                # port.update.end
                pass

        else:
            LOG.debug("### Polling %s", data["name"])
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
