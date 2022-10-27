import asyncio
import os
import threading
import time
from discord.ext import commands
import discord
import logging
import dispatch_IDs
from cogs.play import g_id

IDs = dispatch_IDs.IDs()


def logger_setup():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename="JustBot.log", encoding="utf-8", mode='w')
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(handler)


class JustBot(commands.Bot):
    def __init__(self):
        super(JustBot, self).__init__('/////', intents=discord.Intents.all())

    @staticmethod
    async def on_connect():
        cog_reloader_thread.start()
        await bot.tree.sync(guild=discord.Object(g_id))
        print("Connected")

    @staticmethod
    async def on_ready():
        print("Ready!")


bot = JustBot()
cogs_path = "cogs"


async def main():
    for cog in os.listdir(cogs_path):
        if not cog.startswith("__"):
            await bot.load_extension(f"{cogs_path}.{cog[:-3]}".replace('/', '.'))
    await bot.login(token=IDs["BOT_TOKEN"])
    await bot.connect(reconnect=True)


def cog_reloader() -> None:
    _last_stamps = {}
    while True:
        time.sleep(2)
        try:
            for cog in os.listdir(cogs_path):
                stamp = os.stat(f"{cogs_path}/{cog}").st_mtime
                if cog.startswith("__"):
                    continue
                if cog not in _last_stamps:
                    _last_stamps[cog] = stamp
                elif stamp != _last_stamps[cog]:
                    print("reloaded", cog)
                    _last_stamps[cog] = stamp

                    async def task(passed_cog: str) -> None:
                        await bot.reload_extension(f"{cogs_path}.{passed_cog[:-3]}".replace('/', '.'))
                        # await bot.tree.sync(guild=discord.Object(g_id))

                    bot.loop.create_task(task(cog))
        except SyntaxError:
            print("SyntaxError")
            time.sleep(5)


if __name__ == '__main__':
    logger_setup()

    cog_reloader_thread = threading.Thread(target=cog_reloader)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        loop.close()
