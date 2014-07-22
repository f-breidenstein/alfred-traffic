#! /usr/bin/ern python3
import json
import subprocess
from jinja2 import Environment, FileSystemLoader
import os


def get_key(item):
    return item['total']


if __name__ == "__main__":
    path = os.path.dirname(os.path.realpath(__file__))
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template('layout.html')

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
        node['rx'] = node_json['statistics']['traffic']['tx']['bytes'] / 1000000
        node['tx'] = node_json['statistics']['traffic']['rx']['bytes'] / 1000000
        node['total'] = node['rx'] + node['tx']
        network.append(node)

    sorted = sorted(network, key=get_key, reverse=True)
    print (template.render(data=sorted))
