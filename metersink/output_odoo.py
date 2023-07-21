"""
Library to find odoo related functions
"""
import xmlrpc.client
from datetime import datetime
from pprint import pprint


def get_client(odoo, client='common'):
    """returns the client"""
    if 'url' in odoo:
        url = odoo['url']
    else:
        url = odoo
    if client == 'models':
        client = 'object'
    client = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{client}")
    return client


def get_odoo_version(url):
    """gets the odoo version"""
    try:
        common = get_client(url)
        version = common.version()
        return version
    except xmlrpc.client.ProtocolError:
        print('there was an error connecting to odoo')
    return None


def odoo_get(odoo, model, mode="ids", filter_list=None, projection_dict=None):
    """
    returns matching records
    """

    if not filter_list:
        filter_list = [[]]

    if mode == "records":
        mode = "search_read"
    elif mode == 'fields':
        mode = 'fields_get'
        projection_dict = {'attributes': ['string', 'help', 'type']}
    elif mode == 'ids':
        mode = "search"
    elif mode == 'rights':
        mode = 'check_access_rights'

    # print(model, mode, filter_list, projection_dict)
    models = get_client(odoo, client='models')

    # todo make that less ugly
    if not projection_dict:
        records = models.execute_kw(
            odoo['db'], odoo['user_id'], odoo['password'], model, mode, filter_list
        )
        # projection_dict = {}
    else:
        records = models.execute_kw(
            odoo['db'], odoo['user_id'], odoo['password'],
            model, mode, filter_list, projection_dict
        )
    return records


def get_sales_orders(odoo, filter_list=None, projection_dict=None):
    sale_orders = odoo_get(odoo, 'sale.order',
                  mode='records',
                  filter_list=filter_list,
                  projection_dict=projection_dict)
    return sale_orders


def odoo_create(odoo, model, record_list):
    """
    creates a record in odoo and returns its id
    """
    models = get_client(odoo, client='models')
    record_id = models.execute_kw(odoo['db'], odoo['user_id'], odoo['password'],
                                  model, 'create', record_list)
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
    models = get_client(odoo, client='models')
    record_id = models.execute_kw(odoo['db'], odoo['user_id'], odoo['password'],
                                  model, 'write', [[record_id], data_dict])
    return record_id


def get_odoo_user_id(odoo):
    """
    Takes the odoo config and tries to claim the user_id from the odoo user
    """
    try:
        common = get_client(odoo)
        user_id = common.authenticate(odoo['db'],
                                      odoo['user_name'],
                                      odoo['password'],
                                      {})
        return user_id
    except xmlrpc.client.ProtocolError:
        print('there was an error connecting to odoo')
    except OSError:
        print('there was an error connecting to odoo')
    return None


def get_odoo_partner(odoo, filter_list=None, projection_dict=None):

    partner = odoo_get(odoo,
                       'res.partner',
                       filter_list=filter_list,
                       projection_dict=projection_dict
                       )
    return partner



# def get_account_id(odoo, tw_tag_list):
#     """
#     not used
#     """
#     print('get_account_id')
#     print(tw_tag_list)
#     account_id = None
#     models = get_client(odoo, client='models')
#
#     ids = models.execute_kw(odoo['db'], odoo['user_id'], odoo['password'],
#                             'account.analytic.line', 'search_read',
#                             [[['account_id.name', '=', 'odoo']]]
#                             # [[]]
#                             )
#     pprint(ids)
#     if ids:
#         account_id = ids[0]['account_id']
#         print('matched projects', ids)
#     return account_id


# def get_project_id(odoo, tw_tag_list):
#     """
#     returns the project_id for a tag list
#     """
#     # print('get_project_id')
#     project_id = None
#     for tag in tw_tag_list:
#         line = odoo_get(odoo, 'account.analytic.line',
#                         mode='records',
#                         filter_list=[[['project_id.name', '=', tag]]],
#                         projection_dict={'limit': 1})
#         if line:
#             print(line)
#             project_id = line[0]['project_id'][0]
#             break
#     # print(project_id)
#     return project_id



# def create_line_in_odoo_from_time_tracking_data(odoo, line):
#     """
#     takes the odo config and a dict and returns the line_id created by odoo on inserting the line
#     """
#
#     print(line)
#     # account_id = get_account_id(odoo, odoo_password, tw_line['tags'])
#     # print('account_is: ', account_id)
#     # company_id = get_company_id(odoo, odoo_password)
#
#     project_id = get_project_id(odoo, line['tags'])
#     if project_id:
#         name = 'TimeWarrior import ' + get_hash(line['start'])
#         date = str(datetime.date(line['start']))[:10]
#         amount = line['amount']
#         line_dict = {
#             'date': date,
#             'unit_amount': amount,
#             'name': name,
#             'project_id': project_id,
#         }
#         print('###############################################')
#         print(line_dict)
#
#         line_id = odoo_create(odoo, 'account.analytic.line', [line_dict])
#
#         print(line_id)
#         # new_id = get_analytic_line(odoo, [['id', '=', line_id]])
#         record = odoo_get(odoo, 'account.analytic.line',
#                           mode="record",
#                           filter_list=[[['id', '=', line_id]]],
#                           projection_dict={})
#         print('###############################################')
#         print('created line')
#         pprint(record)
#         return line_id
#     return None


# def get_employee_id(odoo, user_id=None):
#     """
#     returns the employee_id of a user
#     """
#     if not user_id:
#         user_id = odoo['user_id']
#     users = odoo_get(odoo, 'res.users',
#                      mode="records",
#                      filter_list=[[['id', '=', user_id]]],
#                      projection_dict={'fields': ['name', 'employee_id']}
#                      )
#     employee_id = users[0]['employee_id'][0]
#     # print(employee_id)
#     return employee_id


def create_invoice(data):
    pass


def get_invoice_line(data):
    pass


def open_invoice_line(data):
    pass


def close_invoice_line(data):
    pass


def create_flavor_produkt(data):
    pass


def is_in_odoo(odoo, model='account.analytic.line', line=None, filter_dict=None):
    """
    looks for already existing entries.
    """
    # print(line)
    if not filter_dict:
        filter_dict = {}

    filter_dict['date'] = str(datetime.date(line['start']))[:10]
    filter_dict['name'] = 'TimeWarrior import ' + get_hash(line['start'])
    filter_dict['employee_id'] = get_employee_id(odoo)

    filter_list = []
    for key, value in filter_dict.items():
        filter_list.append([key, '=', value])

    project_id = get_project_id(odoo, line['tags'])

    if not project_id:
        return False
    project = ['project_id.id', '=', project_id]
    filter_list.append(project)

    records = odoo_get(odoo, 'account.analytic.line',
                       mode="records",
                       filter_list=[filter_list],
                       projection_dict={'limit': 1}
                       )
    if records:
        # print('######### found records')
        # print(records)
        return True
    return False
