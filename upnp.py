#!/usr/bin/python3
import miniupnpc
from socks import *

class UpnpHandler:
	def __init__(self):
		self.upnp = miniupnpc.UPnP()
		self.upnp.discoverdelay = 3
		self.upnp.discover()
		self.upnp.selectigd()
		self.proto = 'TCP'

	def add_port_mapping(self, local, remote):
		# addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
		self.upnp.addportmapping(remote, self.proto, self.upnp.lanaddr, local, 'proxy', '')

	def remove_port_mapping(self, remote):
		try:
			self.upnp.deleteportmapping(remote, self.proto)
			return "[+] Port mapping closed successfully"
		except Exception as e:
			return f"[-] {e}"
	
	def get_external_ip(self):
		return self.upnp.externalipaddress()



