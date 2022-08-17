from concurrent.futures import thread
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import threading
from upnp import UpnpHandler
from socks import SocksServer

class TelegramHandler(Updater):
	def __init__(self, api_key):
		self.upnp = UpnpHandler()
		self.server_thread = None
		#Setup updater object with bot's API key
		self.updater = Updater(api_key, use_context=True)
		#Register all of the handlers
		self.updater.dispatcher.add_handler(CommandHandler('start', self.start))
		self.updater.dispatcher.add_handler(CommandHandler('help', self.help))
		self.updater.dispatcher.add_handler(CommandHandler('open', self.start_proxy))
		self.updater.dispatcher.add_handler(CommandHandler('close', self.stop_proxy))
		self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.unknown))
		self.updater.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))

	def start_bot(self):
		self.updater.start_polling()
  
	def start(self, update: Update, context: CallbackContext):
		update.message.reply_text("Welcome to the free_proxy bot!")

	def help(self, update: Update, context: CallbackContext):
		update.message.reply_text(
								"The supported operations for this bot\n" +
								"/open Opens a port in the local network for incoming SOCKS requests\n" +
								"/close Closes the port-forwarding request and shuts down the SOCKS erver"
								)

	def start_proxy(self, update: Update, context: CallbackContext):
		update.message.reply_text("[+] Adding external port mapping")
		self.upnp.add_port_mapping(1080, 1080)
		update.message.reply_text("[+] Starting socks server on {ip}:1080".format(ip=self.upnp.get_external_ip()))
		self.server_thread = SocksServer()
		self.server_thread.start()
		
	def stop_proxy(self, update: Update, context: CallbackContext):
		update.message.reply_text("[+] Closing external port mapping")
		update.message.reply_text(self.upnp.remove_port_mapping(1080, 1080))
		#Set stop message to thread
		self.server_thread.stop_thread = True

	def unknown(self, update: Update, context: CallbackContext):
		update.message.reply_text(
			"Sorry '%s' is not a valid command" % update.message.text)