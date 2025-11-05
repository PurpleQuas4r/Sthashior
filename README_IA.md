# 🤖 Sthashior IA - Configuración

## ✨ Nueva Funcionalidad: IA Conversacional

Sthashior ahora puede mantener conversaciones usando **Facebook BlenderBot-400M-distill** a través de Hugging Face.

> **Nota**: Anteriormente usábamos DialoGPT-small, pero fue deprecado por Microsoft. BlenderBot ofrece mejor soporte multiidioma y respuestas más naturales.

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
- Mantiene contexto de los últimos 3 mensajes
- Cada usuario tiene su propio historial
- Respuestas personalizadas y naturales
- Mejor soporte para español

### `#ia_reset`
Reinicia tu historial de conversación.

**Ejemplo:**
```
#ia_reset
```

---

## 🧠 Modelo de IA

**Modelo Actual**: `facebook/blenderbot-400M-distill`

**Características:**
- ✅ Gratuito
- ✅ Sin límites de uso
- ✅ Optimizado para conversaciones
- ✅ Excelente soporte multiidioma (español incluido)
- ✅ Respuestas más naturales y contextuales
- ✅ Mantiene contexto de conversación

**Parámetros configurados:**
- `max_length`: 150 tokens
- `min_length`: 20 tokens
- `temperature`: 0.7 (balance creatividad/coherencia)
- `top_p`: 0.9 (diversidad)
- `repetition_penalty`: 1.2 (evita repeticiones)

**¿Por qué BlenderBot?**
- DialoGPT fue deprecado por Microsoft (error 410)
- BlenderBot ofrece mejor rendimiento en español
- Respuestas más largas y detalladas
- Mejor comprensión del contexto

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

### Error 410: "El modelo no está disponible"
- Este error indicaba que DialoGPT fue deprecado
- Ya fue solucionado cambiando a BlenderBot
- Si persiste, contacta al administrador

### Respuestas de baja calidad
- BlenderBot funciona mejor con preguntas claras y específicas
- Usa `#ia_reset` si la conversación pierde coherencia
- El modelo mejora con contexto apropiado

---

## 📊 Información Técnica

**Archivo**: `cogs/ai_chat.py`  
**API**: Hugging Face Inference API  
**Modelo**: facebook/blenderbot-400M-distill  
**Timeout**: 45 segundos  
**Historial máximo**: 3 mensajes por usuario  
**Restricciones**: Solo servidor y canal específicos
