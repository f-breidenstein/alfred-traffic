#! /usr/bin/ern python3
import json
import subprocess
from jinja2 import Environment, FileSystemLoader
import os

path = os.path.dirname(os.path.realpath(__file__))
env = Environment(loader=FileSystemLoader(path))
template = env.get_template('layout.html')

def getKey(item):
    return item['total']

if __name__ == "__main__":
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
        node['uptime'] = node_json['statistics']['uptime']
        node['load'] = node_json['statistics']['loadavg']
        node['tx'] = node_json['statistics']['traffic']['tx']['bytes'] / 1000000
        node['rx'] = node_json['statistics']['traffic']['rx']['bytes'] / 1000000
        node['total'] = node['rx'] + node['tx']
        network.append(node)

    sorted = sorted(network, key=getKey, reverse=True)
    print (template.render(data=sorted))
