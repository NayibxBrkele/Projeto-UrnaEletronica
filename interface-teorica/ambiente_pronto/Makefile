# =============================================================================
# MAKEFILE PARA OPEN WATCOM C/C++ (DOS 16-BIT / 32-BIT) E GCC (HOST SIMULADOR)
# =============================================================================
# Para compilar para DOS Real-Mode (16-bit) com Open Watcom:
#     wmake -f Makefile.watcom
# Para compilar nativamente no Linux/Windows/macOS (GCC/MinGW):
#     make
# =============================================================================

CC       = gcc
CFLAGS   = -O2 -Wall -Wextra -Iinclude

VIRTUOS_BINS = \
	FI_C/virtuos/ckpack.exe \
	FI_C/virtuos/tipurna.exe \
	FI_C/virtuos/arqcmp.exe \
	FI_C/virtuos/diskfix.exe \
	FI_C/virtuos/log.exe \
	FI_C/virtuos/gecho.exe \
	FI_C/virtuos/res.exe \
	FI_C/virtuos/boot.com \
	FI_C/virtuos/desliga.com

APLIC_BINS = \
	FI_C/aplic/desbloq.exe \
	FI_C/aplic/diag_manut.exe \
	FI_C/aplic/vvota.exe \
	FI_C/aplic/vred.exe \
	FI_C/aplic/vcant_e.exe \
	FI_C/aplic/vjustif.exe \
	FI_C/aplic/vaudit.exe

all: $(VIRTUOS_BINS) $(APLIC_BINS)

FI_C/virtuos/ckpack.exe: src/virtuos/ckpack.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/tipurna.exe: src/virtuos/tipurna.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/arqcmp.exe: src/virtuos/arqcmp.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/diskfix.exe: src/virtuos/diskfix.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/log.exe: src/virtuos/log.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/gecho.exe: src/virtuos/gecho.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/res.exe: src/virtuos/sys_power.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/boot.com: src/virtuos/sys_power.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/virtuos/desliga.com: src/virtuos/sys_power.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/aplic/desbloq.exe: src/aplic/desbloq.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@
	cp $@ RAM_E/desbloq.exe

FI_C/aplic/diag_manut.exe: src/aplic/diag_manut.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/aplic/vvota.exe: src/aplic/vvota.c src/aplic/ui_urna.c src/virtuos/lmvos.c src/virtuos/mterm_display.c src/aplic/cepesc_crypto.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) src/aplic/vvota.c src/aplic/ui_urna.c src/virtuos/lmvos.c src/virtuos/mterm_display.c src/aplic/cepesc_crypto.c -o $@

FI_C/aplic/vred.exe: src/aplic/vmodulos.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/aplic/vcant_e.exe: src/aplic/vmodulos.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/aplic/vjustif.exe: src/aplic/vmodulos.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@

FI_C/aplic/vaudit.exe: src/aplic/vaudit.c include/ue2000_types.h include/dos_compat.h
	$(CC) $(CFLAGS) $< -o $@
