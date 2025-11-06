# 🔧 Instrucciones para Replit - Solución Definitiva

## ⚠️ Problema Actual

Tu instalación manual de FFmpeg está corrupta (Segmentation fault). Necesitamos limpiar y reinstalar.

---

## ✅ Solución Paso a Paso

### **Paso 1: Limpiar Instalación Corrupta**

En la **Shell de Replit**, ejecuta:

```bash
# Limpiar instalaciones corruptas
nix-env --uninstall ffmpeg-full
nix-env --uninstall libopus

# Limpiar caché
nix-collect-garbage -d
```

---

### **Paso 2: Subir Archivos Actualizados**

Los archivos `.replit` y `replit.nix` ya están actualizados en GitHub con:
- ✅ Canal Nix más reciente (24.05)
- ✅ FFmpeg 6 (más estable)
- ✅ Dependencias correctas

**En Replit:**

1. **Detén el bot** (Click "Stop")

2. **Actualiza desde GitHub:**
   - En la pestaña "Version Control" o "Git"
   - Click en "Pull" para obtener los cambios
   
   O en la Shell:
   ```bash
   git pull origin main
   ```

3. **Verifica que los archivos estén actualizados:**
   ```bash
   cat .replit
   cat replit.nix
   ```

---

### **Paso 3: Forzar Reinstalación**

1. **Elimina el archivo `.replit.nix` si existe:**
   ```bash
   rm -f .replit.nix
   ```

2. **Reinicia completamente Replit:**
   - Click en el menú (3 puntos) → "Hard Restart"
   - O simplemente cierra y vuelve a abrir el Repl

3. **Espera a que Replit instale las dependencias:**
   - Verás mensajes de instalación
   - Puede tardar 2-3 minutos
   - NO interrumpas el proceso

---

### **Paso 4: Verificar Instalación**

En la Shell, ejecuta:

```bash
# Verificar FFmpeg
which ffmpeg
ffmpeg -version

# Verificar libopus
ls /nix/store/ | grep libopus

# Verificar Python
python --version
```

**Deberías ver:**
```
✅ /nix/store/.../bin/ffmpeg
✅ ffmpeg version 6.x.x
✅ Archivos de libopus
✅ Python 3.11.x
```

**NO deberías ver:**
```
❌ Segmentation fault
❌ command not found
❌ No such file or directory
```

---

### **Paso 5: Probar el Bot**

1. **Inicia el bot:**
   ```bash
   python main.py
   ```

2. **En Discord:**
   - Únete a un canal de voz
   - Escribe: `#voz Hola, esta es una prueba`

3. **Verifica la consola:**
   ```
   ✅ CORRECTO:
   INFO discord.voice_state Connecting to voice...
   INFO discord.voice_state Voice handshake complete
   
   ❌ INCORRECTO:
   ERROR discord.voice_state Failed to connect
   ConnectionClosed: WebSocket closed with 4006
   ```

---

## 🆘 Si Sigue Sin Funcionar

### **Opción A: Recrear el Repl**

1. **Crea un nuevo Repl desde cero:**
   - Replit → "Create Repl"
   - "Import from GitHub"
   - URL: `https://github.com/PurpleQuas4r/Sthashior`

2. **Configura las variables de entorno:**
   - `TOKEN` = Tu token de Discord
   - `GROQ_API_KEY` = Tu API key de Groq
   - `SPOTIFY_CLIENT_ID` = Tu client ID
   - `SPOTIFY_CLIENT_SECRET` = Tu client secret

3. **Click "Run"**
   - Replit instalará todo automáticamente

---

### **Opción B: Migrar a Railway (Recomendado)**

Railway tiene FFmpeg preinstalado y es más estable:

1. **Ve a [railway.app](https://railway.app)**

2. **"New Project" → "Deploy from GitHub"**

3. **Selecciona tu repositorio**

4. **Configura variables de entorno** (igual que Replit)

5. **Deploy automático**

**Ventajas de Railway:**
- ✅ FFmpeg preinstalado
- ✅ Más estable
- ✅ Mejor rendimiento
- ✅ Gratis hasta $5/mes de uso

---

## 📋 Comandos Útiles de Replit

```bash
# Ver paquetes instalados
nix-env -q

# Limpiar todo
nix-collect-garbage -d

# Reinstalar desde cero
nix-env --uninstall '*'

# Ver logs del sistema
journalctl -xe

# Verificar espacio en disco
df -h
```

---

## 🎯 Resumen Rápido

1. **Limpiar:** `nix-env --uninstall ffmpeg-full libopus`
2. **Pull:** `git pull origin main`
3. **Reiniciar:** Hard Restart en Replit
4. **Esperar:** 2-3 minutos de instalación
5. **Verificar:** `ffmpeg -version`
6. **Probar:** `#voz Hola`

---

## 💡 ¿Por qué falló la instalación manual?

- Replit usa **Nix** para gestionar paquetes
- La instalación manual con `nix-env` puede causar conflictos
- Los archivos `.replit` y `replit.nix` son la forma correcta
- Replit gestiona las dependencias automáticamente

---

## ✨ Una vez funcionando...

Podrás usar:
```bash
#voz Hola, ¿cómo estás?          # Conversar con IA
#voz ¿Cuál es el sentido de la vida?  # Preguntas filosóficas
#voz Cuéntame un chiste          # Humor
#voz_reset                        # Reiniciar historial
#voz_stop                         # Desconectar
```

---

**¡Sigue estos pasos y debería funcionar! 🌸**
