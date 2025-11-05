import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Dict, List


class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cambiando a Groq - API gratuita con modelos rápidos
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Modelo rápido y gratuito
        # Historial de conversaciones por usuario (máximo 3 mensajes)
        self.conversation_history: Dict[int, List[str]] = {}
        self.max_history = 3
        
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.allowed_channel_id = 1266262036250103970
        
        # Cargar personalidad desde archivo
        self.personality = self._load_personality()

    def _load_personality(self) -> str:
        """Carga la personalidad desde el archivo de configuración"""
        try:
            personality_path = os.path.join(os.path.dirname(__file__), "..", "data", "ai_personality.txt")
            with open(personality_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"[WARNING] No se pudo cargar ai_personality.txt: {e}")
            # Personalidad por defecto si falla
            return "Eres Sthashior, un asistente amigable y conversacional. Responde de manera breve y natural."

    async def _query_groq(self, text: str, user_id: int) -> str:
        """Consulta la API de Groq con Llama 3.1"""
        if not self.groq_api_key:
            return "❌ API Key de Groq no configurada. Obtén una gratis en: https://console.groq.com"
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        # Usar personalidad cargada desde archivo
        messages = [
            {"role": "system", "content": self.personality}
        ]
        
        # Añadir historial si existe
        history = self.conversation_history.get(user_id, [])
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
            "max_tokens": 150,
            "top_p": 0.9
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"[DEBUG] URL: {self.api_url}")
                print(f"[DEBUG] Payload: {payload}")
                async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                    # Logs de depuración
                    print(f"[DEBUG] Status Code: {response.status}")
                    print(f"[DEBUG] Headers: {dict(response.headers)}")
                    
                    if response.status == 401:
                        error_detail = await response.text()
                        print(f"[DEBUG] 401 Error: {error_detail}")
                        return "❌ API Key de Groq inválida. Verifica tu clave en https://console.groq.com"
                    
                    if response.status == 429:
                        error_detail = await response.text()
                        print(f"[DEBUG] 429 Error: {error_detail}")
                        return "⏳ Límite de rate alcanzado. Espera un momento e intenta de nuevo."
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[DEBUG] Error {response.status}: {error_text}")
                        return f"❌ Error {response.status}: {error_text[:150]}"
                    
                    result = await response.json()
                    print(f"[DEBUG] Response JSON: {result}")
                    
                    # Groq usa formato OpenAI
                    if "choices" in result and len(result["choices"]) > 0:
                        response_text = result["choices"][0]["message"]["content"].strip()
                        
                        if response_text:
                            # Actualizar historial
                            if user_id not in self.conversation_history:
                                self.conversation_history[user_id] = []
                            
                            self.conversation_history[user_id].append(text)
                            self.conversation_history[user_id].append(response_text)
                            
                            # Mantener solo los últimos mensajes
                            if len(self.conversation_history[user_id]) > self.max_history * 2:
                                self.conversation_history[user_id] = self.conversation_history[user_id][-(self.max_history * 2):]
                            
                            return response_text
                    
                    return "🤔 No pude generar una respuesta..."
        
        except asyncio.TimeoutError:
            return "⏱️ La IA tardó demasiado en responder. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @commands.command(name="ia")
    async def ia_chat(self, ctx: commands.Context, *, texto: str = None):
        """Chatea con la IA usando Groq (Llama 3.1)"""
        # Verificar que esté en el servidor y canal correcto
        if ctx.guild is None or ctx.guild.id != self.allowed_guild_id:
            return
        
        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send("❌ Este comando solo funciona en el canal designado.")
            return
        
        if not texto:
            await ctx.send("❌ Debes escribir algo. Uso: `#ia <tu mensaje>`")
            return
        
        # Mostrar indicador de escritura
        async with ctx.typing():
            response = await self._query_groq(texto, ctx.author.id)
        
        # Enviar respuesta sin embed
        await ctx.send(f"{response}\n-# Conversación con {ctx.author.display_name}")

    @commands.command(name="ia_reset")
    async def ia_reset(self, ctx: commands.Context):
        """Reinicia el historial de conversación con la IA"""
        if ctx.guild is None or ctx.guild.id != self.allowed_guild_id:
            return
        
        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send("❌ Este comando solo funciona en el canal designado.")
            return
        
        if ctx.author.id in self.conversation_history:
            del self.conversation_history[ctx.author.id]
            await ctx.send("✅ Historial de conversación reiniciado.")
        else:
            await ctx.send("ℹ️ No tienes historial de conversación.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
