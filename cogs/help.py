import discord
from discord.ext import commands

HELP_MUSICA = (
    "🌸 Comandos disponibles — Bot musical 🎶\n\n"
    "Hey~ (≧◡≦)ゞ\n"
    "Aquí tienes la lista de comandos para disfrutar de la música como se debe ♪\n\n"
    "🎵 Reproducción y control\n\n"
    "🌸 #play <url | nombre> → Reproduce una canción desde YouTube o Spotify. Si no pones link, busca por nombre.\n\n"
    "🌸 #pause → Pausa la canción actual (っ˘ω˘ς).\n\n"
    "🌸 #resume → Reanuda la música pausada (ง •̀_•́)ง.\n\n"
    "🌸 #stop → Detiene todo y limpia la cola (╥﹏╥).\n\n"
    "🌸 #skip → Salta a la siguiente canción ⏭️.\n\n"
    "📜 Información\n\n"
    "🌸 #queue → Muestra la lista de canciones en espera (⌒‿⌒).\n\n"
    "🌸 #nowplaying → Muestra la canción actual con su duración y autor.\n\n"
    "🌸 #lyrics [nombre] → Muestra la letra de la canción actual o la que indiques 🎤.\n\n"
    "🎧 Conexión\n\n"
    "🌸 #join → Hace que el bot entre a tu canal de voz (づ｡◕‿‿◕｡)づ.\n\n"
    "🌸 #leave → Desconecta al bot y limpia la cola 💨.\n\n"
    "🔁 Control de cola\n\n"
    "🌸 #loop [song | queue | off] → Repite una canción o toda la lista ♻️.\n\n"
    "🌸 #shuffle → Mezcla el orden de la cola como un DJ loco (≧▽≦).\n\n"
    "🌸 #remove <posición> → Elimina una canción específica de la cola 🗑️.\n\n"
    "🌸 Disfruta de la música, comparte el ritmo y deja que el bot haga el resto~ (✿◠‿◠)"
)

HELP_IA = (
    "🌸 Comandos disponibles — IA Conversacional 🤖\n\n"
    "Konnichiwa~ (◕‿◕✿)\n"
    "¡Ahora puedo conversar contigo usando inteligencia artificial!\n\n"
    "🤖 Comandos de IA\n\n"
    "🌸 #ia <mensaje> → Chatea conmigo usando IA. Mantengo el contexto de la conversación (｡◕‿◕｡).\n\n"
    "🌸 #ia_reset → Reinicia el historial de conversación para empezar de nuevo ♻️.\n\n"
    "💡 Nota: Solo funciona en el canal designado del servidor.\n\n"
    "🌸 Powered by IBM Granite ✨"
)

HELP_GENERAL = (
    "🌸 Sthashior Bot - Menú de Ayuda 🌸\n\n"
    "Hola~ (づ｡◕‿‿◕｡)づ\n"
    "Soy Sthashior, tu bot multifuncional kawaii!\n\n"
    "📚 Secciones disponibles:\n\n"
    "🎵 `#help musica` → Comandos de música\n"
    "🤖 `#help ia` → Comandos de IA conversacional\n"
    "🎲 `#datorandom` o `#dt` → Dato random del servidor\n\n"
    "🌸 ¡Disfruta y diviértete! (✿◠‿◠)"
)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx: commands.Context, *, seccion: str | None = None):
        if seccion and seccion.lower() == "musica":
            await ctx.send(HELP_MUSICA)
            return
        if seccion and seccion.lower() == "ia":
            await ctx.send(HELP_IA)
            return
        await ctx.send(HELP_GENERAL)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
