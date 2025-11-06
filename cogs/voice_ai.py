import os
import discord
from discord.ext import commands
import asyncio
from gtts import gTTS
import tempfile
from pathlib import Path
import aiohttp
from typing import Dict, List


class VoiceAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.temp_dir = Path(tempfile.gettempdir()) / "sthashior_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Configuración de IA (igual que ai_chat.py)
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"
        
        # Historial de conversación por voz (por usuario)
        self.voice_conversation_history: Dict[int, List[str]] = {}
        self.max_history = 2  # Solo 2 mensajes de historial para respuestas rápidas
        
        # Cargar personalidad desde archivo
        self.personality = self._load_personality()

    def _load_personality(self) -> str:
        """Carga la personalidad desde el archivo de configuración"""
        try:
            personality_path = os.path.join(os.path.dirname(__file__), "..", "data", "ai_personality.txt")
            with open(personality_path, "r", encoding="utf-8") as f:
                base_personality = f.read().strip()
            
            # Añadir instrucciones específicas para voz
            voice_instructions = """

INSTRUCCIONES ESPECIALES PARA VOZ:
- Responde en MÁXIMO 2-3 oraciones (para que no dure más de 10 segundos)
- Sé directa y concisa
- No uses emoticones (se escucharán raros en voz)
- Responde preguntas tontas con humor
- Mantén el tono casual y amigable"""
            
            return base_personality + voice_instructions
        except Exception as e:
            print(f"[WARNING] No se pudo cargar ai_personality.txt: {e}")
            return "Eres Sthashior, un asistente amigable. Responde de manera muy breve y natural, máximo 2-3 oraciones."

    async def _query_groq_voice(self, text: str, user_id: int) -> str:
        """Consulta la API de Groq para obtener respuesta de IA (versión voz)"""
        if not self.groq_api_key:
            return "No tengo configurada mi clave de IA."
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        # Construir mensajes con personalidad
        messages = [
            {"role": "system", "content": self.personality}
        ]
        
        # Añadir historial si existe (solo últimos 2 mensajes)
        history = self.voice_conversation_history.get(user_id, [])
        for i in range(0, len(history), 2):
            if i < len(history):
                messages.append({"role": "user", "content": history[i]})
            if i + 1 < len(history):
                messages.append({"role": "assistant", "content": history[i+1]})
        
        # Añadir mensaje actual
        messages.append({"role": "user", "content": text})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 80,  # Límite bajo para respuestas cortas
            "top_p": 0.9
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return "Lo siento, tuve un problema al pensar en una respuesta."
                    
                    result = await response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        response_text = result["choices"][0]["message"]["content"].strip()
                        
                        # Actualizar historial
                        if user_id not in self.voice_conversation_history:
                            self.voice_conversation_history[user_id] = []
                        
                        self.voice_conversation_history[user_id].append(text)
                        self.voice_conversation_history[user_id].append(response_text)
                        
                        # Mantener solo últimos mensajes
                        if len(self.voice_conversation_history[user_id]) > self.max_history * 2:
                            self.voice_conversation_history[user_id] = self.voice_conversation_history[user_id][-(self.max_history * 2):]
                        
                        return response_text
                    
                    return "No se me ocurre qué decir."
        except Exception as e:
            print(f"[ERROR] Groq Voice: {e}")
            return "Tuve un error al procesar tu mensaje."

    @commands.command(name="voz")
    async def voice_tts(self, ctx: commands.Context, *, mensaje: str = None):
        """[EN DESARROLLO] Habla con la IA por voz"""
        # Mensaje de desarrollo suspendido
        embed = discord.Embed(
            title="🚧 Función en Desarrollo",
            description=(
                "Lo siento mucho~ (｡•́︿•̀｡)\n\n"
                "El comando de **voz con IA** está temporalmente suspendido debido a limitaciones técnicas de la plataforma de hosting actual.\n\n"
                "**Problemas encontrados:**\n"
                "• Replit no soporta conexiones UDP necesarias para voz\n"
                "• Conflictos con librerías de audio (FFmpeg/libopus)\n"
                "• Incompatibilidad con el sistema de voz de Discord\n\n"
                "**Alternativas disponibles:**\n"
                "🤖 `#ia <mensaje>` - Chatea conmigo por texto\n"
                "🎵 `#play <canción>` - Reproduce música (funciona perfectamente)\n\n"
                "**Estado:** En espera de migración a un hosting compatible (Railway/Render)\n\n"
                "¡Gracias por tu comprensión! 🌸"
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="Desarrollado por PurpleQuasar")
        await ctx.send(embed=embed)

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
        """[EN DESARROLLO] Detiene la reproducción de voz"""
        await ctx.send("ℹ️ El comando `#voz` está temporalmente desactivado. Usa `#voz` para más información.")

    @commands.command(name="voz_reset")
    async def voice_reset(self, ctx: commands.Context):
        """[EN DESARROLLO] Reinicia el historial de conversación por voz"""
        await ctx.send("ℹ️ El comando `#voz` está temporalmente desactivado. Usa `#voz` para más información.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceAI(bot))
