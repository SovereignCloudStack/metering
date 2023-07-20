# openstack_metering

This Tool is an endpoint for ceilometers http/json pipeline publisher.
It consumes raw Ceilometer data, and provides a library easy build plugins to send billing related metrics to the wanted billing administration.

already existing plugins are

* odoo sales-order interface
* simple textfile output

**_since this tool is still a PoC it is not recommended to use it in produktion.
Also, not all openstack resources can be processed yet._**

To use the api just start it with
```shell
$ python metering_api.py
```

For usage please consult
```shell
$ python metering_api.py -python
usage: metering_api.py [-h] [--config CONFIG_FILE] [-v]

options:
  -h, --help            show this help message and exit
  --config CONFIG_FILE, -c CONFIG_FILE
                        The config file to use
  -v, --verbose         increase output verbosity

```

For further configuration on billing endpoints and how to process incoming Data, just create a "settings.conf" file like this
```shell
$ cp settings_template.conf settings.conf
```
and edit it to your needs.