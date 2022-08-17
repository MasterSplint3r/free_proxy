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

	def remove_port_mapping(self, local, remote):

		"""
		Find our port forwarding rule by bruteforce.
		This is done because not all UPNP implementations support 'getportmappingnumberofentries'.
		Iterating the first ten rules shoudl be sufficient.
		"""
		for i in range(10):
			rule = self.upnp.getgenericportmapping(i)
			r_port, local_pair = rule[0], rule[2]
			if r_port == remote and local_pair[0] == self.upnp.lanaddr and local_pair[1] == local:
				try:
					self.upnp.deleteportmapping(i, self.proto)
					return "[+] Port mapping closed successfully"
				except Exception as e:
					return f"[-] {e}"
	
	def get_external_ip(self):
		return self.upnp.externalipaddress()



