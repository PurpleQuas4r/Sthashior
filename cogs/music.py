import os
import random
import asyncio
import discord
from discord.ext import commands
import wavelink
import aiohttp
import urllib.parse
import re
import unicodedata

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except Exception:
    spotipy = None


def _lavalink_config() -> tuple[str, str]:
    host = os.environ.get("LAVALINK_HOST", "lava-v4.ajieblogs.eu.org")
    port = os.environ.get("LAVALINK_PORT", "80")
    secure = os.environ.get("LAVALINK_SECURE", "false").lower() == "true"
    scheme = "https" if secure else "http"
    uri = f"{scheme}://{host}:{port}"
    password = os.environ.get("LAVALINK_PASSWORD", "https://dsc.gg/ajidevserver")
    return uri, password


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop_mode: dict[int, str] = {}
        self.spotify = None
        self.stop_guard = set()
        self.empty_channel_tasks: dict[int, asyncio.Task] = {}  # Tareas de desconexión por inactividad
        cid = os.environ.get("SPOTIFY_CLIENT_ID")
        secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        if spotipy and cid and secret:
            self.spotify = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=secret)
            )

    def _to_tracks(self, obj) -> list[wavelink.Playable]:
        try:
            if obj is None:
                return []
            if isinstance(obj, list):
                return obj
            tracks = getattr(obj, "tracks", None)
            if tracks is not None:
                return list(tracks)
            # Soporta objetos Track individuales
            if hasattr(obj, "title") and hasattr(obj, "uri"):
                return [obj]
            return list(obj)
        except Exception:
            return []

    @commands.Cog.listener()
    async def on_ready(self):
        # Conecta a Lavalink si no hay nodos conectados
        need_connect = True
        try:
            nodes_map = getattr(wavelink.Pool, "nodes", {})
            if nodes_map:
                # Si todos los nodos no están conectados, necesitamos conectar
                need_connect = all(getattr(n, "status", None) != wavelink.NodeStatus.CONNECTED for n in nodes_map.values())
            else:
                need_connect = True
        except Exception:
            need_connect = True

        if need_connect:
            uri, password = _lavalink_config()
            nodes = [wavelink.Node(uri=uri, password=password)]
            await wavelink.Pool.connect(nodes=nodes, client=self.bot)

    def _duration(self, ms: int) -> str:
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

    def _embed(self, title: str, description: str | None = None, color: discord.Color | None = None) -> discord.Embed:
        emb = discord.Embed(title=title, description=description or discord.Embed.Empty, color=color or discord.Color.blurple())
        return emb

    def _cancel_empty_task(self, guild_id: int):
        """Cancela la tarea de desconexión automática si existe"""
        if guild_id in self.empty_channel_tasks:
            self.empty_channel_tasks[guild_id].cancel()
            del self.empty_channel_tasks[guild_id]

    async def _auto_disconnect_if_empty(self, player: wavelink.Player, guild_id: int):
        """Desconecta el bot después de 5 minutos si el canal está vacío"""
        try:
            await asyncio.sleep(300)  # 5 minutos = 300 segundos
            # Verificar si el canal sigue vacío
            if player.channel and len([m for m in player.channel.members if not m.bot]) == 0:
                if player.queue and not player.queue.is_empty:
                    player.queue.clear()
                await player.stop()
                await player.disconnect()
                print(f"Bot desconectado automáticamente del servidor {guild_id} por inactividad")
        except asyncio.CancelledError:
            # La tarea fue cancelada porque alguien se unió al canal
            pass
        finally:
            if guild_id in self.empty_channel_tasks:
                del self.empty_channel_tasks[guild_id]

    def _check_empty_channel(self, player: wavelink.Player):
        """Verifica si el canal está vacío y programa desconexión automática"""
        if not player or not player.channel:
            return
        
        guild_id = player.guild.id
        # Contar miembros que no sean bots
        human_members = [m for m in player.channel.members if not m.bot]
        
        if len(human_members) == 0:
            # Canal vacío, programar desconexión si no existe ya
            if guild_id not in self.empty_channel_tasks:
                task = asyncio.create_task(self._auto_disconnect_if_empty(player, guild_id))
                self.empty_channel_tasks[guild_id] = task
        else:
            # Hay gente en el canal, cancelar desconexión automática
            self._cancel_empty_task(guild_id)

    async def _ensure_player_ctx(self, ctx: commands.Context, join: bool = False) -> wavelink.Player | None:
        guild = ctx.guild
        if not guild:
            return None
        player: wavelink.Player = guild.voice_client  # type: ignore
        if player and isinstance(player, wavelink.Player):
            return player
        if join:
            author: discord.Member = ctx.author  # type: ignore
            if not author.voice or not author.voice.channel:
                await ctx.send("❌ Debes estar en un canal de voz.")
                return None
            channel = author.voice.channel
            player = await channel.connect(cls=wavelink.Player)  # type: ignore
            return player
        return None

    async def _search_tracks(self, query: str) -> list[wavelink.Playable]:
        q = query.strip()
        # Si es URL, normalizamos dominios de YouTube Music y limpiamos 'list=LM'
        if q.startswith("http"):
            try:
                parsed = urllib.parse.urlparse(q)
                netloc = parsed.netloc.lower()
                if netloc in {"music.youtube.com", "m.youtube.com"}:
                    netloc = "www.youtube.com"
                # Opcional: eliminar lista LM para evitar carga fallida
                qs = urllib.parse.parse_qs(parsed.query)
                if "list" in qs and qs.get("list", [""])[0].upper() == "LM":
                    qs.pop("list", None)
                new_query = urllib.parse.urlencode({k: v[0] for k, v in qs.items()}) if qs else ""
                parsed = parsed._replace(netloc=netloc, query=new_query)
                q_norm = urllib.parse.urlunparse(parsed)
            except Exception:
                q_norm = q

            # 1) Intento con Playable.search
            results = await wavelink.Playable.search(q_norm)
            tracks = self._to_tracks(results)
            if tracks:
                return tracks
            # 2) Fallback con Pool.fetch_tracks (acepta URLs directamente)
            try:
                fetched = await wavelink.Pool.fetch_tracks(q_norm)
                tracks = self._to_tracks(fetched)
                if tracks:
                    return tracks
            except Exception:
                pass
            # Fallback: si aún no hay resultados y era URL de YouTube con watch, intenta sin parámetros extra
            try:
                parsed = urllib.parse.urlparse(q_norm)
                if parsed.path == "/watch":
                    qs = urllib.parse.parse_qs(parsed.query)
                    v = qs.get("v", [None])[0]
                    if v:
                        simple = f"https://www.youtube.com/watch?v={v}"
                        res2 = await wavelink.Playable.search(simple)
                        t2 = self._to_tracks(res2)
                        if t2:
                            return t2
                        # Como último recurso, usa ytsearch con el ID
                        res3 = await wavelink.Playable.search(f"ytsearch:{v}")
                        t3 = self._to_tracks(res3)
                        if t3:
                            return t3
                        # Extra: intenta obtener el título vía oEmbed y buscar por nombre
                        try:
                            async with aiohttp.ClientSession() as session:
                                oembed = f"https://www.youtube.com/oembed?url={urllib.parse.quote(simple)}&format=json"
                                async with session.get(oembed) as r:
                                    if r.status == 200:
                                        data = await r.json()
                                        title = data.get("title")
                                        if title:
                                            for prov in ("ytmsearch", "ytsearch", "scsearch"):
                                                res4 = await wavelink.Playable.search(f"{prov}:{title}")
                                                if res4:
                                                    return list(res4)
                        except Exception:
                            pass
            except Exception:
                pass
            return []
        # No es URL: prueba varios proveedores en orden
        for prov in ("ytmsearch", "ytsearch", "scsearch"):
            results = await wavelink.Playable.search(f"{prov}:{q}")
            tracks = self._to_tracks(results)
            if tracks:
                return tracks
        try:
            fetched = await wavelink.Pool.fetch_tracks(f"ytsearch:{q}")
            tracks = self._to_tracks(fetched)
            if tracks:
                return tracks
        except Exception:
            pass
        return []

    async def _from_spotify(self, query: str) -> list[str]:
        MAX_SPOTIFY_TRACKS = 20
        if not self.spotify:
            return [query]
        if "open.spotify.com/track" in query:
            tid = query.split("/")[-1].split("?")[0]
            tr = self.spotify.track(tid)
            return [f"{tr['name']} {tr['artists'][0]['name']}"]
        if "open.spotify.com/album" in query:
            aid = query.split("/")[-1].split("?")[0]
            items = self.spotify.album_tracks(aid)["items"]
            # Limitar a MAX_SPOTIFY_TRACKS
            items = items[:MAX_SPOTIFY_TRACKS]
            return [f"{it['name']} {it['artists'][0]['name']}" for it in items]
        if "open.spotify.com/playlist" in query:
            pid = query.split("/")[-1].split("?")[0]
            items = self.spotify.playlist_tracks(pid)["items"]
            out = []
            for it in items[:MAX_SPOTIFY_TRACKS]:  # Limitar a MAX_SPOTIFY_TRACKS
                tr = it.get("track")
                if tr:
                    out.append(f"{tr['name']} {tr['artists'][0]['name']}")
            return out
        return [query]

    @commands.command(name="join")
    async def join(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx, join=True)
        if player:
            # Cancelar desconexión automática al unirse
            self._cancel_empty_task(ctx.guild.id)
            await ctx.send(f"✅ Conectado a {player.channel.name}")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal.")
            return
        # Cancelar tarea de desconexión automática
        self._cancel_empty_task(ctx.guild.id)
        if player.queue and not player.queue.is_empty:
            player.queue.clear()
        await player.stop()
        await player.disconnect()
        await ctx.send("👋 Desconectado y cola limpiada.")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        player = await self._ensure_player_ctx(ctx, join=True)
        if not player:
            return
        
        # Límite de canciones por playlist
        MAX_PLAYLIST_TRACKS = 20
        
        queries: list[str]
        if query.startswith("http") and "open.spotify.com" in query:
            queries = await self._from_spotify(query)
        else:
            queries = [query]
        
        queued = 0
        first_title = None
        added_titles: list[str] = []
        is_playlist = False
        
        for i, q in enumerate(queries):
            tracks = await self._search_tracks(q)
            if not tracks:
                continue
            
            # Detectar si es una playlist (más de 1 track)
            if len(tracks) > 1:
                is_playlist = True
                # Limitar a MAX_PLAYLIST_TRACKS
                tracks = tracks[:MAX_PLAYLIST_TRACKS]
            
            # Procesar todas las tracks encontradas
            for track_idx, track in enumerate(tracks):
                # La primera canción se reproduce directamente si no hay nada sonando
                if not player.playing and i == 0 and track_idx == 0:
                    await player.play(track)
                    first_title = track.title
                else:
                    await player.queue.put_wait(track)
                    queued += 1
                    if len(added_titles) < 3:  # Guardamos solo los primeros 3 títulos para mostrar
                        added_titles.append(track.title)
        
        # Cancelar desconexión automática al reproducir música
        if ctx.guild:
            self._cancel_empty_task(ctx.guild.id)
        
        # Mensajes de respuesta
        if first_title and queued == 0:
            emb = self._embed("Reproduciendo", f"▶️ **{first_title}**", discord.Color.green())
            await ctx.send(embed=emb)
        elif first_title and queued > 0:
            if is_playlist:
                emb = self._embed("Playlist añadida", f"▶️ **{first_title}**\n➕ Añadidas {queued} canciones más a la cola", discord.Color.green())
            else:
                emb = self._embed("Reproduciendo", f"▶️ **{first_title}**\n➕ Añadidas {queued} a la cola", discord.Color.green())
            await ctx.send(embed=emb)
        elif queued > 0:
            # Ya había reproducción activa; reportamos lo añadido
            if queued == 1:
                emb = self._embed("Añadido a la cola", f"➕ **{added_titles[0]}**", discord.Color.blurple())
                await ctx.send(embed=emb)
            else:
                shown = added_titles[0] if added_titles else "canciones"
                if is_playlist:
                    emb = self._embed("Playlist añadida a la cola", f"➕ {queued} canciones. Primera: **{shown}**", discord.Color.blurple())
                else:
                    emb = self._embed("Añadidas a la cola", f"➕ {queued} pistas. Primera: **{shown}**", discord.Color.blurple())
                await ctx.send(embed=emb)
        else:
            emb = self._embed("Sin resultados", "❌ No se encontraron resultados.", discord.Color.red())
            await ctx.send(embed=emb)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.playing:
            await ctx.send("⏸️ No hay nada sonando.")
            return
        await player.pause(True)
        await ctx.send("⏸️ Pausado.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal.")
            return
        await player.pause(False)
        await ctx.send("▶️ Reanudado.")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal.")
            return
        # Desactiva loop y coloca guard para ignorar el próximo track_end
        if ctx.guild:
            self.loop_mode[ctx.guild.id] = "off"
            self.stop_guard.add(ctx.guild.id)
        if player.queue and not player.queue.is_empty:
            player.queue.clear()
        await player.stop()
        await ctx.send("🛑 Detenido y cola limpiada.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.playing:
            await ctx.send("⏭️ No hay nada para saltar.")
            return
        await player.skip()
        await ctx.send("⏭️ Canción saltada.")

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.queue or player.queue.is_empty:
            emb = self._embed("Cola", "📭 La cola está vacía.", discord.Color.orange())
            await ctx.send(embed=emb)
            return
        items = list(player.queue)
        lines = [f"{i}. {t.title}" for i, t in enumerate(items, start=1)]
        txt = "\n".join(lines)
        if len(txt) > 1900:
            txt = txt[:1900] + "\n…"
        emb = self._embed("Cola", f"🎶 Lista:\n{txt}", discord.Color.teal())
        await ctx.send(embed=emb)

    @commands.command(name="nowplaying")
    async def nowplaying(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.current:
            emb = self._embed("Now Playing", "❌ No hay nada reproduciéndose.", discord.Color.red())
            await ctx.send(embed=emb)
            return
        t = player.current
        duration = self._duration(getattr(t, "length", 0))
        emb = self._embed("Now Playing", f"🎵 **{t.title}** — {duration}", discord.Color.green())
        await ctx.send(embed=emb)

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context, mode: str | None = None):
        if mode is None:
            # Toggle: off -> song, song/queue -> off
            current = self.loop_mode.get(ctx.guild.id if ctx.guild else 0, "off")
            mode = "song" if current == "off" else "off"
        mode = mode.lower()
        if mode not in {"song", "queue", "off"}:
            await ctx.send("Usa: song | queue | off")
            return
        if ctx.guild:
            self.loop_mode[ctx.guild.id] = mode
        await ctx.send(f"🔁 Loop: {mode}")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.queue or player.queue.is_empty:
            await ctx.send("📭 La cola está vacía.")
            return
        items = list(player.queue)
        random.shuffle(items)
        player.queue.clear()
        for t in items:
            await player.queue.put_wait(t)
        await ctx.send("🔀 Cola mezclada.")

    @commands.command(name="remove")
    async def remove(self, ctx: commands.Context, position: int):
        player = await self._ensure_player_ctx(ctx)
        if not player or not player.queue or player.queue.is_empty:
            await ctx.send("📭 La cola está vacía.")
            return
        items = list(player.queue)
        if position < 1 or position > len(items):
            await ctx.send("❌ Posición inválida.")
            return
        removed = items.pop(position - 1)
        player.queue.clear()
        for t in items:
            await player.queue.put_wait(t)
        await ctx.send(f"🗑️ Eliminado: **{removed.title}**")

    @commands.command(name="lyrics")
    async def lyrics(self, ctx: commands.Context, *, name: str | None = None):
        def _clean(s: str) -> str:
            s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        def _unaccent(s: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

        def _first_artist(s: str) -> str:
            # divide por conectores comunes y toma el primero
            parts = re.split(r"\s*(?:,| y | & | and | feat\.? | ft\.? | x )\s*", s, flags=re.IGNORECASE)
            return parts[0].strip()

        # Construir candidatos (artist,title)
        candidates: list[tuple[str, str]] = []
        if name:
            q = _clean(name)
            if " - " in q:
                a, t = q.split(" - ", 1)
                a, t = _clean(a), _clean(t)
                candidates.append((a, t))               # artista - titulo
                candidates.append((_first_artist(a), t)) # primer artista - titulo
                candidates.append((_first_artist(t), a)) # titulo - artista (reversa)
                candidates.append((t, a))               # reversa directa
            else:
                # sin separador, intenta con artista vacío y con título como q
                candidates.append(("", q))
                # Además prueba con el autor del track actual si existe
                player = await self._ensure_player_ctx(ctx)
                if player and player.current:
                    author_guess = _clean(getattr(player.current, "author", ""))
                    if author_guess:
                        candidates.append((author_guess, q))
                        candidates.append((_first_artist(author_guess), q))
        else:
            player = await self._ensure_player_ctx(ctx)
            if not player or not player.current:
                await ctx.send("❌ No hay nada reproduciéndose.")
                return
            t = player.current
            title_guess = _clean(getattr(t, "title", ""))
            author_guess = _clean(getattr(t, "author", ""))
            # Normaliza autores típicos de YouTube: "Artista - Topic", "ArtistVEVO"
            author_guess = re.sub(r"\s*-\s*topic$", "", author_guess, flags=re.IGNORECASE)
            author_guess = re.sub(r"vevo$", "", author_guess, flags=re.IGNORECASE)
            # Si el título contiene un patrón "Artista - Título", úsalo como principal
            if " - " in title_guess:
                a_part, t_part = title_guess.split(" - ", 1)
                a_part, t_part = _clean(a_part), _clean(t_part)
                # Lista de artistas dividida por conectores comunes
                artists = [x.strip() for x in re.split(r"\s*(?:,| y | & | and | feat\.? | ft\.? | x )\s*", a_part, flags=re.IGNORECASE) if x.strip()]
                if artists:
                    # candidato con artistas completos y título
                    candidates.append((a_part, t_part))
                    # candidatos por artista individual
                    for art in artists:
                        candidates.append((art, t_part))
                    # fallback solo título
                    candidates.append(("", t_part))
                else:
                    candidates.append((author_guess or a_part, t_part))
                    candidates.append(("", t_part))
            else:
                candidates.append((author_guess, title_guess))
                candidates.append(("", title_guess))

        # Intentos con y sin acentos
        async with aiohttp.ClientSession() as session:
            # Enriquecimiento: si no se entregó nombre y la pista es de YouTube, usa oEmbed para obtener el título completo
            try:
                if not name and 't' in locals():
                    uri = getattr(t, 'uri', '')
                    if isinstance(uri, str) and 'youtube.com' in uri:
                        # Normaliza a forma simple watch?v=ID
                        parsed = urllib.parse.urlparse(uri)
                        if parsed.path == '/watch':
                            qs = urllib.parse.parse_qs(parsed.query)
                            v = qs.get('v', [None])[0]
                            if v:
                                simple = f"https://www.youtube.com/watch?v={v}"
                                oembed = f"https://www.youtube.com/oembed?url={urllib.parse.quote(simple)}&format=json"
                                async with session.get(oembed) as r:
                                    if r.status == 200:
                                        data = await r.json()
                                        full_title = data.get('title', '')
                                        if ' - ' in full_title:
                                            a_part, t_part = full_title.split(' - ', 1)
                                            a_part = _clean(a_part)
                                            t_part = _clean(t_part)
                                            arts = [x.strip() for x in re.split(r"\s*(?:,| y | & | and | feat\.? | ft\.? | x )\s*", a_part, flags=re.IGNORECASE) if x.strip()]
                                            if arts:
                                                # añade candidatos de oEmbed al inicio para priorizarlos
                                                candidates.insert(0, (a_part, t_part))
                                                for art in arts:
                                                    candidates.insert(0, (art, t_part))
                                                candidates.insert(0, ("", t_part))
            except Exception:
                pass
            # 1) Intentos con lyrics.ovh
            for artist, title in candidates:
                for an, tn in [(artist, title), (_unaccent(artist), _unaccent(title))]:
                    a_enc = urllib.parse.quote(an)
                    t_enc = urllib.parse.quote(tn)
                    url = f"https://api.lyrics.ovh/v1/{a_enc}/{t_enc}" if an else f"https://api.lyrics.ovh/v1//{t_enc}"
                    try:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                text = data.get("lyrics") or "❌ No se encontraron letras."
                                text = "\n".join([ln for ln in text.splitlines() if ln.strip()])
                                if len(text) > 1900:
                                    text = text[:1900] + "\n…"
                                emb = self._embed(f"Letras de {tn}", text, discord.Color.purple())
                                await ctx.send(embed=emb)
                                return
                    except Exception:
                        pass

            # 2) Fallback con SomeRandomAPI por título (mejor para consultas sin artista)
            title_only = None
            if name:
                title_only = _clean(name)
            else:
                # si veníamos de pista actual
                title_only = candidates[0][1] if candidates else None

            if title_only:
                try:
                    # Intenta primero solo el título y luego título + artista principal
                    primary_artist = None
                    if candidates:
                        primary_artist = candidates[0][0] or None
                        if primary_artist:
                            primary_artist = _first_artist(primary_artist)

                    titles_to_try = [title_only]
                    if primary_artist and f"{title_only} {primary_artist}" not in titles_to_try:
                        titles_to_try.append(f"{title_only} {primary_artist}")
                    # Si el título original tenía múltiples artistas, intenta "título + todos los artistas"
                    try:
                        # Reconstruye posibles artistas desde candidates que tengan el mismo título
                        multi = [a for a, t in candidates if t.lower() == title_only.lower() and a]
                        # Mantén únicos, combinación corta "A B" si hay 2 primeros
                        if multi:
                            joined = " ".join(sorted({ _first_artist(a) for a in multi }))
                            if joined and f"{title_only} {joined}" not in titles_to_try:
                                titles_to_try.append(f"{title_only} {joined}")
                    except Exception:
                        pass

                    # Añade variantes sin acentos
                    more = []
                    for q in list(titles_to_try):
                        uq = _unaccent(q)
                        if uq != q:
                            more.append(uq)
                    titles_to_try.extend(more)

                    for qtitle in titles_to_try:
                        api_url = f"https://some-random-api.com/lyrics?title={urllib.parse.quote(qtitle)}"
                        async with session.get(api_url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                text = data.get("lyrics")
                                tn = data.get("title", qtitle)
                                if text:
                                    text = "\n".join([ln for ln in text.splitlines() if ln.strip()])
                                    if len(text) > 1900:
                                        text = text[:1900] + "\n…"
                                    emb = self._embed(f"Letras de {tn}", text, discord.Color.purple())
                                    await ctx.send(embed=emb)
                                    return
                except Exception:
                    pass

            # 3) Fallback con LRCLib (búsqueda por título y artista)
            try:
                for artist, title in candidates:
                    an, tn = _unaccent(artist), _unaccent(title)
                    q = f"https://lrclib.net/api/search?track_name={urllib.parse.quote(tn)}&artist_name={urllib.parse.quote(an)}&limit=1"
                    async with session.get(q) as resp:
                        if resp.status == 200:
                            arr = await resp.json()
                            if isinstance(arr, list) and arr:
                                item = arr[0]
                                text = item.get("plainLyrics") or item.get("syncedLyrics")
                                if text:
                                    text = "\n".join([ln for ln in text.splitlines() if ln.strip()])
                                    if len(text) > 1900:
                                        text = text[:1900] + "\n…"
                                    show_title = item.get("trackName", title)
                                    emb = self._embed(f"Letras de {show_title}", text, discord.Color.purple())
                                    await ctx.send(embed=emb)
                                    return
            except Exception:
                pass

        emb = self._embed("Letras", "❌ No encontré la letra.", discord.Color.red())
        await ctx.send(embed=emb)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player = payload.player
        if not player or not getattr(player, "connected", False):
            return
        gid = player.guild.id
        # Si venimos de un stop manual, ignorar este evento
        if gid in self.stop_guard:
            self.stop_guard.discard(gid)
            return
        mode = self.loop_mode.get(gid, "off")
        last = getattr(payload, "track", None)
        if mode == "song" and last:
            await player.play(last)
            return
        if mode == "queue" and last:
            await player.queue.put_wait(last)
        if hasattr(player, "queue") and player.queue and not player.queue.is_empty:
            nxt = player.queue.get()
            await player.play(nxt)
        else:
            # Si no hay más canciones, verificar si el canal está vacío
            self._check_empty_channel(player)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Detecta cuando alguien se une o sale de un canal de voz"""
        # Ignorar actualizaciones del propio bot
        if member.bot:
            return
        
        guild = member.guild
        player: wavelink.Player = guild.voice_client  # type: ignore
        
        if not player or not isinstance(player, wavelink.Player):
            return
        
        # Si alguien se unió al canal del bot
        if after.channel and after.channel.id == player.channel.id:
            # Cancelar desconexión automática
            self._cancel_empty_task(guild.id)
        
        # Si alguien salió del canal del bot
        elif before.channel and before.channel.id == player.channel.id:
            # Verificar si el canal quedó vacío
            self._check_empty_channel(player)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
