#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export UE2000_FI="$DIR/FI_C"
export UE2000_FC="$DIR/FC_D"
export UE2000_DQ="$DIR/DQ_A"
export UE2000_RE="$DIR/RAM_E"
unset UE2000_NONINTERACTIVE
exec "$UE2000_FI/aplic/vvota.exe" "$@"
