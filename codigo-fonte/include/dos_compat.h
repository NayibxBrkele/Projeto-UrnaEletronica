/* ============================================================================
 * ARQUIVO     : include/dos_compat.h
 * PROJETO     : TSE-UE2000 (Camada de Portabilidade DOS Watcom <-> POSIX/Win)
 * DESCRICAO   : Permite compilar exatamente o mesmo codigo-fonte tanto no
 *               Open Watcom C/Borland C (DOS real/protected mode) quanto no
 *               GCC/Clang/MinGW moderno (simulando EEPROM e portas I/O em disco).
 * ============================================================================ */

#ifndef _DOS_COMPAT_H_
#define _DOS_COMPAT_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "ue2000_types.h"

#ifdef __GNUC__
#define UE_UNUSED __attribute__((unused))
#else
#define UE_UNUSED
#endif

/* Descobre a raiz da Flash Interna (C:\ no DOS ou variavel UE2000_FI no POSIX) */
static UE_UNUSED const char *ue2000_root_fi(void) {
    const char *env = getenv("UE2000_FI");
    return (env && env[0]) ? env : ".";
}

/* Converte caminhos DOS (ex: C:\basedado\candidat.dat) para o SO hospedeiro */
static UE_UNUSED void ue2000_resolve_path(const char *dos_path, char *out_buf, size_t out_sz) {
#if defined(__MSDOS__) || defined(__DOS__) || defined(_WIN32)
    snprintf(out_buf, out_sz, "%s", dos_path);
#else
    const char *fi = getenv("UE2000_FI");
    const char *fc = getenv("UE2000_FC");
    const char *dq = getenv("UE2000_DQ");
    const char *re = getenv("UE2000_RE");
    char temp[1024];
    size_t i;

    if (!fi) fi = ".";
    if (!fc) fc = "../FC_D";
    if (!dq) dq = "../DQ_A";
    if (!re) re = "../RAM_E";

    if ((dos_path[0] == 'C' || dos_path[0] == 'c') && dos_path[1] == ':') {
        snprintf(temp, sizeof(temp), "%s/%s", fi, dos_path + (dos_path[2] == '\\' || dos_path[2] == '/' ? 3 : 2));
    } else if ((dos_path[0] == 'D' || dos_path[0] == 'd') && dos_path[1] == ':') {
        snprintf(temp, sizeof(temp), "%s/%s", fc, dos_path + (dos_path[2] == '\\' || dos_path[2] == '/' ? 3 : 2));
    } else if ((dos_path[0] == 'A' || dos_path[0] == 'a') && dos_path[1] == ':') {
        snprintf(temp, sizeof(temp), "%s/%s", dq, dos_path + (dos_path[2] == '\\' || dos_path[2] == '/' ? 3 : 2));
    } else if ((dos_path[0] == 'E' || dos_path[0] == 'e') && dos_path[1] == ':') {
        snprintf(temp, sizeof(temp), "%s/%s", re, dos_path + (dos_path[2] == '\\' || dos_path[2] == '/' ? 3 : 2));
    } else {
        snprintf(temp, sizeof(temp), "%s", dos_path);
    }

    for (i = 0; temp[i]; i++) {
        if (temp[i] == '\\') temp[i] = '/';
    }
    snprintf(out_buf, out_sz, "%s", temp);
#endif
}

static UE_UNUSED uint16_t ue2000_crc16_ccitt(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    size_t i, j;
    for (i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (j = 0; j < 8; j++) {
            if (crc & 0x8000) crc = (uint16_t)((crc << 1) ^ 0x1021);
            else              crc <<= 1;
        }
    }
    return crc;
}

#if defined(__MSDOS__) || defined(__DOS__)
#include <dos.h>
#include <conio.h>
#else
/* ============================================================================
 * EMULADOR DE BARRAMENTO I/O E EEPROM PARA AMBIENTE POSIX / WINDOWS
 * ============================================================================ */
#if !defined(_WIN32)
#include <termios.h>
#include <unistd.h>
#endif
#define stricmp strcasecmp

typedef struct {
    EEPROM_URNA eeprom;
    uint8_t     eeprom_addr_latch;
    uint8_t     hw_status_reg;    /* 0x01 = Impressora detectada e pronta, bat OK */
    uint8_t     flash_wp_reg;     /* 0x01 = Write-Protect ativo                   */
    uint8_t     power_relay_reg;  /* 0x00 = Ligada, 0xFF = Desligada              */
} VIRTUAL_HW_BUS;

static VIRTUAL_HW_BUS g_vbus;
static int g_vbus_loaded = 0;

static void vbus_get_file(char *out, size_t sz) {
    snprintf(out, sz, "%s/VIRTUAL_HW.BIN", ue2000_root_fi());
}

