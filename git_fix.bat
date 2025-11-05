@echo off
git reset --soft HEAD~1
git add .
git commit -m "Add AI conversational system with DialoGPT, playlist support, auto-disconnect, and Spotify limits"
git push origin main
