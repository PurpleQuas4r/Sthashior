import discord
import json
import random
import time
import asyncio
import re
from collections import defaultdict, deque
from discord.ext import commands
import wavelink
import aiohttp
import urllib.parse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("TOKEN")

# Variables para protección anti-spam y respuestas automáticas
user_command_history = defaultdict(deque)
ultima_respuesta_usada = {}
COOLDOWN_TIEMPO = 1800  # 30 minutos en segundos

# Intents necesarios
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# variable para almacenar las respuestas
datos_mostrados_recientemente = {}

# Crear bot
bot = commands.Bot(command_prefix="#", intents=intents)


# Cargar las respuestas desde un archivo JSON
def cargar_respuestas():
    with open('resp.json', 'r', encoding='utf-8') as f:
        return json.load(f)


# Credenciales de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get(""),
    client_secret=os.environ.get("")))

# Cola de canciones por servidor
queue = {}


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Verificar si el usuario ha enviado más de 10 comandos en el último minuto
    user_history = user_command_history[message.author.id]
    user_history.append(time.time())

    # Eliminar comandos viejos del historial
    while len(user_history) > 0 and time.time() - user_history[0] > 60:
        user_history.popleft()

    if len(user_history) >= 10:
        # Aplicar cooldown y eliminar mensajes
        bot.command_cooldowns = getattr(bot, 'command_cooldowns', {})
        bot.command_cooldowns[message.author.id] = time.time() + 60
        async for msg in message.channel.history(limit=100):
            if msg.author == message.author or msg.author == bot.user:
                if time.time() - msg.created_at.timestamp() <= 30:
                    try:
                        await msg.delete()
                    except:
                        pass
        return

    # Eliminar mensajes que coinciden con el patrón de "the game"
    patrones = [
        r'\bthe\s?game\b',
        r'\bThe\s?Game\b',
        r'\bT\s?h\s?e\s?G\s?a\s?m\s?e\b',
    ]

    if any(
            re.search(patron, message.content, re.IGNORECASE)
            for patron in patrones):
        try:
            await message.delete()  # Eliminar el mensaje
        except:
            pass

        # Cargar las respuestas y filtrar las que están en cooldown
        respuestas = cargar_respuestas()
        respuestas_disponibles = [
            r for r in respuestas['respuestas']
            if r['id'] not in ultima_respuesta_usada or time.time() -
            ultima_respuesta_usada[r['id']] > COOLDOWN_TIEMPO
        ]

        if respuestas_disponibles:
            respuesta_random = random.choice(respuestas_disponibles)
            respuesta_id = respuesta_random['id']

            # Actualizar el tiempo de uso de la respuesta
            ultima_respuesta_usada[respuesta_id] = time.time()

            await message.channel.send('🌸 ' + respuesta_random['texto'])
        else:
            await message.channel.send(
                '🌸 Se acabaron las respuestas inteligentes por ahora... te salvaste... de momento... (￣︿￣)'
            )

    await bot.process_commands(message)


# Función auxiliar para obtener o crear la cola de un servidor
def get_guild_queue(guild_id):
    if guild_id not in queue:
        queue[guild_id] = []
    return queue[guild_id]


# Comando: #play
@bot.command(name="play")
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Debes estar en un canal de voz.")

    channel = ctx.author.voice.channel
    player: wavelink.Player = ctx.voice_client or await channel.connect(
        cls=wavelink.Player)

    # Lista para mantener las pistas encontradas
    tracks_to_play = []

    try:
        if "open.spotify.com/track" in search:
            track_id = search.split("/")[-1].split("?")[0]
            track = sp.track(track_id)
            search_term = f"{track['name']} {track['artists'][0]['name']}"
            tracks_to_play.append(search_term)

        elif "open.spotify.com/album" in search:
            album_id = search.split("/")[-1].split("?")[0]
            album = sp.album_tracks(album_id)
            for item in album["items"]:
                track_name = f"{item['name']} {item['artists'][0]['name']}"
                tracks_to_play.append(track_name)

        elif "open.spotify.com/playlist" in search:
            playlist_id = search.split("/")[-1].split("?")[0]
            results = sp.playlist_tracks(playlist_id)
            for item in results["items"]:
                track = item["track"]
                track_name = f"{track['name']} {track['artists'][0]['name']}"
                tracks_to_play.append(track_name)

        else:
            # Búsqueda manual de texto
            tracks_to_play.append(search)

    except Exception:
        return await ctx.send(
            "❌ Hubo un error al obtener las canciones de Spotify. que basura de plataforma")

    if not tracks_to_play:
        return await ctx.send("❌ No se encontraron pistas.")

    # Reproducir o añadir a la cola
    for i, term in enumerate(tracks_to_play):
        tracks = await wavelink.Playable.search(term)
        if not tracks:
            await ctx.send(f"⚠️ No se encontró: `{term}`")
            continue

        track = tracks[0]

        if not player.playing and i == 0:
            await player.play(track)
            await ctx.send(f"▶️ Reproduciendo: **{track.title}**")
        else:
            await player.queue.put_wait(track)
            await ctx.send(f"➕ Añadido a la cola: **{track.title}**")


