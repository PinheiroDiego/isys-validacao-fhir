#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="7.0.3"
URL="https://github.com/hapifhir/org.hl7.fhir.core/releases/download/${VERSION}/validator_cli.jar"
JAR="$BASE_DIR/tools/validator_cli_${VERSION}.jar"
mkdir -p "$BASE_DIR/tools" "$BASE_DIR/logs"
if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 2 --connect-timeout 10 --max-time 180 "$URL" -o "$JAR" \
    2>&1 | tee "$BASE_DIR/logs/validator-download.txt"
fi
python3 - "$JAR" <<'PY'
import sys,zipfile,hashlib
p=sys.argv[1]
assert zipfile.is_zipfile(p), 'Arquivo não é JAR válido'
print('Arquivo:',p)
print('SHA-256:',hashlib.sha256(open(p,'rb').read()).hexdigest())
with zipfile.ZipFile(p) as z:
 if 'META-INF/MANIFEST.MF' in z.namelist():
  manifest=z.read('META-INF/MANIFEST.MF').decode('utf-8',errors='replace')
  print('Manifest (metadados):',manifest[:400])
PY
python3 "$BASE_DIR/scripts/run_official.py" --jar "$JAR" --root "$BASE_DIR"
