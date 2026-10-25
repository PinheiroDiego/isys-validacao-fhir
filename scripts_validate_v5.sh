#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="7.0.3"
mkdir -p "$ROOT/tools" "$ROOT/outputs/official_v5/evaluation/logs"
JAR="$ROOT/tools/validator_cli_${VERSION}.jar"
if [[ ! -f "$JAR" ]]; then
 curl -fL --retry 2 --connect-timeout 15 --max-time 180 \
  "https://github.com/hapifhir/org.hl7.fhir.core/releases/download/${VERSION}/validator_cli.jar" \
  -o "$JAR" 2>&1 | tee "$ROOT/outputs/official_v5/evaluation/logs/download.txt"
fi
python3 "$ROOT/src/verify_v5.py"
python3 "$ROOT/src/run_hl7_v5.py" --jar "$JAR"
