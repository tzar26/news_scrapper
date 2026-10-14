# Настройка Ollama для проекта

## Требования

- Ollama 0.35.0+
- GPU с достаточной VRAM (у нас 2×P100, 16 ГБ каждая)
- Установлен как systemd-сервис (Ubuntu 24.04)

## Переменные окружения (через `systemctl edit ollama.service`)

[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_KEEP_ALIVE=-1"

**Зачем:**
- `MAX_LOADED_MODELS=2` — держать bge-m3 и qwen одновременно в VRAM.
  Без этого — ping-pong, каждое переключение 25–30 сек.
- `KEEP_ALIVE=-1` — не выгружать модели через 5 минут простоя.

## Модели

- `qwen2.5-coder:14b-16k` — chat/edit. ~12 ГБ с контекстом 16K.
- `bge-m3` — embeddings (1024d). ~664 МБ.

## Проверка после перезапуска

```bash
# Прогрев
curl -s http://localhost:11434/api/embed -d '{"model": "bge-m3", "input": "x"}' > /dev/null
curl -s http://localhost:11434/api/chat -d '{"model": "qwen2.5-coder:14b-16k", "messages": [{"role": "user", "content": "hi"}], "stream": false}' > /dev/null

# Проверка — обе в VRAM
curl -s http://localhost:11434/api/ps | python -m json.tool
