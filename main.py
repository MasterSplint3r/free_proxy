#!/usr/bin/python3
import miniupnpc
import requests
from socks import *



def add_port_mapping(local, remote):
	upnp = miniupnpc.UPnP()
	upnp.discoverdelay = 10
	upnp.discover()
	upnp.selectigd()

	# addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
	upnp.addportmapping(remote, 'TCP', upnp.lanaddr, local, 'testing', '')


def get_external_ip():
	response = requests.get("http://icanhazip.com")
	return response.text.strip()

print("[+] Adding external port mapping")
add_port_mapping(1080, 1080)
print("[+] Starting socks server on {ip}:1080".format(ip=get_external_ip()))
start_server()
