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
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
        # Historial de conversaciones por usuario (máximo 5 mensajes)
        self.conversation_history: Dict[int, List[str]] = {}
        self.max_history = 5
        
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.allowed_channel_id = 1266262036250103970

    async def _query_huggingface(self, text: str, user_id: int) -> str:
        """Consulta la API de Hugging Face con el modelo DialoGPT"""
        if not self.hf_token:
            return "❌ Token de Hugging Face no configurado."
        
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        # Obtener historial del usuario
        history = self.conversation_history.get(user_id, [])
        
        # Construir el contexto de conversación
        # DialoGPT funciona mejor con el historial completo
        conversation_text = " ".join(history + [text]) if history else text
        
        payload = {
            "inputs": conversation_text,
            "parameters": {
                "max_length": 100,
                "min_length": 10,
                "temperature": 0.9,
                "top_p": 0.9,
                "do_sample": True
            },
            "options": {
                "wait_for_model": True
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 503:
                        # Modelo cargándose
                        return "⏳ El modelo se está cargando, intenta de nuevo en unos segundos..."
                    
                    if response.status == 401:
                        return "❌ Token de Hugging Face inválido."
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return f"❌ Error al conectar con la IA: {response.status}"
                    
                    result = await response.json()
                    
                    # DialoGPT retorna una lista con el texto generado
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        
                        # Extraer solo la respuesta nueva (después del input)
                        if conversation_text in generated_text:
                            response_text = generated_text[len(conversation_text):].strip()
                        else:
                            response_text = generated_text.strip()
                        
                        # Actualizar historial
                        if user_id not in self.conversation_history:
                            self.conversation_history[user_id] = []
                        
                        self.conversation_history[user_id].append(text)
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
        """Chatea con la IA usando DialoGPT"""
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
