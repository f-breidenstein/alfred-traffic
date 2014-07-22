#! /usr/bin/ern python3
import json
import subprocess
from jinja2 import Environment, FileSystemLoader
import os
import sqlite3

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
    return item['total']


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

    output = subprocess.check_output(["alfred-json","-r","158","-f","json","-z"])
    alfred = json.loads(output.decode("utf-8"))

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
        node['version'] =  node_json['software']['firmware']['release']
        node['uptime'] = round(node_json['statistics']['uptime'] / 3600,2)

        #show uptime in days if it's bigger than 24h
        if(24 <  node['uptime']):
            node['uptime'] = "%s d" % (str(round(node['uptime'] / 24,2)))
        node['load'] = node_json['statistics']['loadavg']

        # Swap rx/tx beauce  it's meassured on the bat interface and not
        # on the Wifi interface. 
        # Rx on Bat0 == Tx on WiFi
        traffic_rx = node_json['statistics']['traffic']['tx']['bytes'] / 1000000
        traffic_tx = node_json['statistics']['traffic']['rx']['bytes'] / 1000000
        node['total'] = traffic_rx + traffic_tx

        traffic_sum, traffic_last = get_traffic(conn, node_name=node['name'])
        if node['total'] >= traffic_last:
            traffic_sum += node['total'] - traffic_last
        else:
            traffic_sum += node['total']
        update_traffic(conn,
                       node_name=node['name'],
                       traffic_sum=traffic_sum,
                       traffic_last=node['total'])

        network.append(node)

    sorted = sorted(network, key=get_key, reverse=True)
    print (template.render(data=sorted))

