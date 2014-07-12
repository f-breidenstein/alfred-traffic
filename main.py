#! /usr/bin/ern python3
import json
json_data=open('alfred.json')

alfred = json.load(json_data)

print("%30s %12s %12s" % ("Name", "MByte RX", "MByte TX") )

nodes = []

for node in alfred:
    nodes.append(node)

for mac in nodes:
    name = alfred[mac]['hostname']
    tx = alfred[mac]['statistics']['traffic']['tx']['bytes'] / 1000000
    rx = alfred[mac]['statistics']['traffic']['rx']['bytes'] / 1000000
    print("%30s %12d %12d" % (name, rx, tx) )

json_data.close()
