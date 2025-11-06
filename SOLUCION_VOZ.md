# 🔧 Solución: Error de Conexión de Voz (4006)

## ❌ Problema

```
discord.errors.ConnectionClosed: Shard ID None WebSocket closed with 4006
```

Este error significa que **FFmpeg** y **libopus** no están instalados en Replit.

---

## ✅ Solución en Replit

### **Opción 1: Configuración Automática (Recomendada)**

1. **Los archivos `.replit` y `replit.nix` ya están creados**
   - Estos archivos configuran Replit para instalar FFmpeg automáticamente

2. **Reinicia el Repl:**
   - Click en el botón "Stop" (si está corriendo)
   - Click en "Run" de nuevo
   - Replit detectará los archivos y instalará las dependencias

3. **Espera a que termine la instalación:**
   - Verás mensajes de instalación en la consola
   - Puede tardar 1-2 minutos la primera vez

4. **Prueba el comando:**
   ```
   #voz Hola, esta es una prueba
   ```

---

### **Opción 2: Instalación Manual (Si la Opción 1 falla)**

1. **Abre la Shell de Replit:**
   - Click en "Shell" (pestaña al lado de "Console")

2. **Ejecuta estos comandos:**
   ```bash
   # Instalar FFmpeg
   nix-env -iA nixpkgs.ffmpeg-full
   
   # Instalar libopus
   nix-env -iA nixpkgs.libopus
   
   # Verificar instalación
   ffmpeg -version
   ```

3. **Reinicia el bot:**
   - Click en "Stop"
   - Click en "Run"

4. **Prueba el comando:**
   ```
   #voz Hola
   ```

---

## 🔍 Verificar que Funciona

Después de la instalación, deberías ver en la consola:

```
✅ CORRECTO:
INFO discord.voice_state Connecting to voice...
INFO discord.voice_state Voice handshake complete
INFO discord.voice_state Voice connection complete

❌ INCORRECTO:
ERROR discord.voice_state Failed to connect to voice
ConnectionClosed: WebSocket closed with 4006
```

---

## 📋 Archivos Creados

- ✅ `.replit` - Configuración de Replit
- ✅ `replit.nix` - Dependencias del sistema (FFmpeg, libopus)
- ✅ `install_voice_deps.sh` - Script de instalación manual

---

## 🎯 ¿Por qué pasa esto?

Discord.py necesita:
1. **FFmpeg** - Para procesar audio
2. **libopus** - Para codificar/decodificar audio de Discord
3. **PyNaCl** - Para encriptar la conexión (ya instalado en requirements.txt)

Sin FFmpeg, el bot no puede establecer la conexión WebSocket de voz.

---

## 🚀 Pasos Completos (Desde Cero)

1. **Subir los archivos a GitHub** (ya hecho)
2. **En Replit:**
   - Los archivos `.replit` y `replit.nix` se detectan automáticamente
   - Click en "Run"
   - Espera la instalación
3. **Únete a un canal de voz en Discord**
4. **Prueba:**
   ```
   #voz Hola, ¿cómo estás?
   ```

---

## 💡 Alternativa: Usar otro Hosting

Si Replit sigue dando problemas, puedes usar:

### **Railway.app** (Recomendado)
- FFmpeg viene preinstalado
- Más estable para bots de Discord
- Gratis con límites generosos

### **Render.com**
- FFmpeg preinstalado
- Fácil de configurar
- Plan gratuito disponible

### **Heroku**
- Requiere buildpack de FFmpeg
- Más complejo pero funcional

---

## 🔧 Troubleshooting

### "nix-env: command not found"
- Replit debería tener Nix instalado por defecto
- Intenta con la Opción 1 (archivos de configuración)

### "Permission denied"
- No uses `sudo` en Replit
- Usa `nix-env` en lugar de `apt-get`

### El bot se conecta pero no reproduce audio
- Verifica que FFmpeg esté instalado: `ffmpeg -version`
- Verifica permisos del bot en Discord (Conectar, Hablar)

### Sigue sin funcionar
- Considera migrar a Railway o Render
- Ambos tienen FFmpeg preinstalado

---

## 📞 Soporte

Si después de seguir estos pasos sigue sin funcionar:

1. Verifica la consola de Replit
2. Busca errores diferentes al 4006
3. Comparte los logs completos

---

## ✨ Una vez funcionando...

Podrás usar:
- `#voz <pregunta>` - Conversar con IA por voz
- `#voz_reset` - Reiniciar historial
- `#voz_stop` - Desconectar del canal

¡Disfruta de las conversaciones por voz con Sthashior! 🎤🌸
