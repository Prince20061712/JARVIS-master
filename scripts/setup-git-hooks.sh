#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root"
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
chmod +x scripts/security/check_secrets.py

echo "Git hooks configured: core.hooksPath=.githooks"
