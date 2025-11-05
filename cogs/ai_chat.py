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
        # Usando IBM Granite - modelo pequeño y reciente (actualizado oct 2024)
        # NUEVA URL de Hugging Face (la antigua fue deprecada)
        self.api_url = "https://router.huggingface.co/hf-inference/models/ibm-granite/granite-4.0-h-350m"
        # Historial de conversaciones por usuario (máximo 3 mensajes)
        self.conversation_history: Dict[int, List[str]] = {}
        self.max_history = 3
        
        # IDs específicos donde funciona el comando
        self.allowed_guild_id = 391755494978617344
        self.allowed_channel_id = 1266262036250103970

    async def _query_huggingface(self, text: str, user_id: int) -> str:
        """Consulta la API de Hugging Face con el modelo IBM Granite"""
        if not self.hf_token:
            return "❌ Token de Hugging Face no configurado."
        
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        # TinyLlama usa formato simple
        prompt = f"Responde de manera amigable y breve: {text}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.8,
                "top_p": 0.9,
                "do_sample": True
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                    # Logs de depuración
                    print(f"[DEBUG] Status Code: {response.status}")
                    print(f"[DEBUG] Headers: {dict(response.headers)}")
                    
                    if response.status == 503:
                        error_detail = await response.text()
                        print(f"[DEBUG] 503 Error: {error_detail}")
                        return "⏳ El modelo se está cargando, intenta de nuevo en unos segundos..."
                    
                    if response.status == 401:
                        error_detail = await response.text()
                        print(f"[DEBUG] 401 Error: {error_detail}")
                        return "❌ Token de Hugging Face inválido."
                    
                    if response.status == 410:
                        error_detail = await response.text()
                        print(f"[DEBUG] 410 Error: {error_detail}")
                        return f"❌ Modelo no disponible (410). Detalle: {error_detail[:100]}"
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[DEBUG] Error {response.status}: {error_text}")
                        return f"❌ Error {response.status}: {error_text[:100]}"
                    
                    result = await response.json()
                    
                    # Granite retorna una lista con el texto generado
                    print(f"[DEBUG] Response JSON: {result}")
                    response_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        if isinstance(result[0], dict):
                            response_text = result[0].get("generated_text", "").strip()
                        else:
                            response_text = str(result[0]).strip()
                    elif isinstance(result, dict):
                        response_text = result.get("generated_text", "").strip()
                    
                    # Limpiar el prompt de la respuesta si está incluido
                    if text in response_text:
                        response_text = response_text.replace(text, "").strip()
                    
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
                    
                    return "🤔 No tengo una respuesta para eso..."
        
        except asyncio.TimeoutError:
            return "⏱️ La IA tardó demasiado en responder. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @commands.command(name="ia")
    async def ia_chat(self, ctx: commands.Context, *, texto: str = None):
        """Chatea con la IA usando IBM Granite"""
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
