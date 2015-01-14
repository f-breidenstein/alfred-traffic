#! /usr/bin/ern python3
import json
import requests
from jinja2 import Environment, FileSystemLoader
import os
import sqlite3
from requests.auth import HTTPBasicAuth

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS
        traffic
        (node_name text,
         traffic_sum int,
         traffic_last int);"""

GET_TRAFFIC_SQL = """
    SELECT
        traffic_sum,
        traffic_last
    FROM traffic
    WHERE node_name = ?;"""

UPDATE_TRAFFIC_SQL = """
    UPDATE
        traffic
    SET
        traffic_sum = ?,
        traffic_last = ?;"""

INSERT_TRAFFIC_SQL = """
    INSERT INTO
        traffic
    (node_name,
     traffic_sum,
     traffic_last)
    VALUES (?, ?, ?);"""


def get_key(item):
    val = item['total']
    if type(val) is str:
        return float(val.replace("GB","")) * 1000
    else:
        return val

def format_traffic(val):
    if type(val) is str:
        return val.replace("GB","")
    else:
        return int(val/1000.0)


def create_table(conn):
    c = conn.cursor()
    c.execute(CREATE_TABLE_SQL)


def get_traffic(conn, node_name):
    c = conn.cursor()
    c.execute(GET_TRAFFIC_SQL, (node_name,))
    result = c.fetchone()

    if result:
        traffic_sum, traffic_last = result
    else:
        traffic_sum = 0
        traffic_last = 0

    return traffic_sum, traffic_last


def update_traffic(conn, node_name, traffic_sum, traffic_last):
    c = conn.cursor()
    c.execute(UPDATE_TRAFFIC_SQL, (traffic_sum, traffic_last))
    conn.commit()

if __name__ == "__main__":
    path = os.path.dirname(os.path.realpath(__file__))
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template('layout.html')

    conn = sqlite3.connect('data.sqlite')
    create_table(conn)

    r =  requests.get("http://gw04.darmstadt.freifunk.net/alfred/158.json", auth=HTTPBasicAuth('fleaz', 'aaV7Czzk'))
    alfred = json.loads(r.text)

    r =  requests.get("http://gw04.darmstadt.freifunk.net/alfred/159.json", auth=HTTPBasicAuth('fleaz', 'aaV7Czzk'))
    alfred2 = json.loads(r.text)

    macs = []
    network = []

    # iterate over the data from alfred to get every mac address
    for node in alfred:
        macs.append(node)

    # get some of the data fileds from the data provided by alfred
    for mac in macs:
        node = {}
        node_json = alfred[mac]
        node['name'] = node_json['hostname']
        node['ip'] = node_json['network']['addresses'][0]
        node['branch'] = node_json['software']['autoupdater']['branch']
        node['autpupdater'] = node_json['software']['autoupdater']['enabled']
        node['version_full'] =  node_json['software']['firmware']['release']
        node['version'] = node['version_full']

        node['model'] = node_json['hardware']['model']

        node_json = alfred2[mac]
        node['uptime'] = round(node_json['uptime'] / 3600,2)

        # Strip Model names
        node['model'] = node['model'].replace("TP-Link","").replace("Buffalo","").replace("Ubiquiti","").replace("NETGEAR","").strip()

        #show uptime in days if it's bigger than 24h
        if(24 <  node['uptime']):
            node['uptime'] = "%s d" % (str(round(node['uptime'] / 24,2)))
        node['load'] = node_json['loadavg']

        # Swap rx/tx beauce  it's meassured on the bat interface and not
        # on the Wifi interface. 
        # Rx on Bat0 == Tx on WiFi
        traffic_rx = node_json['traffic']['tx']['bytes'] / 1000000
        traffic_tx = node_json['traffic']['rx']['bytes'] / 1000000

        node['total'] = traffic_rx + traffic_tx

        traffic_sum, traffic_last = get_traffic(conn, node_name=node['name'])

        if node['total'] == 0 or node['total'] >= traffic_last:
            traffic_sum += node['total'] - traffic_last
        else:
            traffic_sum += node['total']
        update_traffic(conn,
                       node_name=node['name'],
                       traffic_sum=traffic_sum,
                       traffic_last=node['total'])

        # show high traffic values in GB
        if (node['total'] > 10000):
            node['total'] = "%d GB" % (node['total'] / 1000)
        network.append(node)

    sorted = sorted(network, key=get_key, reverse=True)

    for x in network:
        x['total'] = format_traffic(x['total'])

    print (template.render(data=sorted))

