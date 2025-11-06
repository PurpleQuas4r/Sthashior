import os
import discord
from discord.ext import commands
import asyncio
from gtts import gTTS
import tempfile
from pathlib import Path


class VoiceAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.temp_dir = Path(tempfile.gettempdir()) / "sthashior_tts"
        self.temp_dir.mkdir(exist_ok=True)

    @commands.command(name="voz")
    async def voice_tts(self, ctx: commands.Context, *, mensaje: str = None):
        """Reproduce un mensaje en el canal de voz usando TTS"""
        # Verificar que esté en el servidor correcto
        if ctx.guild is None or ctx.guild.id != self.allowed_guild_id:
            return
        
        if not mensaje:
            await ctx.send("❌ Debes escribir un mensaje. Uso: `#voz <mensaje>`")
            return
        
        # Verificar que el usuario esté en un canal de voz
        if not ctx.author.voice:
            await ctx.send("❌ Debes estar en un canal de voz para usar este comando.")
            return
        
        # Obtener el canal de voz del usuario
        voice_channel = ctx.author.voice.channel
        
        try:
            # Conectar al canal de voz si no está conectado
            voice_client = ctx.guild.voice_client
            if voice_client is None:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
            
            # Verificar si ya está reproduciendo algo
            if voice_client.is_playing():
                await ctx.send("⏳ Espera a que termine el mensaje anterior...")
                return
            
            await ctx.send(f"🎤 Reproduciendo mensaje en voz...")
            
            # Generar audio TTS
            audio_file = await self._generate_tts(mensaje)
            
            # Reproducir el audio
            voice_client.play(
                discord.FFmpegPCMAudio(str(audio_file)),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self._cleanup_audio(audio_file, voice_client, ctx),
                    self.bot.loop
                )
            )
            
        except discord.ClientException as e:
            await ctx.send(f"❌ Error al conectar al canal de voz: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Error al generar voz: {str(e)}")
            print(f"[ERROR] Voice TTS: {e}")

    async def _generate_tts(self, text: str) -> Path:
        """Genera un archivo de audio TTS usando Google TTS"""
        # Crear archivo temporal
        audio_file = self.temp_dir / f"tts_{hash(text)}.mp3"
        
        # Generar TTS en español
        tts = gTTS(text=text, lang='es', slow=False)
        tts.save(str(audio_file))
        
        return audio_file

    async def _cleanup_audio(self, audio_file: Path, voice_client, ctx):
        """Limpia el archivo de audio y desconecta del canal"""
        await asyncio.sleep(1)
        
        # Eliminar archivo temporal
        try:
            if audio_file.exists():
                audio_file.unlink()
        except Exception as e:
            print(f"[WARNING] No se pudo eliminar {audio_file}: {e}")
        
        # Desconectar después de 3 segundos de inactividad
        await asyncio.sleep(3)
        if voice_client and not voice_client.is_playing():
            await voice_client.disconnect()

    @commands.command(name="voz_stop")
    async def voice_stop(self, ctx: commands.Context):
        """Detiene la reproducción de voz y desconecta el bot"""
        if ctx.guild is None or ctx.guild.id != self.allowed_guild_id:
            return
        
        voice_client = ctx.guild.voice_client
        if voice_client:
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            await ctx.send("🔇 Desconectado del canal de voz.")
        else:
            await ctx.send("ℹ️ No estoy conectado a ningún canal de voz.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceAI(bot))