@bot.command()
async def skip(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player or not player.connected:
        return await ctx.send("❌ No estoy conectado a un canal de voz.")
    if not player.playing:
        return await ctx.send("⏸️ No hay nada reproduciéndose.")

    try:
        await player.skip()
        await ctx.send("⏭️ Saltando canción...")
    except Exception as e:
        print(f"❌ Error al saltar canción: {e}")
        await ctx.send("❌ Hubo un problema al intentar saltar la canción. Soy una Loser °n°)/")


# Evento al terminar una canción
@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    player = payload.player
    if not player or not player.is_connected:
        return

    # 🔒 Verificación segura
    if hasattr(player, "queue") and player.queue and not player.queue.is_empty:
        next_track = player.queue.get()
        await player.play(next_track)



# Comando: #cola
@bot.command()
async def cola(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player or player.queue.is_empty:
        return await ctx.send("📭 La cola está vacía.")

    queue_list = list(player.queue)
    mensaje = "\n".join(f"{idx+1}. {track.title}"
                        for idx, track in enumerate(queue_list))
    await ctx.send(f"🎶 **Cola actual:**\n{mensaje}")


# Comando: #join
@bot.command(name="join")
async def join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send(
            "❌ Debes estar en un canal de voz para usar este comando.")

    channel = ctx.author.voice.channel
    await channel.connect(cls=wavelink.Player)
    await ctx.send(f"✅ Me uní al canal de voz: **{channel.name}**")


# Comando: #leave
@bot.command(name="leave")
async def leave(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        return await ctx.send("❌ No estoy conectado a ningún canal de voz.")

    await player.disconnect()
    await ctx.send("👋 Bueno... se bien cuando no soy deseada ( ｡ •` ⤙´• ｡)")


# Comando: #letra
@bot.command(name="letra")
async def lyrics(ctx):
    player: wavelink.Player = ctx.voice_client

    if not player or not player.current:
        return await ctx.send("❌ No hay ninguna canción reproduciéndose.")

    import re

    full_title = player.current.title

    parts = full_title.split(" - ")
    if len(parts) >= 2:
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        artist = "Unknown Artist"
        title = full_title.strip()
        return await ctx.send(
            f"❌Tuve problemas para obtener la puta letra culia de tu tema... perdon :c"
        )

    title = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()

    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"https://api.lyrics.ovh/v1/{artist}/{title}") as resp:
            if resp.status != 200:
                return await ctx.send(
                    f"❌ No encontré la letra de: **{artist} - {title}**")
            data = await resp.json()
            raw_lyrics = data.get("lyrics",
                                  "❌ No se encontraron letras disponibles.")

            # 🔍 Eliminar líneas vacías o con solo espacios
            cleaned_lyrics = "\n".join(line
                                       for line in raw_lyrics.splitlines()
                                       if line.strip())

            if len(cleaned_lyrics) > 2000:
                return await ctx.send(
                    f"📜 La letra de **{title}** es muy larga para mostrar.")
            await ctx.send(
                f"📜 Letra de **{artist} - {title}**:\n\n{cleaned_lyrics}")


# DEPURACION O CODIGO TEMPORAL
@bot.command(name="debug_player")
async def debug_player(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        return await ctx.send("❌ Player no existe.")
    if not player.current:
        return await ctx.send("⛔ Player activo, pero no hay canción actual.")
    await ctx.send(f"✅ Player activo y reproduciendo: {player.current.title}")


# COMANDO DATO RANDOM
@bot.command(name='datorandom')
@commands.cooldown(1, 45, commands.BucketType.user)
async def datorandom(ctx):
    global datos_mostrados_recientemente

    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            datos = data['datos']

        if datos:
            # Filter out recently shown data
            datos_no_recientes = [
                d for d in datos
                if d['id'] not in datos_mostrados_recientemente
            ]

            if not datos_no_recientes:
                # Reset recently shown data if all are shown
                datos_mostrados_recientemente.clear()
                datos_no_recientes = datos

            dato_random = random.choice(datos_no_recientes)
            dato_id = dato_random['id']
            dato_texto = dato_random['texto']

            # Add the data to the recently shown list with current time
            datos_mostrados_recientemente[dato_id] = time.time()

            datorandom_message = await ctx.send(
                f"🌸 Dato Random: {dato_texto} 🌸")

            # Clean up data shown more than an hour ago
            datos_mostrados_recientemente = {
                id: timestamp
                for id, timestamp in datos_mostrados_recientemente.items()
                if time.time() - timestamp < 86400
            }
        else:
            datorandom_message = await ctx.send(
                "Se acabaron todos los datos randoms... como es eso posible... son unos animales asquerosos (｡•ˇ‸ˇ•｡)"
            )
    except Exception as e:
        datorandom_message = await ctx.send(f'Ocurrió un error: {str(e)}')
        print(f'Error al obtener el dato random... perdonenme (｡>﹏<)')

    # Delete the message after 1 minute
    await asyncio.sleep(180)
    await datorandom_message.delete()


    # Error handler for datorandom cooldown
@datorandom.error
async def datorandom_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"🌸 Espera un poco, un poquito maaaas!!!... Puedes usar el comando en {error.retry_after:.0f} segundos. No seas ansioso(a) (｡•ˇ‸ˇ•｡)"
        )


# COMANDO SAY - Solo para un usuario específico
@bot.command(name='say')
async def say(ctx, *, message: str):

    AUTHORIZED_USER_ID = 447296273632985088
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("🌸 y quien soy vo 🌸")
        return

    await ctx.message.delete()
    sent_message = await ctx.send(message)
    await asyncio.sleep(999999999)
    await sent_message.delete()


# Checkear constante estado
async def monitorear_lavalink():
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            if not wavelink.Pool.nodes:
                print("⚠️ No hay nodos en la Pool. Intentando reconectar...")
                await connect_wavelink()
            else:
                node = list(wavelink.Pool.nodes.values())[0]

                if node.status != wavelink.NodeStatus.CONNECTED:
                    print(
                        "⚠️ Nodo no está conectado. Intentando reconectar...")
                    await connect_wavelink()

                    for guild in bot.guilds:
                        vc = guild.voice_client
                        if vc and not vc.is_connected():
                            try:
                                await vc.channel.connect(cls=wavelink.Player,
                                                         reconnect=True)
                                print(
                                    f"🔄 Reconectado al canal de voz en {guild.name}"
                                )
                            except Exception as e:
                                print(
                                    f"❌ Error al reconectarse en {guild.name}: {e}"
                                )

        except Exception as e:
            print(f"❌ Error monitoreando Lavalink: {e}")

        await asyncio.sleep(5)


# TESTEAR MANUALMENTE EL ESTADO
@bot.command(name="testlavalink")
async def test_lavalink(ctx):
    await ctx.send("🔍 Probando conexión con Lavalink...")

    try:
        # Verificar si ya hay nodos
        if not wavelink.Pool.nodes:
            await ctx.send(
                "⚠️ No hay nodos registrados. Intentando conectar...")
        else:
            await ctx.send(
                "🔄 Nodo existente detectado. Reiniciando conexión...")

        # Intentar reconectar
        await connect_wavelink()
        await asyncio.sleep(2)  # Esperar un poco a que se establezca

        # Revisar el estado del nodo
        node = list(wavelink.Pool.nodes.values())[0]
        if node.status == wavelink.NodeStatus.CONNECTED:
            await ctx.send("✅ Conexión a Lavalink restablecida correctamente.")
        else:
            await ctx.send(
                "❌ El nodo aún no está conectado. Revisa el estado del servidor Lavalink."
            )

    except Exception as e:
        print(f"❌ Error al testear conexión con Lavalink: {e}")
        await ctx.send(f"❌ Falló la prueba de conexión. Error: `{str(e)}`")


# Mantener el bot activo con Flask
app = Flask('')

@app.route('/')
def home():
    print("✅ Ping recibido: Sthashior siempre viva nunca inviva")
    return "¡¡¡Sthashior esta vivita y coleando!!!"

def run():
    app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

# funcion connect-lavalink
async def connect_wavelink():
    try:
        nodes = [
            wavelink.Node(
                uri="http://lavalink.jirayu.net:13592",
                password="youshallnotpass"
            )
        ]
        await wavelink.Pool.connect(nodes=nodes, client=bot)
        print("✅ Wavelink conectado exitosamente")
    except Exception as e:
        print(f"❌ Error conectando a Wavelink: {e}")

# ON_READY
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    await connect_wavelink()
    bot.loop.create_task(monitorear_lavalink())

# Ejecutar el bot
bot.run(TOKEN)
