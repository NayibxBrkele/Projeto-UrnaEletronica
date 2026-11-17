#!/bin/sh
# Auxiliar POSIX para preparar os diretórios previstos pelo Makefile e compilar
# os binários de demonstração para o sistema hospedeiro usando GCC.
set -eu

command -v gcc >/dev/null 2>&1 || {
    echo "Erro: gcc não encontrado no PATH." >&2
    exit 127
}
command -v make >/dev/null 2>&1 || {
    echo "Erro: make não encontrado no PATH." >&2
    exit 127
}

mkdir -p FI_C/virtuos FI_C/aplic RAM_E
exec make -f Makefile "$@"
