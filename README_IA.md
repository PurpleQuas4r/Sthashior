# 🤖 Sthashior IA - Configuración

## ✨ Nueva Funcionalidad: IA Conversacional

Sthashior ahora puede mantener conversaciones usando **Microsoft DialoGPT-small** a través de Hugging Face.

---

## 🔧 Configuración

### 1. Variables de Entorno

Añade esta variable a tu archivo `.env`:

```env
HUGGINGFACE_TOKEN=tu_token_de_huggingface_aqui
```

**Obtén tu token en**: https://huggingface.co/settings/tokens

### 2. IDs Configurados

El sistema de IA está configurado para funcionar **solo** en:

- **Servidor ID**: `391755494978617344`
- **Canal ID**: `1266262036250103970`

Para cambiar estos IDs, edita el archivo `cogs/ai_chat.py`:

```python
self.allowed_guild_id = 391755494978617344  # ID de tu servidor
self.allowed_channel_id = 1266262036250103970  # ID de tu canal
```

---

## 📝 Comandos Disponibles

### `#ia <mensaje>`
Inicia o continúa una conversación con la IA.

**Ejemplo:**
```
#ia Hola, ¿cómo estás?
```

**Características:**
- Mantiene contexto de los últimos 5 mensajes
- Cada usuario tiene su propio historial
- Respuestas personalizadas

### `#ia_reset`
Reinicia tu historial de conversación.

**Ejemplo:**
```
#ia_reset
```

---

## 🧠 Modelo de IA

**Modelo**: `microsoft/DialoGPT-small`

**Características:**
- ✅ Gratuito
- ✅ Sin límites de uso
- ✅ Ligero y rápido
- ✅ Conversaciones naturales
- ✅ Mantiene contexto

**Parámetros configurados:**
- `max_length`: 100 tokens
- `min_length`: 10 tokens
- `temperature`: 0.9 (creatividad)
- `top_p`: 0.9 (diversidad)

---

## 🔄 Modelo Alternativo

Si DialoGPT no está disponible, puedes cambiar a **BlenderBot**:

En `cogs/ai_chat.py`, línea 13:
```python
self.api_url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
```

---

## ⚠️ Notas Importantes

1. **Primera consulta**: El modelo puede tardar ~20 segundos en cargar la primera vez
2. **Respuesta 503**: Significa que el modelo se está cargando, espera unos segundos
3. **Historial**: Se guarda en memoria, se pierde al reiniciar el bot
4. **Privacidad**: Cada usuario tiene su propio historial separado

---

## 🎯 Ejemplo de Uso

```
Usuario: #ia Hola Sthashior
Bot: 🤖 Sthashior IA
     Hi! How are you doing today?

Usuario: #ia Cuéntame un chiste
Bot: 🤖 Sthashior IA
     Why did the scarecrow win an award? Because he was outstanding in his field!

Usuario: #ia_reset
Bot: ✅ Historial de conversación reiniciado.
```

---

## 🐛 Solución de Problemas

### Error: "Token de Hugging Face no configurado"
- Verifica que `HUGGINGFACE_TOKEN` esté en tu `.env`
- Reinicia el bot

### Error: "Este comando solo funciona en el canal designado"
- Verifica que estés en el canal correcto
- Verifica los IDs en `ai_chat.py`

### Error: "El modelo se está cargando"
- Espera 20-30 segundos
- Intenta de nuevo

### Respuestas en inglés
- DialoGPT está entrenado principalmente en inglés
- Para mejor soporte en español, considera usar BlenderBot

---

## 📊 Información Técnica

**Archivo**: `cogs/ai_chat.py`  
**API**: Hugging Face Inference API  
**Timeout**: 30 segundos  
**Historial máximo**: 5 mensajes por usuario  
**Restricciones**: Solo servidor y canal específicos