static void vbus_load(void) {
    char path[1024];
    FILE *f;
    if (g_vbus_loaded) return;
    vbus_get_file(path, sizeof(path));
    f = fopen(path, "rb");
    if (f) {
        if (fread(&g_vbus, sizeof(VIRTUAL_HW_BUS), 1, f) == 1) {
            fclose(f);
            g_vbus_loaded = 1;
            return;
        }
        fclose(f);
    }
    /* Estado default de fabrica para uma urna UE2000 integra */
    memset(&g_vbus, 0, sizeof(VIRTUAL_HW_BUS));
    memcpy(g_vbus.eeprom.assinatura, "TSE", 4);
    g_vbus.eeprom.modelo_urna    = MODELO_HW_UE2000;
    g_vbus.eeprom.numero_serie   = 654321UL;
    g_vbus.eeprom.lote_fabrica   = 1;
    g_vbus.eeprom.modo_operacao  = EEPROM_MODO_FCC0;
    g_vbus.eeprom.contador_boots = 1;
    g_vbus.eeprom.crc16_eeprom   = ue2000_crc16_ccitt(
        (const uint8_t *)&g_vbus.eeprom, sizeof(EEPROM_URNA) - sizeof(uint16_t)
    );
    g_vbus.hw_status_reg  = 0x01; /* Bit 0=1 (Impressora presente), demais=0 (OK) */
    g_vbus.flash_wp_reg   = 0x01; /* Protecao de escrita ativa */
    g_vbus.power_relay_reg= 0x00;
    g_vbus_loaded = 1;
}

static void vbus_save(void) {
    char path[1024];
    FILE *f;
    vbus_get_file(path, sizeof(path));
    f = fopen(path, "wb");
    if (f) {
        fwrite(&g_vbus, sizeof(VIRTUAL_HW_BUS), 1, f);
        fclose(f);
    }
}

static UE_UNUSED int inp(unsigned short port) {
    const uint8_t *eep_bytes;
    vbus_load();
    eep_bytes = (const uint8_t *)&g_vbus.eeprom;
    switch (port) {
        case IO_PORT_EEPROM_ADDR: return g_vbus.eeprom_addr_latch;
        case IO_PORT_EEPROM_DATA:
            if (g_vbus.eeprom_addr_latch < sizeof(EEPROM_URNA)) {
                return eep_bytes[g_vbus.eeprom_addr_latch];
            }
            return 0xFF;
        case IO_PORT_HW_STATUS:   return g_vbus.hw_status_reg;
        case IO_PORT_FLASH_WP:    return g_vbus.flash_wp_reg;
        case IO_PORT_POWER_RELAY: return g_vbus.power_relay_reg;
        case 0x02FD:              return 0x20; /* UART LSR: TX Holding Empty */
        default:                  return 0x00;
    }
}

static UE_UNUSED void outp(unsigned short port, int val) {
    uint8_t *eep_bytes;
    vbus_load();
    eep_bytes = (uint8_t *)&g_vbus.eeprom;
    switch (port) {
        case IO_PORT_EEPROM_ADDR:
            g_vbus.eeprom_addr_latch = (uint8_t)(val & 0xFF);
            break;
        case IO_PORT_EEPROM_DATA:
            if (g_vbus.eeprom_addr_latch < sizeof(EEPROM_URNA)) {
                eep_bytes[g_vbus.eeprom_addr_latch] = (uint8_t)(val & 0xFF);
                /* Atualiza CRC da EEPROM automaticamente ao alterar modo */
                if (g_vbus.eeprom_addr_latch == 10 || g_vbus.eeprom_addr_latch == 11) {
                    g_vbus.eeprom.crc16_eeprom = ue2000_crc16_ccitt(
                        (const uint8_t *)&g_vbus.eeprom, sizeof(EEPROM_URNA) - sizeof(uint16_t)
                    );
                }
            }
            break;
        case IO_PORT_HW_STATUS:
            g_vbus.hw_status_reg = (uint8_t)(val & 0xFF);
            break;
        case IO_PORT_FLASH_WP:
            g_vbus.flash_wp_reg = (uint8_t)(val & 0xFF);
            break;
        case IO_PORT_POWER_RELAY:
            g_vbus.power_relay_reg = (uint8_t)(val & 0xFF);
            break;
        default:
            break;
    }
    vbus_save();
}

static UE_UNUSED void clrscr(void) {
    printf("\033[2J\033[H");
}

static UE_UNUSED int getch(void) {
#if defined(_WIN32)
    int c = getchar();
    return (c == '\n') ? 0x0D : c;
#else
    struct termios old_t, new_t;
    int c;
    if (!isatty(STDIN_FILENO)) {
        c = getchar();
        return (c == '\n') ? 0x0D : c;
    }
    if (tcgetattr(STDIN_FILENO, &old_t) != 0) return getchar();
    new_t = old_t;
    new_t.c_lflag &= (tcflag_t)~(ICANON | ECHO);
    new_t.c_cc[VMIN] = 1;
    new_t.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &new_t) != 0) return getchar();
    c = getchar();
    (void)tcsetattr(STDIN_FILENO, TCSADRAIN, &old_t);
    return (c == '\n') ? 0x0D : c;
#endif
}
#endif /* __MSDOS__ */

#endif /* _DOS_COMPAT_H_ */
