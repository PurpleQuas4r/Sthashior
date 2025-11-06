#!/bin/bash
# Script para instalar dependencias de voz en Replit

echo "🔧 Instalando dependencias de voz..."

# Instalar FFmpeg
echo "📦 Instalando FFmpeg..."
apt-get update -qq
apt-get install -y ffmpeg libopus0 libopus-dev

# Verificar instalación
echo "✅ Verificando instalación..."
ffmpeg -version
echo ""
echo "🎤 Dependencias de voz instaladas correctamente!"
echo "🔄 Reinicia el bot para aplicar los cambios."
