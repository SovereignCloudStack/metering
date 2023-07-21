# Metering Sink

This tool is a proof-of-concept for directly using Ceilometer HTTP/JSON
publisher data to implement metering for the purposes of billing customers for
resource usage.

The motivation is that many cloud service providers these days go beyond just
IaaS (or IaaS may even just be a means to an end, e.g. for PaaS offerings on
top). This generally implies that built-in end-to-end mechanisms in OpenStack
for billing may not be adequate or there already exist platforms which handle
the billing process which must be integrated into OpenStack.

The OpenStack Ceilometer project collects resource usage information from event
and polled data throughout OpenStack. It provides this usage data to a
"web hook" (HTTP publisher) in realtime.

The tool in this repository uses this data to decompose and process it and
write it into any of the pluggable backends.

**Note:** This tool is in a proof-of-concept stage.

Currently, two plugins exist:

* The odoo plugin which writes to an Odoo sales-order
* A simple textfile output for debugging purposes.

## Usage

To use the api just start it with
```shell
$ python -m metersink
```

For usage please consult:

```shell
$ python -m metersink -h
usage: __main__.py [-h] [--config CONFIG_FILE] [-v]

options:
  -h, --help            show this help message and exit
  --config CONFIG_FILE, -c CONFIG_FILE
                        The config file to use
  -v, --verbose         increase output verbosity

```

## Configuration

Refer to `settings_template.conf` for additional documentation on the
configuration. Copy the template and pass the path to the copy via the `-c`
command line flag to use it.
