import asyncio
import json
import os
import random
import time
from typing import Dict, Optional

import discord
from discord.ext import commands

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "datorandom.json")
RESP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "respuestas.json")
SARC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "respuestas_sarcasticas.json")

COOLDOWN_SECONDS = 45
PENALTY_SECONDS = 120
MESSAGE_TTL_SECONDS = 120
MAX_USES = 10


def _load_json_array(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # soporta formatos {"respuestas": [...]} y lista directa
        if isinstance(data, dict):
            for key in ("datos", "respuestas"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


class DatoRandom(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._datos = _load_json_array(DATA_PATH)
        self._respuestas = _load_json_array(RESP_PATH)
        self._sarcasticas = _load_json_array(SARC_PATH)
        # estado por usuario
        self._last_use: Dict[int, float] = {}
        self._cooldown_until: Dict[int, float] = {}
        self._cd_attempts: Dict[int, int] = {}
        self._penalty_until: Dict[int, float] = {}
        self._uses_count: Dict[int, int] = {}

    def _now(self) -> float:
        return time.time()

    def _in_penalty(self, user_id: int) -> bool:
        return self._penalty_until.get(user_id, 0) > self._now()

    def _in_cooldown(self, user_id: int) -> bool:
        return self._cooldown_until.get(user_id, 0) > self._now()

    def _cooldown_remaining(self, user_id: int) -> int:
        return max(0, int(self._cooldown_until.get(user_id, 0) - self._now()))

    async def _delete_later(self, *messages: discord.Message):
        await asyncio.sleep(MESSAGE_TTL_SECONDS)
        for m in messages:
            try:
                await m.delete()
            except Exception:
                pass

    def _random_text_from(self, collection: list) -> Optional[str]:
        if not collection:
            return None
        item = random.choice(collection)
        if isinstance(item, dict):
            return item.get("texto")
        if isinstance(item, str):
            return item
        return None

    @commands.command(name="datorandom", aliases=["dt"])
    async def datorandom(self, ctx: commands.Context):
        user_id = ctx.author.id

        # Si está bajo penalización: eliminar mensaje y no responder
        if self._in_penalty(user_id):
            try:
                await ctx.message.delete()
            except Exception:
                pass
            return

        # Límite de usos
        uses = self._uses_count.get(user_id, 0)
        if uses >= MAX_USES:
            txt = self._random_text_from(self._respuestas) or "Tu cuota de datos random expiró. Intenta mañana (￣ω￣;)"
            emb = discord.Embed(title="Dato Random", description=txt, color=discord.Color.orange())
            await ctx.send(embed=emb)
            return

        # Cooldown activo (no penalizado)
        if self._in_cooldown(user_id):
            # sumar intento, y si llega a 3 -> activar penalización y responder sarcástico 1 vez
            attempts = self._cd_attempts.get(user_id, 0) + 1
            self._cd_attempts[user_id] = attempts
            if attempts >= 3:
                self._penalty_until[user_id] = self._now() + PENALTY_SECONDS
                self._cd_attempts[user_id] = 0
                msg = self._random_text_from(self._sarcasticas) or "Relájate, campeón, no es una competencia (¬_¬)"
                await ctx.send(msg)
                return
            # informar tiempo restante
            rem = self._cooldown_remaining(user_id)
            emb = discord.Embed(title="Cooldown activo", description=f"⏳ Te faltan {rem}s para volver a usar el comando.", color=discord.Color.orange())
            await ctx.send(embed=emb)
            return

        # Entregar dato aleatorio
        text = self._random_text_from(self._datos) or "No hay datos disponibles ahora mismo."
        emb = discord.Embed(title="Dato Random", description=text, color=discord.Color.blurple())
        reply = await ctx.send(embed=emb)
        # programar borrado de ambos mensajes
        asyncio.create_task(self._delete_later(ctx.message, reply))

        # actualizar contadores y cooldown
        self._uses_count[user_id] = uses + 1
        self._last_use[user_id] = self._now()
        self._cooldown_until[user_id] = self._now() + COOLDOWN_SECONDS
        self._cd_attempts[user_id] = 0


async def setup(bot: commands.Bot):
    await bot.add_cog(DatoRandom(bot))
