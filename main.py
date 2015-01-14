#! /usr/bin/ern python3
import json
import requests
from jinja2 import Environment, FileSystemLoader
import os
from requests.auth import HTTPBasicAuth

def get_key(node):
    value = node["traffic_total"]
    if value.find("GB") != -1:
        return int(node["traffic_total"].replace("GB","")) * 1000
    else:
        return int(node["traffic_total"].replace("MB",""))

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

def getGateway(gw_mac):
    maclist={"2e:08:b9:56:9b:2f": "04",
             "12:d9:94:14:33:5c": "03"}
    return maclist[gw_mac]

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
        
        node['model'] = json_158['hardware']['model']
        node['autoupdater'] = json_158['software']['autoupdater']['enabled']
        node['branch'] = json_158['software']['autoupdater']['branch']
        node['firmware'] = json_158['software']['firmware']['release']

        try:
            node['long'] = json_158['location']['longitude']
            node['lat'] = json_158['location']['latitude']
        except:
            node['long'] = None
            node['lat'] = None

        ## get data from 159
        json_159 = alfred_159[mac]
        node['uptime'] =  json_159['uptime']
        node['gateway'] = json_159['gateway']
        node['traffic_tx'] = json_159['traffic']['tx']['bytes'] / 1000000
        node['traffic_rx'] = json_159['traffic']['rx']['bytes'] / 1000000
        node['traffic_total'] = node['traffic_tx'] + node['traffic_rx']
        node['load'] = json_159['loadavg']

        ## enhance the date
        # Remove manufacturer name
        node['model'] = stripModel(node['model'])
        # convert sec to hours
        node['uptime'] =  convertUptime(node['uptime'])
        # change GW MAC with name
        node['gateway'] = getGateway(node['gateway'])
        # convert traffic to gb if needed
        convertTraffic(node)
        # get color for current load
        node['loadcolor'] = getLoadColor(node['load'])

        network.append(node)

    sorted = sorted(network, key=get_key, reverse=True)

    print (template.render(data=sorted))

