#! /usr/bin/env python3
import json
import requests
from jinja2 import Environment, FileSystemLoader
import os
from requests.auth import HTTPBasicAuth

def get_key(node):
    value = node["traffic_total"]
    if value.find("GB") != -1:
        value = float(node["traffic_total"].replace("GB","").strip()) * 1000
    else:
        value = float(node["traffic_total"].replace("MB","").strip())
    return int(value)

def stripModel(model):
    return model.replace("TP-Link","").replace("Buffalo","").replace("Ubiquiti","").replace("NETGEAR","").strip()

def convertUptime(seconds):
    time = round(seconds / 3600,2)
    if(24 <  time):
        return "{} d".format(str(round(time/ 24,2)))
    else:
        return "{} h".format(time)

def convertTraffic(node):
    for x in ['traffic_total', 'traffic_tx', 'traffic_rx']:
        if (node[x] > 10000):
            node[x] = "{} GB".format(round(node[x] / 1000),2)
        else:
            node[x] = "{} MB".format(int(node[x]))

def getLoadColor(load):
    if load < 0.5:
        return "green"
    elif 0.5 <= load < 0.8:
        return "yellow"
    else:
        return "red"

if __name__ == "__main__":
    path = os.path.dirname(os.path.realpath(__file__))
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template('layout.html')

    r =  requests.get("http://gw04.darmstadt.freifunk.net/alfred/158.json", auth=HTTPBasicAuth('fleaz', 'aaV7Czzk'))
    alfred_158 = json.loads(r.text)

    r =  requests.get("http://gw04.darmstadt.freifunk.net/alfred/159.json", auth=HTTPBasicAuth('fleaz', 'aaV7Czzk'))
    alfred_159 = json.loads(r.text)

    macs = []
    network = []

    # iterate over the data to get the mac of every router
    for node in alfred_158:
        macs.append(node)

    # get  the data for every mac
    for mac in macs:
        node = {}

        ## get data from 158
        json_158 = alfred_158[mac]
        node['name'] = json_158['hostname']
        try:
            node['model'] = json_158['hardware']['model']
            node['type'] = "router"
        except:
            node['model'] = "Server"
            node['type'] = "server"

        if node['type'] == "server":
            node['autoupdater'] = "-"
            node['branch'] = None
            node['firmware'] = json_158['software']['firmware']['base']
        else:
            node['autoupdater'] = json_158['software']['autoupdater']['enabled']
            node['branch'] = json_158['software']['autoupdater']['branch']
            node['firmware'] = json_158['software']['firmware']['release']

        # try to get GPS data
        try:
            node['long'] = json_158['location']['longitude']
            node['lat'] = json_158['location']['latitude']
        except:
            node['long'] = None
            node['lat'] = None

        ## get data from 159
        json_159 = alfred_159[mac]
        node['uptime'] =  json_159['uptime']
        node['traffic_tx'] = json_159['traffic']['tx']['bytes'] / 1000000
        node['traffic_rx'] = json_159['traffic']['rx']['bytes'] / 1000000
        node['traffic_total'] = node['traffic_tx'] + node['traffic_rx']
        node['load'] = json_159['loadavg']

        ## enhance the date
        # Remove manufacturer name
        node['model'] = stripModel(node['model'])
        # convert sec to hours
        node['uptime'] =  convertUptime(node['uptime'])
        # convert traffic to gb if needed
        convertTraffic(node)
        # get color for current load
        node['loadcolor'] = getLoadColor(node['load'])

        network.append(node)

    sorted = sorted(network, key=get_key, reverse=True)

    print (template.render(data=sorted))

