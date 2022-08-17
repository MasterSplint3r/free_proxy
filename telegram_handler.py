from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from utils import UpnpHandler
from socks import *

UPNP = UpnpHandler()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the free_proxy bot!")


def help(update: Update, context: CallbackContext):
    update.message.reply_text(
    						  "The supported operations for this bot\n" +
    						  "/open Opens a port in the local network for incoming SOCKS requests\n" +
    						  "/close Closes the port-forwarding request and shuts down the SOCKS erver"
    						 )


def start_proxy(update: Update, context: CallbackContext):
	update.message.reply_text("[+] Adding external port mapping")
	UPNP.add_port_mapping(1080, 1080)
	update.message.reply_text("[+] Starting socks server on {ip}:1080".format(ip=UPNP.get_external_ip()))
	start_server()

def stop_proxy(update: Update, context: CallbackContext):
	update.message.reply_text("[+] Closing external port mapping")
	update.message.reply_text(UPNP.remove_port_mapping(1080, 1080))

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text)


class TelegramHandler:
	def __init__(self, api_key):
		#Setup updater object with bot's API key
		self.updater = Updater(api_key, use_context=True)
		#Register all of the handlers
		self.updater.dispatcher.add_handler(CommandHandler('start', start))
		self.updater.dispatcher.add_handler(CommandHandler('help', help))
		self.updater.dispatcher.add_handler(CommandHandler('open', start_proxy))
		self.updater.dispatcher.add_handler(CommandHandler('close', stop_proxy))
		self.updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
		self.updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

	def start_bot(self):
		self.updater.start_polling()