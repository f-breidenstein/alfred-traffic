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
    data = []

    for node in alfred:
        macs.append(node)

    for mac in macs:
        nodeData = {}
        nodeData['name'] = alfred[mac]['hostname']
        nodeData['rx'] = alfred[mac]['statistics']['traffic']['tx']['bytes'] / 1000000
        nodeData['tx'] = alfred[mac]['statistics']['traffic']['rx']['bytes'] / 1000000
        nodeData['total'] = nodeData['rx'] + nodeData['tx']
        data.append(nodeData)


    
    sorted = sorted(data, key=getKey, reverse=True)
    print (template.render(data=sorted))
