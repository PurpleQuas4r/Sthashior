import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

class SthashiorBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("cogs.music")
        await self.load_extension("cogs.help")
        await self.load_extension("cogs.datorandom")
        await self.load_extension("cogs.ai_chat")
        await self.load_extension("cogs.voice_ai")

        # Inicia un pequeño servidor HTTP para mantener vivo en Replit/Render/Koyeb
        async def handle_root(request: web.Request) -> web.Response:
            return web.Response(text="OK", status=200)

        app = web.Application()
        app.router.add_get("/", handle_root)

        port = int(os.environ.get("PORT", "3000"))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        await site.start()

bot = SthashiorBot(command_prefix="#", intents=intents, help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    if not token:
        raise RuntimeError("TOKEN no configurado en variables de entorno")
    bot.run(token)
