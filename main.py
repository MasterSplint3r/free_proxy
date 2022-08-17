#!/usr/bin/python3
import consts
from telegram_handler import TelegramHandler

def main():
	telegram_bot = TelegramHandler(consts.API_KEY)
	telegram_bot.start_bot()

if __name__ == "__main__":
	main()
