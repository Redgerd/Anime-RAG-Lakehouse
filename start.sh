#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Anime Sentiment Lakehouse — Startup Script
# ═══════════════════════════════════════════════════════════════

echo "🚀 Starting Anime Sentiment Lakehouse..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to become healthy..."
sleep 15

echo ""
echo "🌐 Opening UIs..."

# Detect OS and open browser accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  # Windows (Git Bash / PowerShell)
  start http://localhost:8081   # Flink
  start http://localhost:9001   # MinIO
  start http://localhost:19120  # Nessie
  start http://localhost:9090   # Prometheus
  start http://localhost:3000   # Grafana
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  open http://localhost:8081
  open http://localhost:9001
  open http://localhost:19120
  open http://localhost:9090
  open http://localhost:3000
else
  # Linux
  xdg-open http://localhost:8081
  xdg-open http://localhost:9001
  xdg-open http://localhost:19120
  xdg-open http://localhost:9090
  xdg-open http://localhost:3000
fi

echo ""
echo "✅ All done! Services running:"
echo ""
echo "   Flink        → http://localhost:8081"
echo "   MinIO        → http://localhost:9001  (minioadmin / minioadmin123)"
echo "   Nessie       → http://localhost:19120"
echo "   Prometheus   → http://localhost:9090"
echo "   Grafana      → http://localhost:3000  (admin / admin123)"
echo ""
echo "   To stop everything: docker compose down"