# 🎤 Sthashior - Text-to-Speech (TTS)

## ✨ Nueva Funcionalidad: Voz en Discord

Sthashior ahora puede reproducir mensajes en canales de voz usando Text-to-Speech.

---

## 🎯 Comandos Disponibles

### `#voz <mensaje>`
Reproduce un mensaje en el canal de voz donde estés conectado.

**Ejemplo:**
```
#voz Hola a todos, soy Sthashior
```

**Características:**
- Usa Google TTS (Text-to-Speech)
- Voz en español
- Gratuito e ilimitado
- Se desconecta automáticamente después de reproducir

### `#voz_stop`
Detiene la reproducción actual y desconecta el bot del canal de voz.

---

## 📋 Requisitos

### 1. **FFmpeg** (Requerido)

FFmpeg es necesario para que Discord.py pueda reproducir audio.

#### En Replit:
```bash
# Ya está instalado por defecto
```

#### En Windows (local):
1. Descarga FFmpeg: https://ffmpeg.org/download.html
2. Extrae el archivo
3. Añade la carpeta `bin` al PATH del sistema
4. Verifica: `ffmpeg -version`

#### En Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. **Dependencias Python**

Ya incluidas en `requirements.txt`:
```
gTTS==2.5.1        # Google Text-to-Speech
PyNaCl==1.5.0      # Soporte de voz para Discord
```

---

## 🚀 Uso

1. **Únete a un canal de voz**
2. **Escribe el comando:**
   ```
   #voz Hola, este es un mensaje de prueba
   ```
3. **El bot se conectará y reproducirá el mensaje**
4. **Se desconectará automáticamente**

---

## ⚙️ Características Técnicas

### Google TTS
- **Idioma:** Español (es)
- **Velocidad:** Normal
- **Calidad:** Alta
- **Límites:** Ninguno (gratuito e ilimitado)

### Comportamiento del Bot
- Se conecta al canal donde estés
- Reproduce el mensaje
- Se desconecta después de 3 segundos de inactividad
- Limpia archivos temporales automáticamente

---

## 🔧 Solución de Problemas

### "❌ Debes estar en un canal de voz"
- Conéctate a un canal de voz antes de usar el comando

### "⏳ Espera a que termine el mensaje anterior"
- El bot ya está reproduciendo algo
- Espera o usa `#voz_stop`

### "❌ Error al conectar al canal de voz"
- Verifica que el bot tenga permisos de "Conectar" y "Hablar"
- Verifica que FFmpeg esté instalado

### El bot se conecta pero no reproduce nada
- **Problema:** FFmpeg no está instalado o no está en el PATH
- **Solución:** Instala FFmpeg y reinicia el bot

---

## 🎨 Ejemplos de Uso

```bash
# Mensaje simple
#voz Hola a todos

# Mensaje largo
#voz Bienvenidos al servidor, espero que se diviertan y disfruten de la música

# Anuncio
#voz Atención, en 5 minutos comenzará el evento

# Detener
#voz_stop
```

---

## 💡 Limitaciones

1. **Solo texto:** No puede reproducir archivos de audio externos
2. **Un mensaje a la vez:** No puede encolar mensajes
3. **Idioma fijo:** Solo español (puedes cambiar en el código)
4. **Calidad:** Voz robótica (TTS básico, no IA conversacional)

---

## 🔮 Futuras Mejoras Posibles

- ✨ Voces más naturales (ElevenLabs, Play.ht)
- 🎭 Múltiples voces/idiomas
- 📝 Cola de mensajes
- 🎵 Efectos de sonido
- 🤖 Integración con IA conversacional

---

## 📊 Comparación de Servicios TTS

| Servicio | Gratis | Calidad | Límites | Voces |
|----------|--------|---------|---------|-------|
| **Google TTS** | ✅ | ⭐⭐⭐ | Ilimitado | Básicas |
| ElevenLabs | ⚠️ | ⭐⭐⭐⭐⭐ | 10k chars/mes | Naturales |
| Play.ht | ⚠️ | ⭐⭐⭐⭐ | 2.5k chars/mes | Múltiples |
| Amazon Polly | ⚠️ | ⭐⭐⭐⭐ | 5M chars/mes | Profesionales |

**Actualmente usamos Google TTS por ser completamente gratuito e ilimitado.**

---

## 🌸 ¡Disfruta de la nueva funcionalidad de voz! 🎤
