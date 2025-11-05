import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Dict, List


class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        # Cambiado a BlenderBot por deprecación de DialoGPT
        self.api_url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
        # Historial de conversaciones por usuario (máximo 3 mensajes para BlenderBot)
        self.conversation_history: Dict[int, List[str]] = {}
        self.max_history = 3
        
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.allowed_channel_id = 1266262036250103970

    async def _query_huggingface(self, text: str, user_id: int) -> str:
        """Consulta la API de Hugging Face con el modelo BlenderBot"""
        if not self.hf_token:
            return "❌ Token de Hugging Face no configurado."
        
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        # BlenderBot usa un formato más simple, solo el texto actual
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": 150,
                "min_length": 20,
                "temperature": 0.7,
                "top_p": 0.9,
                "repetition_penalty": 1.2
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                    if response.status == 503:
                        # Modelo cargándose
                        return "⏳ El modelo se está cargando, intenta de nuevo en unos segundos..."
                    
                    if response.status == 401:
                        return "❌ Token de Hugging Face inválido."
                    
                    if response.status == 410:
                        return "❌ El modelo no está disponible. Contacta al administrador."
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return f"❌ Error al conectar con la IA: {response.status}"
                    
                    result = await response.json()
                    
                    # BlenderBot retorna una lista con el texto generado
                    if isinstance(result, list) and len(result) > 0:
                        # BlenderBot puede retornar el texto directamente o en generated_text
                        if isinstance(result[0], dict):
                            response_text = result[0].get("generated_text", "").strip()
                        else:
                            response_text = str(result[0]).strip()
                        
                        # Actualizar historial
                        if user_id not in self.conversation_history:
                            self.conversation_history[user_id] = []
                        
                        self.conversation_history[user_id].append(text)
                        if response_text:
                            self.conversation_history[user_id].append(response_text)
                        
                        # Mantener solo los últimos mensajes
                        if len(self.conversation_history[user_id]) > self.max_history * 2:
                            self.conversation_history[user_id] = self.conversation_history[user_id][-(self.max_history * 2):]
                        
                        return response_text if response_text else "🤔 No tengo una respuesta para eso..."
                    
                    return "❌ No pude generar una respuesta."
        
        except asyncio.TimeoutError:
            return "⏱️ La IA tardó demasiado en responder. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @commands.command(name="ia")
    async def ia_chat(self, ctx: commands.Context, *, texto: str = None):
        """Chatea con la IA usando BlenderBot"""
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
            response = await self._query_huggingface(texto, ctx.author.id)
        
        # Enviar respuesta
        embed = discord.Embed(
            title="🤖 Sthashior IA",
            description=response,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Conversación con {ctx.author.display_name}")
        await ctx.send(embed=embed)

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
