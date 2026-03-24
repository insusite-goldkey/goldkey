#!/bin/bash
set -e
echo "[HQ-INIT] Starting Goldkey-AI Dual Stack Service..."
exec /usr/bin/supervisord -n -c /home/user/app/supervisord.conf