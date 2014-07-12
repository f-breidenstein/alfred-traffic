#! /usr/bin/ern python3
import json
import subprocess
import HTML

def getKey(item):
    return item[3]

output = subprocess.check_output(["alfred-json","-r","158","-f","json","-z"])
alfred = json.loads(output.decode("utf-8"))

macs = []
t = []

for node in alfred:
    macs.append(node)

for mac in macs:
    name = alfred[mac]['hostname']
    tx = alfred[mac]['statistics']['traffic']['tx']['bytes'] / 1000000
    rx = alfred[mac]['statistics']['traffic']['rx']['bytes'] / 1000000
    sum = rx + tx
    t.append([name,rx,tx,sum])

sorted_table = sorted(t, key=getKey,  reverse=True)
htmlcode = HTML.table(sorted_table, header_row=['Name', 'MByte RX', 'MByte TX', 'MByte total'])

print htmlcode
