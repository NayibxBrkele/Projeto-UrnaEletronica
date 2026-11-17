# Inventário da Base Documental

Este documento detalha a estrutura e os ficheiros que compõem a reconstrução da base documental da UE2000 presentes no diretório `codigo-fonte/`.

- **Quantidade de ficheiros mapeados:** 44

## Distribuição

| Caminho | Quantidade | Conteúdo |
|---|---:|---|
| `include/` | 2 | Cabeçalhos C |
| `src/virtuos/` | 9 | Módulos C atribuídos à camada VirtuOS na reconstrução |
| `src/aplic/` | 7 | Módulos C de aplicação/demonstração |
| `arquivos_lote/` | 24 | `SETUP.BAT`, `instala.bat` e 22 ficheiros `roda_*.bat` |
| Raiz do diretório | 2 | `Makefile` e `LEIA-ME_BASE_DOCUMENTAL.md` |
| **Total** | **44** | |

## Ficheiros por diretório

### `include/`
- `dos_compat.h`
- `ue2000_types.h`

### `src/virtuos/`
- `arqcmp.c`
- `ckpack.c`
- `diskfix.c`
- `gecho.c`
- `lmvos.c`
- `log.c`
- `mterm_display.c`
- `sys_power.c`
- `tipurna.c`

### `src/aplic/`
- `cepesc_crypto.c`
- `desbloq.c`
- `diag_manut.c`
- `ui_urna.c`
- `vaudit.c`
- `vmodulos.c`
- `vvota.c`

### `arquivos_lote/`
- `SETUP.BAT`
- `instala.bat`
- `roda_acv.bat`
- `roda_asv.bat`
- `roda_can1.bat`
- `roda_can2.bat`
- `roda_j1.bat`
- `roda_j2.bat`
- `roda_se1.bat`
- `roda_se2.bat`
- `roda_sj1.bat`
- `roda_sj2.bat`
- `roda_sv1.bat`
- `roda_sv2.bat`
- `roda_t1.bat`
- `roda_t2.bat`
- `roda_tj1.bat`
- `roda_tj2.bat`
- `roda_tm1.bat`
- `roda_tm2.bat`
- `roda_tv1.bat`
- `roda_tv2.bat`
- `roda_v1.bat`
- `roda_v2.bat`

## Itens acrescentados para o ambiente moderno

Além dos 44 ficheiros preservados e mapeados para a recriação da base documental, foi acrescentado o ficheiro `codigo-fonte/build-host.sh`. Este script é um auxiliar POSIX criado para estruturar os diretórios de saída e invocar o `Makefile` com o compilador GCC. Trata-se de uma conveniência moderna do repositório para facilitar a compilação, não sendo um ficheiro histórico da UE2000.

## Interface Gráfica
Para a interação com os binários gerados por esta base, consulte o diretório `interface-teorica/`, que contém a demonstração moderna e visual construída em Python/Tkinter.
