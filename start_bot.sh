#!/bin/bash

# Configurar rutas de Python
export PYTHONPATH="/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages:$PYTHONPATH"

# Configurar rutas de FFmpeg y libopus
export PATH="/nix/store/3zc5jbvqzrn8zmva4fx5p0nh4yy03wk4-ffmpeg-6.1.1-bin/bin:$PATH"
export LD_LIBRARY_PATH="/nix/store/0py9xncsn0s6vqxhvqblvhs2cqbb30s8-libopus-1.5.2/lib:/nix/store/2m0ngng1iy80h65052chw7mn18qbgq0w-libopus-1.5.2/lib:/nix/store/ssgy1vi7bfiqijy5p40hmi3vxkgrj2kv-libsodium-1.0.20/lib:$LD_LIBRARY_PATH"

# Verificar que FFmpeg funciona
echo "🔍 Verificando FFmpeg..."
ffmpeg -version | head -n 1

# Iniciar el bot
echo "🚀 Iniciando Sthashior Bot..."
python main.py
