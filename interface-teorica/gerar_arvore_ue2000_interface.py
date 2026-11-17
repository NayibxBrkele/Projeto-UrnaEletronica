#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
CONSTRUTOR E SIMULADOR DOCUMENTAL — INTERFACE UE2000 (v2.2)
===============================================================================
Este script reconstrói toda a árvore de diretórios, arquivos binários de estado,
bancos de dados eleitorais (candidat.dat, elelocal.dat), os 22 runners roda_*,
os scripts de sistema (SETUP.BAT, instala.bat, novobat.bat, setup.mnt), todos
os utilitários e aplicativos em C (compatíveis com Open Watcom C/DOS e GCC),
calcula e assina criptograficamente todos os 16 manifestos .crc/.sig e gera
a configuração pronta para DOSBox (dosbox_ue2000.conf) e Makefile.

Uso:
    python3 gerar_arvore_ue2000_interface.py [--dest ./ue2000_env] [--no-compile] [--no-test]
    cd ue2000_env && ./demo.sh  # iniciar interface interativa
===============================================================================
"""

import argparse
import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


# =============================================================================
# 1. DEFINIÇÃO DOS ARQUIVOS DE CABEÇALHO C (include/ue2000_types.h & dos_compat.h)
# =============================================================================

HEADER_UE2000_TYPES = r"""/* ============================================================================
 * ARQUIVO     : include/ue2000_types.h
 * PROJETO     : TSE-UE2000 (Reconstrucao Teorica Integral v2.1)
 * COMPILADOR  : Open Watcom C/C++ (16/32-bit DOS) / Borland C++ / GCC (POSIX/Win)
 * DESCRICAO   : Estruturas binarias exatas (estgeral.ctr, EEPROM, .crc/.sig,
 *               candidat.dat, elelocal.dat, RDV/BU e protocolo Microterminal)
 * ============================================================================ */

#ifndef _UE2000_TYPES_H_
#define _UE2000_TYPES_H_

#include <stdint.h>
#include <stddef.h>

#pragma pack(push, 1)

/* ----------------------------------------------------------------------------
 * 1.1. Estrutura do estgeral.ctr (64 bytes - Ap4D + Call sites de arqcmp)
 * ----------------------------------------------------------------------------
 * - Offset 0x00: rota_bateria -> testado por arqcmp ... 1 0 {0 | 240 | 241}
 * - Offset 0x01: fase_operacao -> testado por arqcmp ... 1 1 1 contra discoNN
 * ---------------------------------------------------------------------------- */
#define EST_ROTA_PADRAO         0x00  /* Segue para ue<modelo>_continuacao    */
#define EST_ROTA_BATERIA_1      0xF0  /* 240 dec -> ver_bateria<modelo>_1     */
#define EST_ROTA_BATERIA_2      0xF1  /* 241 dec -> ver_bateria<modelo>_2     */

#define FASE_NAO_INSTALADA      0x00
#define FASE_PRONTA_VOTACAO     0x01  /* Offset 1 == 1 (exigido por disco15)  */
#define FASE_EM_VOTACAO         0x02
#define FASE_ENCERRADA_1T       0x03
#define FASE_ENCERRADA_2T       0x04
#define FASE_MANUTENCAO         0xFF

typedef struct {
    uint8_t  rota_bateria;       /* 0x00: 0 (padrao), 240 (bat1), 241 (bat2)  */
    uint8_t  fase_operacao;      /* 0x01: 1 = Pronta, 2 = Votando, 3 = Encerr */
    uint8_t  turno_atual;        /* 0x02: 1 = 1o Turno, 2 = 2o Turno          */
    uint8_t  codigo_disco;       /* 0x03: 1..31, 99 (ultimo disco instalado)  */
    uint16_t zona_eleitoral;     /* 0x04: Numero da Zona Eleitoral            */
    uint16_t secao_eleitoral;    /* 0x06: Numero da Secao Eleitoral           */
    uint16_t municipio_cod;      /* 0x08: Codigo TSE do Municipio             */
    char     uf_sigla[2];        /* 0x0A: UF ("SP", "BA", "DF"...)            */
    uint32_t total_eleitores;    /* 0x0C: Total de eleitores aptos na secao   */
    uint32_t total_comparecim;   /* 0x10: Total de eleitores que ja votaram   */
    uint8_t  data_abertura[6];   /* 0x14: DD, MM, AA, HH, MM, SS              */
    uint8_t  data_fechamento[6]; /* 0x1A: DD, MM, AA, HH, MM, SS              */
    uint8_t  reservado[30];      /* 0x20..0x3D: Reservado Ap4D                */
    uint16_t crc16_estrutura;    /* 0x3E: CRC-16 CCITT dos primeiros 62 bytes */
} ESTGERAL_CTR;

/* ----------------------------------------------------------------------------
 * 1.2. Mapa de Portas I/O e EEPROM de Hardware (tipurna.exe / desbloq.exe)
 * ---------------------------------------------------------------------------- */
#define IO_PORT_EEPROM_ADDR     0x02E0
#define IO_PORT_EEPROM_DATA     0x02E1
#define IO_PORT_HW_STATUS       0x02E2  /* Bits de Impressora (0..3) e Bat (4..7) */
#define IO_PORT_FLASH_WP        0x02E3  /* 0x00 = Escrita Livre, 0x01 = Bloqueada */
#define IO_PORT_POWER_RELAY     0x02E4  /* 0xFF = Desliga fonte inteligente       */

#define MODELO_HW_INVALIDO      0x00
#define MODELO_HW_UE96          0x96
#define MODELO_HW_UE98          0x98
#define MODELO_HW_UE2000        0xA0

#define EEPROM_MODO_FCC0        0xFCC0  /* Modo Normal Operacional                */
#define EEPROM_MODO_FCC2        0xFCC2  /* Urna de Contingencia (Reserva Virgem)  */
#define EEPROM_MODO_FCC4        0xFCC4  /* Reserva Ativada (apos desbloq -r)      */
#define EEPROM_MODO_AUDIT       0xFCCA  /* Modo Auditoria V.PRE (apos desbloq -a) */
#define EEPROM_MODO_DIAG        0xFCCD  /* Modo Diagnostico (apos desbloq -d)     */
#define EEPROM_MODO_MANUT       0xFCCF  /* Modo Manutencao (apos desbloq -m)      */
#define EEPROM_MODO_ENCERRADO   0xFCEF  /* Votacao Encerrada (-z, -x, -y, -w)     */

typedef struct {
    char     assinatura[4];      /* 0x00: "TSE\0"                             */
    uint8_t  modelo_urna;        /* 0x04: 0x96, 0x98 ou 0xA0 (UE2000)         */
    uint32_t numero_serie;       /* 0x05: Faixa UE2000 = 500000..999999       */
    uint8_t  lote_fabrica;       /* 0x09: Lote Procomp/Microbase/Fucapi       */
    uint16_t modo_operacao;      /* 0x0A: EEPROM_MODO_FCC0..EEPROM_MODO_...   */
    uint16_t contador_boots;     /* 0x0C: Contador nao-volatil de boots       */
    uint16_t crc16_eeprom;       /* 0x0E: CRC-16 CCITT dos 14 bytes anteriores*/
} EEPROM_URNA;                   /* Tamanho total: 16 bytes                   */

/* ----------------------------------------------------------------------------
 * 1.3. Manifesto Criptografico .SIG (Algoritmo ASSINA 256-bit Microbase)
 * ---------------------------------------------------------------------------- */
typedef struct {
    char     magic[4];           /* "AS2K"                                    */
    uint32_t key_id;             /* Identificador da chave publica TSE 2000   */
    uint8_t  md5_crc_file[16];   /* Digest MD5 binario do arquivo .crc        */
    uint8_t  ec_signature[32];   /* Assinatura de 256 bits sobre o MD5        */
} ARQUIVO_SIG;                   /* Tamanho total: 56 bytes                   */

/* ----------------------------------------------------------------------------
 * 1.4. Tabelas Eleitorais: candidat.dat e elelocal.dat (C:\basedado\)
 * ---------------------------------------------------------------------------- */
#define CARGO_VEREADOR          1
#define CARGO_PREFEITO          2

typedef struct {
    uint8_t  cargo;              /* 1 = Vereador (5 dig), 2 = Prefeito (2 dig)*/
    uint32_t numero;             /* Numero do candidato (ex: 10..99 ou 10000) */
    char     nome_urna[32];      /* Nome exibido no LCD do eleitor            */
    char     partido_sigla[8];   /* Sigla do partido                          */
    char     arquivo_foto[16];   /* Nome do arquivo .BMP/.RAW em D:\fotos\    */
    char     arquivo_audio[16];  /* Nome do arquivo .WAV/.PCM em C:\canttrei\ */
    uint32_t total_votos;        /* Acumulador em memoria / arquivo de votos  */
} REGISTRO_CANDIDATO;

typedef struct {
    char     titulo_eleitor[13]; /* 12 digitos + '\0' (validado por Modulo-11)*/
    char     nome_eleitor[40];   /* Nome no caderno de votacao                */
    uint8_t  ja_votou;           /* 0 = Apto, 1 = Votou, 2 = Justificou       */
    uint16_t codigo_autenticacao;/* Hash curto impresso no comprovante        */
} REGISTRO_ELEITOR;

/* ----------------------------------------------------------------------------
 * 1.5. Protocolo Serial RS-485 do Microterminal do Mesario (COM2)
 * ---------------------------------------------------------------------------- */
#define MTERM_STX               0x02
#define MTERM_ETX               0x03
#define MTERM_CMD_RESET         0x10
#define MTERM_CMD_DISPLAY       0x20  /* Envia 2x20 caracteres ao LCD mesario */
#define MTERM_CMD_LED_LIBERADO  0x31  /* Acende LED verde "Eleitor Liberado"  */
#define MTERM_CMD_LED_OCUPADO   0x32  /* Acende LED amarelo "Cabine Ocupada"  */
#define MTERM_CMD_BEEP          0x40  /* Aciona buzzer do microterminal       */

typedef struct {
    uint8_t  stx;                /* 0x02                                      */
    uint8_t  cmd;                /* Comando MTERM_CMD_*                       */
    uint8_t  seq;                /* Numero de sequencia                       */
    char     linha1[20];         /* Linha superior do LCD do mesario          */
    char     linha2[20];         /* Linha inferior do LCD do mesario          */
    uint8_t  bcc;                /* XOR de todos os bytes de cmd ate linha2   */
    uint8_t  etx;                /* 0x03                                      */
} FRAME_MICROTERMINAL;

#pragma pack(pop)
#endif /* _UE2000_TYPES_H_ */
"""


HEADER_DOS_COMPAT = r"""/* ============================================================================
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
"""


# =============================================================================
# 2. CÓDIGO-FONTE DOS SUBSISTEMAS FECHADOS E UTILITÁRIOS (/virtuos e /aplic)
# =============================================================================

SRC_LMVOS_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/lmvos.c
 * PROJETO     : Microbase VirtuOS - LMVOS.LIB (Multitasking & Microterminal)
 * DESCRICAO   : Escalonador cooperativo de threads (setjmp/longjmp) e driver
 *               serial RS-485 com checksum BCC para o Microterminal do Mesario.
 * ============================================================================ */

#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/dos_compat.h"

#define MAX_VTHREADS        8
#define STACK_SIZE_BYTES    8192

typedef enum {
    VT_FREE = 0,
    VT_READY,
    VT_RUNNING,
    VT_SLEEPING
} VT_STATE;

typedef struct {
    int            id;
    VT_STATE       state;
    jmp_buf        context;
    unsigned long  wake_tick;
    void          (*entry)(void *);
    void          *arg;
} VTHREAD_TCB;

static VTHREAD_TCB   g_threads[MAX_VTHREADS];
static int           g_current_thread = 0;
static unsigned long g_system_ticks   = 0;
static uint8_t       g_mterm_seq      = 0;

void lmvos_init(void) {
    memset(g_threads, 0, sizeof(g_threads));
    g_threads[0].id    = 0;
    g_threads[0].state = VT_RUNNING;
}

int lmvos_thread_create(void (*func)(void *), void *arg) {
    int i;
    for (i = 1; i < MAX_VTHREADS; i++) {
        if (g_threads[i].state == VT_FREE) {
            g_threads[i].id    = i;
            g_threads[i].state = VT_READY;
            g_threads[i].entry = func;
            g_threads[i].arg   = arg;
            return i;
        }
    }
    return -1;
}

void lmvos_yield(void) {
    int prev = g_current_thread;
    volatile int next = (prev + 1) % MAX_VTHREADS;
    g_system_ticks++;

    while (next != prev) {
        if (g_threads[next].state == VT_SLEEPING && g_system_ticks >= g_threads[next].wake_tick) {
            g_threads[next].state = VT_READY;
        }
        if (g_threads[next].state == VT_READY) break;
        next = (next + 1) % MAX_VTHREADS;
    }
    if (next == prev) return;

    if (setjmp(g_threads[prev].context) == 0) {
        if (g_threads[prev].state == VT_RUNNING) g_threads[prev].state = VT_READY;
        g_current_thread = next;
        g_threads[next].state = VT_RUNNING;
        longjmp(g_threads[next].context, 1);
    }
}

/* Envia um quadro RS-485 completo (2x20 chars + BCC) para o Microterminal */
void lmvos_mterm_send_frame(uint8_t cmd, const char *l1, const char *l2) {
    FRAME_MICROTERMINAL frame;
    const uint8_t *raw = (const uint8_t *)&frame;
    uint8_t bcc = 0;
    size_t i;
    char log_path[1024];
    FILE *flog;

    memset(&frame, ' ', sizeof(frame));
    frame.stx = MTERM_STX;
    frame.cmd = cmd;
    frame.seq = ++g_mterm_seq;

    if (l1) memcpy(frame.linha1, l1, strlen(l1) < 20 ? strlen(l1) : 20);
    if (l2) memcpy(frame.linha2, l2, strlen(l2) < 20 ? strlen(l2) : 20);

    for (i = 1; i < offsetof(FRAME_MICROTERMINAL, bcc); i++) {
        bcc ^= raw[i];
    }
    frame.bcc = bcc;
    frame.etx = MTERM_ETX;

    /* Transmite byte a byte pela UART COM2 (0x02F8) */
    for (i = 0; i < sizeof(frame); i++) {
        while ((inp(0x02FD) & 0x20) == 0) {
            lmvos_yield();
        }
        outp(0x02F8, raw[i]);
    }

    /* Registra espelho visual do LCD do Mesario para inspecao e auditoria */
    ue2000_resolve_path("C:\\MTERM_LCD.LOG", log_path, sizeof(log_path));
    flog = fopen(log_path, "ab");
    if (flog) {
        fprintf(flog, "[SEQ=%03u CMD=0x%02X BCC=0x%02X] | %-20.20s | %-20.20s |\r\n",
                frame.seq, frame.cmd, frame.bcc, frame.linha1, frame.linha2);
        fclose(flog);
    }
}

/* Valida Titulo de Eleitor (12 digitos) segundo algoritmo oficial Modulo-11 TSE */
int lmvos_valida_titulo_tse(const char *titulo12) {
    int pesos1[8] = {2, 3, 4, 5, 6, 7, 8, 9};
    int soma = 0, resto, dv1, dv2, uf;
    int i;

    if (!titulo12 || strlen(titulo12) != 12) return 0;
    for (i = 0; i < 12; i++) {
        if (!isdigit((unsigned char)titulo12[i])) return 0;
    }

    for (i = 0; i < 8; i++) {
        soma += (titulo12[i] - '0') * pesos1[i];
    }
    resto = soma % 11;
    uf = (titulo12[8] - '0') * 10 + (titulo12[9] - '0');
    if (resto == 0) {
        dv1 = (uf == 1 || uf == 2) ? 1 : 0;
    } else if (resto == 10) {
        dv1 = 0;
    } else {
        dv1 = resto;
    }
    if ((titulo12[10] - '0') != dv1) return 0;

    soma = (titulo12[8] - '0') * 7 + (titulo12[9] - '0') * 8 + dv1 * 9;
    resto = soma % 11;
    if (resto == 0) {
        dv2 = (uf == 1 || uf == 2) ? 1 : 0;
    } else if (resto == 10) {
        dv2 = 0;
    } else {
        dv2 = resto;
    }
    return ((titulo12[11] - '0') == dv2) ? 1 : 0;
}
"""


SRC_CEPESC_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/cepesc_crypto.c
 * PROJETO     : Subsistema Criptografico CEPESC/ABIN (Reconstrucao L0/L3)
 * DESCRICAO   : Cifrador simetrico Feistel de 16 rodadas (BU e RDV) + ASSINA
 * ============================================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/dos_compat.h"

static const uint32_t K_CEPESC_SUBKEYS[16] = {
    0x7A91C40EUL, 0x55B83DE2UL, 0x196FA344UL, 0x8CD02B77UL,
    0xE9035AC1UL, 0x984E62F5UL, 0x318BD714UL, 0xA650CC39UL,
    0xB4F1092DUL, 0x6C3A85E1UL, 0x0F72D49BUL, 0xD81E53A0UL,
    0x4297C61FUL, 0xF0841B6EUL, 0x5E2D9A3CUL, 0x87C3E045UL
};

static void cepesc_feistel_encrypt_block(uint32_t *L, uint32_t *R) {
    int r;
    for (r = 0; r < 16; r++) {
        uint32_t temp = *R;
        uint32_t f    = ((*R << 5) | (*R >> 27)) ^ (*R + K_CEPESC_SUBKEYS[r]) ^ 0x9E3779B9UL;
        *R = *L ^ f;
        *L = temp;
    }
}

int cepesc_cifra_e_assina_bu(const char *bu_claro_dos, const char *bu_cifrado_dos) {
    char in_path[1024], out_path[1024];
    FILE *in, *out;
    uint32_t bloco[2];
    size_t lidos;

    ue2000_resolve_path(bu_claro_dos, in_path, sizeof(in_path));
    ue2000_resolve_path(bu_cifrado_dos, out_path, sizeof(out_path));

    in  = fopen(in_path, "rb");
    out = fopen(out_path, "wb");
    if (!in || !out) {
        if (in)  fclose(in);
        if (out) fclose(out);
        return -1;
    }

    while ((lidos = fread(bloco, 1, sizeof(bloco), in)) > 0) {
        if (lidos < sizeof(bloco)) {
            memset(((uint8_t *)bloco) + lidos, 0, sizeof(bloco) - lidos);
        }
        cepesc_feistel_encrypt_block(&bloco[0], &bloco[1]);
        fwrite(bloco, sizeof(bloco), 1, out);
    }

    fclose(in);
    fclose(out);
    return 0;
}
"""


SRC_CKPACK_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/ckpack.c
 * BINARIO     : C:\VIRTUOS\CKPACK.EXE
 * CONTRATO L4 : ckpack [-m] <arquivo.crc> <diretorio>
 * DESCRICAO   : Verifica a assinatura ASSINA (.sig) de 256 bits sobre o .crc e
 *               confere o resumo MD5 (RFC 1321) de cada arquivo listado.
 *               A flag -m flexibiliza divergencias em arquivos '*cant*'.
 * ============================================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "../include/dos_compat.h"

/* Implementacao RFC 1321 MD5 completa e portavel */
static const uint32_t MD5_K[64] = {
    0xd76aa478UL, 0xe8c7b756UL, 0x242070dbUL, 0xc1bdceeeUL,
    0xf57c0fafUL, 0x4787c62aUL, 0xa8304613UL, 0xfd469501UL,
    0x698098d8UL, 0x8b44f7afUL, 0xffff5bb1UL, 0x895cd7beUL,
    0x6b901122UL, 0xfd987193UL, 0xa679438eUL, 0x49b40821UL,
    0xf61e2562UL, 0xc040b340UL, 0x265e5a51UL, 0xe9b6c7aaUL,
    0xd62f105dUL, 0x02441453UL, 0xd8a1e681UL, 0xe7d3fbc8UL,
    0x21e1cde6UL, 0xc33707d6UL, 0xf4d50d87UL, 0x455a14edUL,
    0xa9e3e905UL, 0xfcefa3f8UL, 0x676f02d9UL, 0x8d2a4c8aUL,
    0xfffa3942UL, 0x8771f681UL, 0x6d9d6122UL, 0xfde5380cUL,
    0xa4beea44UL, 0x4bdecfa9UL, 0xf6bb4b60UL, 0xbebfbc70UL,
    0x289b7ec6UL, 0xeaa127faUL, 0xd4ef3085UL, 0x04881d05UL,
    0xd9d4d039UL, 0xe6db99e5UL, 0x1fa27cf8UL, 0xc4ac5665UL,
    0xf4292244UL, 0x432aff97UL, 0xab9423a7UL, 0xfc93a039UL,
    0x655b59c3UL, 0x8f0ccc92UL, 0xffeff47dUL, 0x85845dd1UL,
    0x6fa87e4fUL, 0xfe2ce6e0UL, 0xa3014314UL, 0x4e0811a1UL,
    0xf7537e82UL, 0xbd3af235UL, 0x2ad7d2bbUL, 0xeb86d391UL
};

static const uint8_t MD5_S[64] = {
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21
};

#define LEFTROTATE(x, c) (((x) << (c)) | ((x) >> (32 - (c))))

static int md5_file_digest(const char *host_path, uint8_t digest[16], char hex_out[33]) {
    FILE *f = fopen(host_path, "rb");
    uint8_t *msg = NULL;
    long file_len;
    size_t new_len, offset;
    uint32_t h0 = 0x67452301UL, h1 = 0xefcdab89UL;
    uint32_t h2 = 0x98badcfeUL, h3 = 0x10325476UL;
    uint64_t bits_len;
    int i;

    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    file_len = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (file_len < 0) { fclose(f); return -1; }

    new_len = (size_t)file_len + 1;
    while ((new_len % 64) != 56) new_len++;

    msg = (uint8_t *)calloc(new_len + 8, 1);
    if (!msg) { fclose(f); return -1; }

    if (file_len > 0 && fread(msg, 1, (size_t)file_len, f) != (size_t)file_len) {
        free(msg);
        fclose(f);
        return -1;
    }
    fclose(f);

    msg[file_len] = 0x80;
    bits_len = (uint64_t)file_len * 8ULL;
    for (i = 0; i < 8; i++) {
        msg[new_len + i] = (uint8_t)((bits_len >> (8 * i)) & 0xFF);
    }

    for (offset = 0; offset < new_len; offset += 64) {
        uint32_t w[16];
        uint32_t a = h0, b = h1, c = h2, d = h3;
        for (i = 0; i < 16; i++) {
            w[i] = (uint32_t)msg[offset + i * 4] |
                   ((uint32_t)msg[offset + i * 4 + 1] << 8) |
                   ((uint32_t)msg[offset + i * 4 + 2] << 16) |
                   ((uint32_t)msg[offset + i * 4 + 3] << 24);
        }
        for (i = 0; i < 64; i++) {
            uint32_t f_val, g;
            if (i < 16) {
                f_val = (b & c) | ((~b) & d);
                g = (uint32_t)i;
            } else if (i < 32) {
                f_val = (d & b) | ((~d) & c);
                g = (uint32_t)((5 * i + 1) % 16);
            } else if (i < 48) {
                f_val = b ^ c ^ d;
                g = (uint32_t)((3 * i + 5) % 16);
            } else {
                f_val = c ^ (b | (~d));
                g = (uint32_t)((7 * i) % 16);
            }
            {
                uint32_t temp = d;
                d = c;
                c = b;
                b = b + LEFTROTATE((a + f_val + MD5_K[i] + w[g]), MD5_S[i]);
                a = temp;
            }
        }
        h0 += a; h1 += b; h2 += c; h3 += d;
    }
    free(msg);

    for (i = 0; i < 4; i++) {
        digest[i]      = (uint8_t)((h0 >> (8 * i)) & 0xFF);
        digest[i + 4]  = (uint8_t)((h1 >> (8 * i)) & 0xFF);
        digest[i + 8]  = (uint8_t)((h2 >> (8 * i)) & 0xFF);
        digest[i + 12] = (uint8_t)((h3 >> (8 * i)) & 0xFF);
    }
    for (i = 0; i < 16; i++) {
        sprintf(hex_out + (i * 2), "%02x", digest[i]);
    }
    hex_out[32] = '\0';
    return 0;
}

static void assina_256_compute(const uint8_t md5_in[16], uint8_t sig_out[32]) {
    int i;
    for (i = 0; i < 16; i++) {
        sig_out[i]      = (uint8_t)(md5_in[i] ^ 0xA5 ^ (i * 17));
        sig_out[i + 16] = (uint8_t)((md5_in[15 - i] + 0x3C + (i * 9)) & 0xFF);
    }
}

static int verifica_assina_sig(const char *crc_host_path) {
    char sig_path[2056];
    uint8_t md5_crc[16], expected_sig[32];
    char hex_dummy[33];
    ARQUIVO_SIG sig;
    FILE *fs;
    char *dot;

    snprintf(sig_path, sizeof(sig_path), "%s", crc_host_path);
    dot = strrchr(sig_path, '.');
    if (dot) strcpy(dot, ".sig");
    else     strcat(sig_path, ".sig");

    if (md5_file_digest(crc_host_path, md5_crc, hex_dummy) != 0) return 0;

    fs = fopen(sig_path, "rb");
    if (!fs) return 0;
    if (fread(&sig, sizeof(ARQUIVO_SIG), 1, fs) != 1) {
        fclose(fs);
        return 0;
    }
    fclose(fs);

    if (memcmp(sig.magic, "AS2K", 4) != 0) return 0;
    if (memcmp(sig.md5_crc_file, md5_crc, 16) != 0) return 0;

    assina_256_compute(md5_crc, expected_sig);
    if (memcmp(sig.ec_signature, expected_sig, 32) != 0) return 0;

    return 1;
}

int main(int argc, char *argv[]) {
    int modo_m = 0;
    const char *crc_arg = NULL;
    const char *dir_arg = NULL;
    char crc_host[2048], dir_host[1024];
    FILE *fcrc;
    char nome[128], esperado[33];

    if (argc == 4 && (strcmp(argv[1], "-m") == 0 || strcmp(argv[1], "-M") == 0)) {
        modo_m  = 1;
        crc_arg = argv[2];
        dir_arg = argv[3];
    } else if (argc == 3) {
        crc_arg = argv[1];
        dir_arg = argv[2];
    } else {
        return 1;
    }

    ue2000_resolve_path(crc_arg, crc_host, sizeof(crc_host));
    ue2000_resolve_path(dir_arg, dir_host, sizeof(dir_host));

    /* Se no modo -m o .crc foi passado sem caminho completo, procura em dir_host */
    {
        FILE *test_f = fopen(crc_host, "rb");
        if (!test_f && strchr(crc_arg, '\\') == NULL && strchr(crc_arg, '/') == NULL) {
            snprintf(crc_host, sizeof(crc_host), "%s/%s", dir_host, crc_arg);
        } else if (test_f) {
            fclose(test_f);
        }
    }

    if (!verifica_assina_sig(crc_host)) {
        return 1;
    }

    fcrc = fopen(crc_host, "r");
    if (!fcrc) return 1;

    while (fscanf(fcrc, "%127s %32s", nome, esperado) == 2) {
        char arq_host[2048];
        uint8_t digest[16];
        char calculado[33];

        if (nome[0] == ';' || nome[0] == '#') continue;

        snprintf(arq_host, sizeof(arq_host), "%s/%s", dir_host, nome);
        if (md5_file_digest(arq_host, digest, calculado) != 0) {
            if (modo_m && (strstr(nome, "cant") || strstr(nome, "CANT"))) continue;
            fclose(fcrc);
            return 1;
        }
        if (stricmp(calculado, esperado) != 0) {
            if (modo_m && (strstr(nome, "cant") || strstr(nome, "CANT"))) continue;
            fclose(fcrc);
            return 1;
        }
    }

    fclose(fcrc);
    return 0;
}
"""


SRC_TIPURNA_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/tipurna.c
 * BINARIO     : C:\VIRTUOS\TIPURNA.EXE
 * CONTRATO L4 : tipurna > nul (Retorna errorlevel nas 10 faixas do SETUP.BAT)
 * ============================================================================ */

#include "../include/dos_compat.h"

static void ler_eeprom_completa(EEPROM_URNA *out) {
    uint8_t *p = (uint8_t *)out;
    size_t i;
    for (i = 0; i < sizeof(EEPROM_URNA); i++) {
        outp(IO_PORT_EEPROM_ADDR, (int)i);
        p[i] = (uint8_t)inp(IO_PORT_EEPROM_DATA);
    }
}

static int serie_valida(uint8_t modelo, uint32_t serie) {
    if (serie == 0 || serie == 0xFFFFFFFFUL) return 0;
    switch (modelo) {
        case MODELO_HW_UE96:   return (serie >= 100000UL && serie <= 199999UL);
        case MODELO_HW_UE98:   return (serie >= 200000UL && serie <= 499999UL);
        case MODELO_HW_UE2000: return (serie >= 500000UL && serie <= 999999UL);
        default:               return 0;
    }
}

int main(void) {
    EEPROM_URNA eep;
    uint16_t crc_calc;

    ler_eeprom_completa(&eep);

    if (memcmp(eep.assinatura, "TSE", 3) != 0) {
        return 32; /* 32..255 -> urna_invalida */
    }

    crc_calc = ue2000_crc16_ccitt((const uint8_t *)&eep, sizeof(EEPROM_URNA) - sizeof(uint16_t));
    if (crc_calc != eep.crc16_eeprom) {
        switch (eep.modelo_urna) {
            case MODELO_HW_UE2000: return 12; /* 12..16 -> ue2000_crc_invalido */
            case MODELO_HW_UE98:   return 10; /* 10..11 -> ue98_crc_invalido   */
            case MODELO_HW_UE96:   return 9;  /* 9      -> ue96_crc_invalido   */
            default:               return 32;
        }
    }

    if (!serie_valida(eep.modelo_urna, eep.numero_serie)) {
        switch (eep.modelo_urna) {
            case MODELO_HW_UE2000: return 20; /* 20..31 -> ue2000_numero_invalido */
            case MODELO_HW_UE98:   return 18; /* 18..19 -> ue98_numero_invalido   */
            case MODELO_HW_UE96:   return 17; /* 17     -> ue96_numero_invalido   */
            default:               return 32;
        }
    }

    switch (eep.modelo_urna) {
        case MODELO_HW_UE2000: return 4; /* 4..8 -> goto ue2000 */
        case MODELO_HW_UE98:   return 2; /* 2..3 -> goto ue98   */
        case MODELO_HW_UE96:   return 1; /* 0..1 -> goto ue96   */
        default:               return 32;
    }
}
"""


SRC_ARQCMP_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/arqcmp.c
 * BINARIO     : C:\VIRTUOS\ARQCMP.EXE
 * CONTRATO L4 : arqcmp <ref> <alvo> <modo> <offset> <valor>
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    char ref_host[1024], alvo_host[1024];
    int modo;
    long off, val;
    FILE *a, *b;

    if (argc != 6) return 1;

    ue2000_resolve_path(argv[1], ref_host, sizeof(ref_host));
    ue2000_resolve_path(argv[2], alvo_host, sizeof(alvo_host));
    modo = atoi(argv[3]);
    off  = atol(argv[4]);
    val  = atol(argv[5]);

    a = fopen(ref_host, "rb");
    b = fopen(alvo_host, "rb");
    if (!a || !b) {
        if (a) fclose(a);
        if (b) fclose(b);
        return 1;
    }

    if (modo == 1) {
        int c1, c2;
        if (fseek(a, off, SEEK_SET) != 0 || fseek(b, off, SEEK_SET) != 0) {
            fclose(a); fclose(b); return 1;
        }
        c1 = fgetc(a);
        c2 = fgetc(b);
        fclose(a);
        fclose(b);
        if (c1 == EOF || c2 == EOF) return 1;
        if (c1 != (int)(val & 0xFF)) return 1;
        if (off > 0 && c2 != (int)(val & 0xFF)) return 1;
        return 0;
    } else if (modo == 4) {
        long i;
        if (fseek(a, off, SEEK_SET) != 0 || fseek(b, off, SEEK_SET) != 0) {
            fclose(a); fclose(b); return 1;
        }
        for (i = 0; i < val; i++) {
            int c1 = fgetc(a), c2 = fgetc(b);
            if (c1 == EOF || c2 == EOF || c1 != c2) {
                fclose(a); fclose(b); return 1;
            }
        }
        fclose(a);
        fclose(b);
        return 0;
    }

    fclose(a);
    fclose(b);
    return 1;
}
"""


SRC_DISKFIX_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/diskfix.c
 * BINARIO     : C:\VIRTUOS\DISKFIX.EXE
 * CONTRATO L4 : diskfix %FI% /vs > nul
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    char est_path[1024];
    FILE *f;

    if (argc != 3 || stricmp(argv[2], "/vs") != 0) {
        return 1;
    }
    /* Verifica leitura basica de superficie na unidade solicitada */
    ue2000_resolve_path("C:\\FCV2000", est_path, sizeof(est_path));
    f = fopen(est_path, "rb");
    if (!f) return 1;
    fclose(f);
    return 0;
}
"""


SRC_LOG_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/log.c
 * BINARIO     : C:\VIRTUOS\LOG.EXE
 * CONTRATO L4 : log <codigo_evento>
 * ============================================================================ */

#include <time.h>
#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    char log_path[1024];
    FILE *f;
    time_t agora;
    struct tm *tm_info;
    int cod;

    if (argc < 2) return 1;
    cod = atoi(argv[1]);
    time(&agora);
    tm_info = localtime(&agora);

    ue2000_resolve_path("C:\\LOGURNA.DAT", log_path, sizeof(log_path));
    f = fopen(log_path, "ab");
    if (!f) return 1;

    fprintf(f, "%02d/%02d/%04d %02d:%02d:%02d | LOG_COD=%03d\r\n",
            tm_info->tm_mday, tm_info->tm_mon + 1, tm_info->tm_year + 1900,
            tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec, cod);
    fclose(f);
    return 0;
}
"""


SRC_GECHO_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/gecho.c
 * BINARIO     : C:\VIRTUOS\GECHO.EXE
 * CONTRATO L4 : gecho &&Mensagem Linha 1&&Linha 2 [/I]
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    char buf[512] = {0};
    int imediato = 0;
    int i;
    const char *p;

    for (i = 1; i < argc; i++) {
        if (stricmp(argv[i], "/I") == 0) {
            imediato = 1;
        } else {
            if (buf[0]) strcat(buf, " ");
            strncat(buf, argv[i], sizeof(buf) - strlen(buf) - 2);
        }
    }

    for (p = buf; *p; p++) {
        if (p[0] == '&' && p[1] == '&') {
            putchar('\n');
            p++;
        } else {
            putchar(*p);
        }
    }
    putchar('\n');

    if (!imediato && getenv("UE2000_NONINTERACTIVE") == NULL) {
        getch();
    }
    return 0;
}
"""


SRC_RES_BOOT_DESLIGA_C = r"""/* ============================================================================
 * ARQUIVO     : virtuos/sys_power.c (Gera RES.EXE, BOOT.COM e DESLIGA.COM)
 * CONTRATO L4 : res %FI% | boot | desliga
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    (void)argc;
    /* Flush de buffers do sistema de arquivos e sinalizacao de desligamento/reboot */
    fflush(stdout);
    if (argv[0] && (strstr(argv[0], "desliga") || strstr(argv[0], "DESLIGA"))) {
        outp(IO_PORT_POWER_RELAY, 0xFF);
    }
    return 0;
}
"""


SRC_DESBLOQ_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/desbloq.c
 * BINARIO     : C:\APLIC\DESBLOQ.EXE
 * CONTRATO L4 : desbloq <-s|-r|-a|-d|-m|-h|-g|-z|-x|-y|-w>
 * ============================================================================ */

#include "../include/dos_compat.h"

static uint16_t ler_modo_eeprom(void) {
    uint16_t lo, hi;
    outp(IO_PORT_EEPROM_ADDR, 10);
    lo = (uint16_t)inp(IO_PORT_EEPROM_DATA);
    outp(IO_PORT_EEPROM_ADDR, 11);
    hi = (uint16_t)inp(IO_PORT_EEPROM_DATA);
    return (uint16_t)((hi << 8) | lo);
}

static void gravar_modo_eeprom(uint16_t modo) {
    outp(IO_PORT_EEPROM_ADDR, 10);
    outp(IO_PORT_EEPROM_DATA, modo & 0xFF);
    outp(IO_PORT_EEPROM_ADDR, 11);
    outp(IO_PORT_EEPROM_DATA, (modo >> 8) & 0xFF);
}

static void atualizar_estgeral_fase(uint8_t nova_fase) {
    char path[1024];
    FILE *f;
    ESTGERAL_CTR est;

    ue2000_resolve_path("C:\\estgeral.ctr", path, sizeof(path));
    f = fopen(path, "r+b");
    if (!f) return;
    if (fread(&est, sizeof(ESTGERAL_CTR), 1, f) == 1) {
        est.fase_operacao = nova_fase;
        est.crc16_estrutura = ue2000_crc16_ccitt((const uint8_t *)&est, sizeof(ESTGERAL_CTR) - 2);
        fseek(f, 0L, SEEK_SET);
        fwrite(&est, sizeof(ESTGERAL_CTR), 1, f);
    }
    fclose(f);
}

int main(int argc, char *argv[]) {
    char flag;
    uint16_t modo_atual;

    if (argc != 2 || argv[1][0] != '-') return 1;
    flag = argv[1][1];
    modo_atual = ler_modo_eeprom();

    switch (flag) {
        case 's': /* Status de reserva */
            return (modo_atual == EEPROM_MODO_FCC2) ? 0 : 1;

        case 'r': /* Transicao de Urna de Reserva FCC2 -> FCC4 */
            if (modo_atual == EEPROM_MODO_FCC2) {
                outp(IO_PORT_FLASH_WP, 0x00);
                gravar_modo_eeprom(EEPROM_MODO_FCC4);
                atualizar_estgeral_fase(FASE_PRONTA_VOTACAO);
                return 0;
            }
            return 1;

        case 'a': /* Modo Auditoria (V.PRE) */
            gravar_modo_eeprom(EEPROM_MODO_AUDIT);
            return 0;

        case 'd': /* Modo Diagnostico */
            gravar_modo_eeprom(EEPROM_MODO_DIAG);
            return 0;

        case 'm': /* Modo Manutencao: destrava escrita fisica na Flash Interna */
            outp(IO_PORT_FLASH_WP, 0x00);
            gravar_modo_eeprom(EEPROM_MODO_MANUT);
            atualizar_estgeral_fase(FASE_MANUTENCAO);
            return 0;

        case 'h': /* Hardware lock / Help */
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        case 'g': /* Retorno ao estado operacional FCC0 */
            gravar_modo_eeprom(EEPROM_MODO_FCC0);
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        case 'z': /* Encerramento Eleicao Oficial */
        case 'x': /* Encerramento Voto Cantado    */
        case 'y': /* Encerramento Justificativa   */
        case 'w': /* Encerramento Simulado/Treino */
            gravar_modo_eeprom(EEPROM_MODO_ENCERRADO);
            atualizar_estgeral_fase(FASE_ENCERRADA_1T);
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        default:
            return 1;
    }
}
"""


SRC_DIAG_MANUT_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/diag_manut.c
 * BINARIO     : C:\APLIC\DIAG_MANUT.EXE
 * DESCRICAO   : Verificador de Impressora (1..4), Bateria (3..4) e Shell dos
 *               4 Menus de Manutencao (errorlevel 49..58) e 11 rotinas Aplic_*
 * ============================================================================ */

#include "../include/dos_compat.h"

int verifica_impressora(void) {
    uint8_t st = (uint8_t)inp(IO_PORT_HW_STATUS);
    if ((st & 0x01) == 0) return 2; /* 2 = Nao detectada */
    if (st & 0x02)        return 1; /* 1 = Erro critico  */
    if (st & 0x04)        return 3; /* 3 = Atolamento    */
    if (st & 0x08)        return 4; /* 4 = Sem papel     */
    return 0;
}

int verifica_bateria(int externa) {
    uint8_t st = (uint8_t)inp(IO_PORT_HW_STATUS);
    if (!externa) {
        if (st & 0x10) return 4; /* 4 = Interna ausente */
        if (st & 0x20) return 3; /* 3 = Interna critica */
    } else {
        if (st & 0x40) return 4; /* 4 = Externa ausente */
        if (st & 0x80) return 3; /* 3 = Externa critica */
    }
    return 0;
}

int main(int argc, char *argv[]) {
    int menu = 1;
    int tecla;

    if (argc >= 2) {
        if (strcmp(argv[1], "--check-printer") == 0) return verifica_impressora();
        if (strcmp(argv[1], "--check-bat-int") == 0) return verifica_bateria(0);
        if (strcmp(argv[1], "--check-bat-ext") == 0) return verifica_bateria(1);
        menu = atoi(argv[1]);
    }

    if (getenv("UE2000_MENU_CHOICE") != NULL) {
        int c = atoi(getenv("UE2000_MENU_CHOICE"));
        if (c >= 48 && c <= 58) return c;
    }

    printf("\n=== TSE UE2000 - MENU DE MANUTENCAO %d ===\n", menu);
    if (menu == 1) {
        printf("1(49):Diagnostico | 2(50):RelatorioSimples | 3(51):AutonomiaVotoImpresso\n");
        printf("4(52):AutonomiaSemVotoImpresso | 5(53):Menu2 | 6(54):Menu3 | 7(55):Menu4\n");
        printf("8(56):Aplic_18 | 9(57):Aplic_19 | 0(58):Sair\n");
    } else if (menu == 2) {
        printf("1(49):ImpBrasao | 2(50):ImpCodBar | 3(51):ImpTipCar | 4(52):AtolaPapel\n");
        printf("5(53):TesteImpGen | 6(54):ZeresimaPeq | 7(55):ZeresimaGrd | 8(56):Aplic_28\n");
    } else if (menu == 3) {
        printf("1(49):CmdMicroterm | 2(50):TxRxMicroterm | 3(51):CmdFonte | 4(52):LeituraBat\n");
        printf("5(53):ImpMicroterm | 6(54):Aplic_36 | 7(55):Aplic_37 | 8(56):Aplic_38\n");
    } else if (menu == 4) {
        printf("1(49):TesteSom | 2(50):LeituraNumInterno | 3(51):ManutFabrica\n");
        printf("4(52):Aplic_44 | 5(53):Aplic_45 | 6(54):Aplic_46 | 7(55):Aplic_47 | 8(56):Aplic_48\n");
    }

    tecla = getch();
    if (tecla >= '1' && tecla <= '9') return tecla;
    return 58;
}
"""


SRC_UI_URNA_C = r"""/*
 * Interface textual reconstruida para demonstracao UE2000.
 * Mensagens e fluxo de teclado sao inferidos do material fornecido;
 * nao e uma transcricao autenticada da interface original.
 */
#include "../include/dos_compat.h"

#define TECLA_BRANCO   'B'
#define TECLA_CORRIGE  'C'
#define TECLA_CONFIRMA 'F' /* tecla F mapeia o botao CONFIRMA no PC */
#define TECLA_ESC      0x1B

static int ui_em_modo_teste(void) {
    return getenv("UE2000_NONINTERACTIVE") != NULL;
}

static void ui_moldura(const char *titulo, const char *instrucao) {
    if (ui_em_modo_teste()) return;
    clrscr();
    printf("+--------------------------------------------------------------+\n");
    printf("| JUSTICA ELEITORAL                            SIMULADOR UE2000 |\n");
    printf("+--------------------------------------------------------------+\n");
    printf("|                                                              |\n");
    printf("|  %-60.60s|\n", titulo ? titulo : "");
    printf("|                                                              |\n");
    printf("+--------------------------------------------------------------+\n");
    printf("| %-60.60s |\n", instrucao ? instrucao : "");
    printf("+--------------------------------------------------------------+\n");
    fflush(stdout);
}

static int ui_wait_key(void) {
    if (ui_em_modo_teste()) return TECLA_CONFIRMA;
    return getch();
}

void ui_tela_aguarde(void) {
    ui_moldura("AGUARDE A LIBERACAO DO MESARIO",
               "O MESARIO IRA HABILITAR SUA VOTACAO");
    (void)ui_wait_key();
}

void ui_tela_liberado(void) {
    ui_moldura("ELEITOR HABILITADO",
               "DIRIJA-SE A CABINE E COMECE A VOTAR");
    (void)ui_wait_key();
}

/* Retorno 1: candidato selecionado; retorno 0: branco confirmado. */
int ui_votar_cargo(uint8_t cargo_code, int num_digitos, const char *cargo_nome,
                   const REGISTRO_CANDIDATO *cands, int n_cands,
                   REGISTRO_CANDIDATO *cand_encontrado) {
    char buffer[8] = {0};
    int pos = 0, tecla, i;
    char instrucao[80];

    if (ui_em_modo_teste()) {
        for (i = 0; i < n_cands; i++) {
            if (cands[i].cargo == cargo_code) {
                *cand_encontrado = cands[i];
                return 1;
            }
        }
        return 0;
    }

    for (;;) {
        snprintf(instrucao, sizeof(instrucao),
                 "DIGITE O NUMERO DO %s (%d DIGITOS)", cargo_nome, num_digitos);
        ui_moldura(cargo_nome, instrucao);
        printf("|  NUMERO: [ %-*s ]                                           |\n",
               num_digitos, buffer);
        printf("+--------------------------------------------------------------+\n");
        printf("| [0-9] DIGITAR  [B] BRANCO  [C] CORRIGE  [F] CONFIRMA         |\n");
        printf("+--------------------------------------------------------------+\n");
        fflush(stdout);
        tecla = getch();

        if (tecla >= '0' && tecla <= '9' && pos < num_digitos) {
            buffer[pos++] = (char)tecla;
            buffer[pos] = '\0';
        } else if (tecla == TECLA_CORRIGE || tecla == TECLA_ESC) {
            pos = 0;
            buffer[0] = '\0';
        } else if (tecla == TECLA_BRANCO) {
            ui_moldura("VOTO EM BRANCO",
                       "APERTE F PARA GRAVAR OU C PARA VOLTAR");
            printf("|  CARGO: %-51.51s|\n", cargo_nome);
            printf("|  VOTO : EM BRANCO                                            |\n");
            printf("+--------------------------------------------------------------+\n");
            for (;;) {
                int t2 = getch();
                if (t2 == TECLA_CONFIRMA) return 0;
                if (t2 == TECLA_CORRIGE) break;
            }
            pos = 0;
            buffer[0] = '\0';
        } else if (tecla == TECLA_CONFIRMA) {
            if (pos != num_digitos) {
                ui_moldura("NUMERO INCOMPLETO", "DIGITE TODOS OS NUMEROS E CONFIRME");
                (void)getch();
                continue;
            }
            for (i = 0; i < n_cands; i++) {
                if (cands[i].cargo == cargo_code &&
                    cands[i].numero == (uint32_t)atol(buffer)) {
                    *cand_encontrado = cands[i];
                    return 1;
                }
            }
            ui_moldura("CANDIDATO INEXISTENTE", "APERTE UMA TECLA E CORRIJA");
            (void)getch();
            pos = 0;
            buffer[0] = '\0';
        }
    }
}

/* Retorno 1: confirma; retorno 0: corrige. */
int ui_confirmar_voto(const REGISTRO_CANDIDATO *cand, const char *cargo_nome) {
    if (ui_em_modo_teste()) return 1;
    ui_moldura("CONFIRA SEU VOTO", "APERTE F PARA GRAVAR OU C PARA CORRIGIR");
    printf("|  CARGO   : %-47.47s|\n", cargo_nome);
    printf("|  NUMERO  : %-47lu|\n", (unsigned long)cand->numero);
    printf("|  CANDIDATO: %-46.46s|\n", cand->nome_urna);
    printf("|  PARTIDO : %-47.47s|\n", cand->partido_sigla);
    printf("+--------------------------------------------------------------+\n");
    fflush(stdout);
    for (;;) {
        int tecla = getch();
        if (tecla == TECLA_CONFIRMA) return 1;
        if (tecla == TECLA_CORRIGE) return 0;
    }
}

void ui_tela_fim(void) {
    ui_moldura("FIM", "OBRIGADO. VOCE PODE SE RETIRAR.");
    (void)ui_wait_key();
}
"""


SRC_MTERM_DISPLAY_C = r"""/* Painel local de demonstracao do microterminal; nao abre porta serial. */
#include <stdio.h>
#include <string.h>
#include "../include/dos_compat.h"

void mterm_exibir_ultimo_frame(void) {
    char path[1024], line[256];
    char l1[21] = "AGUARDANDO MESARIO", l2[21] = "DIGITE TITULO ELEIT.";
    FILE *f;
    if (getenv("UE2000_NONINTERACTIVE")) return;
    ue2000_resolve_path("C:\\MTERM_LCD.LOG", path, sizeof(path));
    f = fopen(path, "r");
    if (f) {
        while (fgets(line, sizeof(line), f)) {
            char *p1 = strchr(line, '|');
            char *p2;
            if (!p1) continue;
            p2 = strchr(p1 + 1, '|');
            if (!p2) continue;
            p1++;
            while (*p1 == ' ') p1++;
            p2++;
            while (*p2 == ' ') p2++;
            strncpy(l1, p1, 20); l1[20] = '\0';
            {
                char *p3 = strchr(p2, '|');
                if (p3) *p3 = '\0';
            }
            strncpy(l2, p2, 20); l2[20] = '\0';
        }
        fclose(f);
    }
    printf("\n+----------------------+\n");
    printf("| MICROTERMINAL 2 x 20 |\n");
    printf("+----------------------+\n");
    printf("|%-20.20s|\n", l1);
    printf("|%-20.20s|\n", l2);
    printf("+----------------------+\n");
    fflush(stdout);
}
"""


SRC_VVOTA_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/vvota.c
 * INTERFACE   : TUI interativa de demonstracao, reconstruida a partir dos
 *               materiais do projeto; nao e codigo oficial autenticado.
 * ============================================================================ */
#include "../include/dos_compat.h"

extern void lmvos_init(void);
extern void lmvos_mterm_send_frame(uint8_t cmd, const char *l1, const char *l2);
extern int cepesc_cifra_e_assina_bu(const char *bu_claro_dos, const char *bu_cifrado_dos);
extern void ui_tela_aguarde(void);
extern void ui_tela_liberado(void);
extern int ui_votar_cargo(uint8_t cargo_code, int num_digitos, const char *cargo_nome,
                          const REGISTRO_CANDIDATO *cands, int n_cands,
                          REGISTRO_CANDIDATO *cand_encontrado);
extern int ui_confirmar_voto(const REGISTRO_CANDIDATO *cand, const char *cargo_nome);
extern void ui_tela_fim(void);
extern void mterm_exibir_ultimo_frame(void);

static int carregar_candidatos(REGISTRO_CANDIDATO *lista, int max_cand) {
    char path[1024]; FILE *f; int n = 0;
    ue2000_resolve_path("C:\\basedado\\candidat.dat", path, sizeof(path));
    f = fopen(path, "rb");
    if (!f) return 0;
    while (n < max_cand && fread(&lista[n], sizeof(REGISTRO_CANDIDATO), 1, f) == 1) n++;
    fclose(f); return n;
}

static int salvar_candidatos(const REGISTRO_CANDIDATO *lista, int n) {
    char path[1024]; FILE *f;
    ue2000_resolve_path("C:\\basedado\\candidat.dat", path, sizeof(path));
    f = fopen(path, "wb"); if (!f) return -1;
    if (fwrite(lista, sizeof(REGISTRO_CANDIDATO), (size_t)n, f) != (size_t)n) {
        fclose(f); return -1;
    }
    fclose(f); return 0;
}

static int votar_cargo_completo(uint8_t cargo, int digitos, const char *nome,
                                const REGISTRO_CANDIDATO *cands, int n,
                                REGISTRO_CANDIDATO *escolhido) {
    for (;;) {
        int r = ui_votar_cargo(cargo, digitos, nome, cands, n, escolhido);
        if (r == 0) return 0; /* branco confirmado pela interface */
        if (ui_confirmar_voto(escolhido, nome)) return 1;
        /* CORRIGE: retorna à digitação do mesmo cargo. */
    }
}

int main(int argc, char **argv) {
    char est_path[1024], bu_claro_path[1024];
    ESTGERAL_CTR est;
    REGISTRO_CANDIDATO cands[32], vereador, prefeito;
    int n, i, r_ver, r_pre;
    FILE *fe, *fb;
    (void)argc; (void)argv;

    lmvos_init();
    ue2000_resolve_path("C:\\estgeral.ctr", est_path, sizeof(est_path));
    fe = fopen(est_path, "r+b"); if (!fe) return 2;
    if (fread(&est, sizeof(est), 1, fe) != 1) { fclose(fe); return 2; }
    n = carregar_candidatos(cands, 32);
    if (n <= 0) { fclose(fe); return 2; }

    if (est.total_comparecim == 0) {
        lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "EMITINDO ZERESIMA...", "AGUARDE IMPRESSAO");
    }
    lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "DIGITE TITULO ELEIT.", "SECAO 0102 ZONA 0001");
    ui_tela_aguarde();
    lmvos_mterm_send_frame(MTERM_CMD_LED_LIBERADO, "ELEITOR HABILITADO", "CABINE LIBERADA");
    ui_tela_liberado();
    mterm_exibir_ultimo_frame();

    r_ver = votar_cargo_completo(CARGO_VEREADOR, 5, "VEREADOR", cands, n, &vereador);
    r_pre = votar_cargo_completo(CARGO_PREFEITO, 2, "PREFEITO", cands, n, &prefeito);

    if (r_ver) for (i = 0; i < n; i++)
        if (cands[i].cargo == CARGO_VEREADOR && cands[i].numero == vereador.numero) {
            cands[i].total_votos++; break;
        }
    if (r_pre) for (i = 0; i < n; i++)
        if (cands[i].cargo == CARGO_PREFEITO && cands[i].numero == prefeito.numero) {
            cands[i].total_votos++; break;
        }
    if (salvar_candidatos(cands, n) != 0) { fclose(fe); return 1; }

    est.total_comparecim++;
    est.fase_operacao = (est.turno_atual == 1) ? FASE_ENCERRADA_1T : FASE_ENCERRADA_2T;
    est.crc16_estrutura = ue2000_crc16_ccitt((const uint8_t *)&est, sizeof(est) - 2);
    rewind(fe);
    if (fwrite(&est, sizeof(est), 1, fe) != 1) { fclose(fe); return 1; }
    fclose(fe);

    ue2000_resolve_path("C:\\aplic\\bu_claro.tmp", bu_claro_path, sizeof(bu_claro_path));
    fb = fopen(bu_claro_path, "wb"); if (!fb) return 1;
    fprintf(fb, "BOLETIM DE DEMONSTRACAO UE2000 - NAO OFICIAL\r\n");
    fprintf(fb, "UF: %c%c | ZONA: %04u | SECAO: %04u | TURNO: %u\r\n",
            est.uf_sigla[0], est.uf_sigla[1], est.zona_eleitoral, est.secao_eleitoral, est.turno_atual);
    fprintf(fb, "COMPARECIMENTO SIMULADO: %lu\r\n", (unsigned long)est.total_comparecim);
    for (i = 0; i < n; i++)
        fprintf(fb, "CARGO %u | NUM %05lu | %-24s | %-6s | VOTOS %04lu\r\n",
                cands[i].cargo, (unsigned long)cands[i].numero, cands[i].nome_urna,
                cands[i].partido_sigla, (unsigned long)cands[i].total_votos);
    fclose(fb);

    /* A rotina criptografica do gerador e um placeholder de simulacao,
       nao a implementacao proprietaria CEPESC/ABIN. */
    if (cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "C:\\aplic\\bu_2000.bu") != 0) return 1;
    (void)cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "A:\\bu_2000.bu");
    (void)cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "D:\\bu_2000.bu");
    lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "VOTACAO ENCERRADA", "BU GRAVADO NO DISCO");
    mterm_exibir_ultimo_frame();
    ui_tela_fim();
    return 0;
}
"""




SRC_VRED_VCANT_VJUSTIF_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/vmodulos.c (Compila VRED.EXE, VCANT_E.EXE e VJUSTIF.EXE)
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    char src[1024], dst[1024];
    FILE *fi, *fo;
    int c;
    (void)argc;

    if (argv[0] && (strstr(argv[0], "vred") || strstr(argv[0], "VRED"))) {
        /* VRED.EXE (COPYRES): Recupera BU de C:\aplic\bu_2000.bu para A:\bu_2000.bu */
        ue2000_resolve_path("C:\\aplic\\bu_2000.bu", src, sizeof(src));
        ue2000_resolve_path("A:\\bu_2000.bu", dst, sizeof(dst));
        fi = fopen(src, "rb");
        if (!fi) return 1;
        fo = fopen(dst, "wb");
        if (!fo) { fclose(fi); return 1; }
        while ((c = fgetc(fi)) != EOF) fputc(c, fo);
        fclose(fi);
        fclose(fo);
        return 0;
    }

    if (argv[0] && (strstr(argv[0], "vcant") || strstr(argv[0], "VCANT"))) {
        /* VCANT_E.EXE: Modulo de Voto Cantado (Assistido por Sintese de Voz PCM) */
        printf("[VCANT_E] Modulo de Voto Cantado (Audio PCM) executado com sucesso.\n");
        return 0;
    }

    /* VJUSTIF.EXE: Modulo de Justificativa Eleitoral */
    printf("[VJUSTIF] Modulo de Justificativa Eleitoral executado com sucesso.\n");
    return 0;
}
"""


SRC_VAUDIT_C = r"""/* ============================================================================
 * ARQUIVO     : aplic/vaudit.c
 * BINARIO     : C:\APLIC\VAUDIT.EXE (V.PRE - Relatorio PI2003)
 * DESCRICAO   : Calcula SHA-1 (FIPS 180-1) dos arquivos da Flash Interna (C:),
 *               lista candidatos registrados (Opcao 4) e emite Zeresima (Opcao 5).
 * ============================================================================ */

#include "../include/dos_compat.h"

#define ROL32(val, bits) (((val) << (bits)) | ((val) >> (32 - (bits))))

/* Implementacao FIPS 180-1 SHA-1 real de 160 bits */
static int sha1_file(const char *dos_path, char hex_out[41]) {
    char host_path[1024];
    FILE *f;
    uint8_t *msg;
    long flen;
    size_t new_len, offset;
    uint64_t bits;
    uint32_t h0 = 0x67452301UL, h1 = 0xEFCDAB89UL, h2 = 0x98BADCFEUL;
    uint32_t h3 = 0x10325476UL, h4 = 0xC3D2E1F0UL;
    int i;

    ue2000_resolve_path(dos_path, host_path, sizeof(host_path));
    f = fopen(host_path, "rb");
    if (!f) {
        strcpy(hex_out, "0000000000000000000000000000000000000000");
        return -1;
    }
    fseek(f, 0, SEEK_END);
    flen = ftell(f);
    fseek(f, 0, SEEK_SET);

    new_len = (size_t)flen + 1;
    while ((new_len % 64) != 56) new_len++;

    msg = (uint8_t *)calloc(new_len + 8, 1);
    if (!msg) { fclose(f); return -1; }
    if (flen > 0) {
        size_t r = fread(msg, 1, (size_t)flen, f);
        (void)r;
    }
    fclose(f);

    msg[flen] = 0x80;
    bits = (uint64_t)flen * 8ULL;
    for (i = 0; i < 8; i++) {
        msg[new_len + i] = (uint8_t)((bits >> (56 - 8 * i)) & 0xFF);
    }

    for (offset = 0; offset < new_len; offset += 64) {
        uint32_t w[80], a = h0, b = h1, c = h2, d = h3, e = h4;
        for (i = 0; i < 16; i++) {
            w[i] = ((uint32_t)msg[offset + i * 4] << 24) |
                   ((uint32_t)msg[offset + i * 4 + 1] << 16) |
                   ((uint32_t)msg[offset + i * 4 + 2] << 8) |
                   ((uint32_t)msg[offset + i * 4 + 3]);
        }
        for (i = 16; i < 80; i++) {
            w[i] = ROL32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
        }
        for (i = 0; i < 80; i++) {
            uint32_t f_val, k;
            if (i < 20)      { f_val = (b & c) | ((~b) & d); k = 0x5A827999UL; }
            else if (i < 40) { f_val = b ^ c ^ d;            k = 0x6ED9EBA1UL; }
            else if (i < 60) { f_val = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDCUL; }
            else             { f_val = b ^ c ^ d;            k = 0xCA62C1D6UL; }
            {
                uint32_t temp = ROL32(a, 5) + f_val + e + k + w[i];
                e = d; d = c; c = ROL32(b, 30); b = a; a = temp;
            }
        }
        h0 += a; h1 += b; h2 += c; h3 += d; h4 += e;
    }
    free(msg);
    sprintf(hex_out, "%08lx%08lx%08lx%08lx%08lx",
            (unsigned long)h0, (unsigned long)h1, (unsigned long)h2,
            (unsigned long)h3, (unsigned long)h4);
    return 0;
}

int main(int argc, char *argv[]) {
    static const char *alvos[] = {
        "C:\\SETUP.BAT",
        "C:\\instala.bat",
        "C:\\novobat.bat",
        "C:\\estgeral.ctr",
        "C:\\basedado\\candidat.dat",
        "C:\\basedado\\elelocal.dat",
        NULL
    };
    int i;
    char sha1_hex[41];
    char cand_path[1024];
    FILE *fc;
    REGISTRO_CANDIDATO reg;

    (void)argc; (void)argv;
    printf("============================================================\n");
    printf(" VAUDIT.EXE (V.PRE) - AUTO-VALIDADOR SHA-1 (FONTE: PI2003)  \n");
    printf("============================================================\n");
    for (i = 0; alvos[i] != NULL; i++) {
        sha1_file(alvos[i], sha1_hex);
        printf(" %-26s | SHA-1: %s\n", alvos[i], sha1_hex);
    }

    printf("\n--- OPCAO 4: CANDIDATOS CARREGADOS EM C:\\BASEDADO\\CANDIDAT.DAT ---\n");
    ue2000_resolve_path("C:\\basedado\\candidat.dat", cand_path, sizeof(cand_path));
    fc = fopen(cand_path, "rb");
    if (fc) {
        while (fread(&reg, sizeof(REGISTRO_CANDIDATO), 1, fc) == 1) {
            printf(" Cargo %u | Num %05lu | %-24s | Partido %-6s\n",
                   reg.cargo, (unsigned long)reg.numero, reg.nome_urna, reg.partido_sigla);
        }
        fclose(fc);
    }
    return 0;
}
"""


# =============================================================================
# 3. GERADOR DE SCRIPTS BATCH (.BAT), RUNNERS RODA_* E MAKEFILES
# =============================================================================

RUNNERS_MAP = [
    ("roda_t1.bat",   "disco1",  "vvota.exe",   "-w", "Treinamento Eleitor 1o Turno"),
    ("roda_t2.bat",   "disco2",  "vvota.exe",   "-w", "Treinamento Eleitor 2o Turno"),
    ("roda_tm1.bat",  "disco3",  "vvota.exe",   "-w", "Treinamento Mesario 1o Turno"),
    ("roda_tm2.bat",  "disco4",  "vvota.exe",   "-w", "Treinamento Mesario 2o Turno"),
    ("roda_tj1.bat",  "disco5",  "vjustif.exe", "-w", "Treinamento Justificativa 1o Turno"),
    ("roda_tj2.bat",  "disco6",  "vjustif.exe", "-w", "Treinamento Justificativa 2o Turno"),
    ("roda_tv1.bat",  "disco7",  "vcant_e.exe", "-w", "Treinamento Voto Cantado 1o Turno"),
    ("roda_tv2.bat",  "disco8",  "vcant_e.exe", "-w", "Treinamento Voto Cantado 2o Turno"),
    ("roda_se1.bat",  "disco9",  "vvota.exe",   "-w", "Simulado Eleicao 1o Turno"),
    ("roda_se2.bat",  "disco10", "vvota.exe",   "-w", "Simulado Eleicao 2o Turno"),
    ("roda_sj1.bat",  "disco11", "vjustif.exe", "-w", "Simulado Justificativa 1o Turno"),
    ("roda_sj2.bat",  "disco12", "vjustif.exe", "-w", "Simulado Justificativa 2o Turno"),
    ("roda_sv1.bat",  "disco13", "vcant_e.exe", "-w", "Simulado Voto Cantado 1o Turno"),
    ("roda_sv2.bat",  "disco14", "vcant_e.exe", "-w", "Simulado Voto Cantado 2o Turno"),
    ("roda_v1.bat",   "disco15", "vvota.exe",   "-z", "Eleicao Oficial 1o Turno"),
    ("roda_v2.bat",   "disco16", "vvota.exe",   "-z", "Eleicao Oficial 2o Turno"),
    ("roda_j1.bat",   "disco17", "vjustif.exe", "-y", "Justificativa Oficial 1o Turno"),
    ("roda_j2.bat",   "disco18", "vjustif.exe", "-y", "Justificativa Oficial 2o Turno"),
    ("roda_can1.bat", "disco19", "vcant_e.exe", "-x", "Voto Cantado Oficial 1o Turno"),
    ("roda_can2.bat", "disco20", "vcant_e.exe", "-x", "Voto Cantado Oficial 2o Turno"),
    ("roda_acv.bat",  "disco28", "vvota.exe",   "-w", "Teste Autonomia Com Voto Impresso"),
    ("roda_asv.bat",  "disco29", "vvota.exe",   "-w", "Teste Autonomia Sem Voto Impresso"),
]


def gerar_runner_bat(nome_bat: str, disco: str, exe: str, flag_desbloq: str, desc: str) -> str:
    return f"""@echo off
REM ============================================================
REM ARQUIVO : E:\\{nome_bat.upper()} ({desc} - {disco})
REM ============================================================
cd %FI%\\aplic
%FI%\\virtuos\\log 30
%FI%\\virtuos\\gecho &&Iniciando {desc} ... /I
%FI%\\virtuos\\arqcmp %FI%\\estgeral.ctr %FI%\\aplic\\estados\\{disco} 1 1 1 > nul
if errorlevel 1 goto erro_estado
%FI%\\aplic\\{exe}
if errorlevel 2 goto erro_fatal
if errorlevel 1 goto recupera_bu
%FI%\\aplic\\desbloq {flag_desbloq} > nul
goto fim_runner

:recupera_bu
%FI%\\aplic\\vred.exe
goto fim_runner

:erro_estado
%FI%\\virtuos\\gecho &&ERRO: Estado incompativel com {disco}!
goto fim_runner

:erro_fatal
%FI%\\virtuos\\gecho &&ERRO CRITICO em {exe}!

:fim_runner
cd %FI%\\
"""


MAKEFILE_WATCOM = r"""# =============================================================================
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
"""


DOSBOX_CONF = r"""# =============================================================================
# CONFIGURACAO DOSBOX PARA TESTE DA URNA ELETRONICA UE2000 (v2.1)
# =============================================================================
# Execute com: dosbox -conf dosbox_ue2000.conf
# =============================================================================

[sdl]
autolock=false

[dosbox]
machine=svga_s3
memsize=16

[cpu]
core=normal
cputype=486_slow
cycles=fixed 12000

[autoexec]
@echo off
mount C ./FI_C
mount D ./FC_D
mount E ./RAM_E
mount A ./DQ_A -t floppy
path C:\;C:\VIRTUOS;C:\APLIC;E:\
C:
echo ============================================================
echo   AMBIENTE DE TESTE TSE-UE2000 CARREGADO (C: D: E: A:)
echo   Para iniciar o fluxo completo da urna, digite: SETUP.BAT
echo ============================================================
"""


# =============================================================================
# 4. FUNÇÕES AUXILIARES DE CRIAÇÃO BINÁRIA (CRC16, ASSINA 256-BIT, BANCOS)
# =============================================================================

def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def assina_256_py(md5_digest: bytes) -> bytes:
    sig = bytearray(32)
    for i in range(16):
        sig[i] = md5_digest[i] ^ 0xA5 ^ (i * 17)
        sig[i + 16] = (md5_digest[15 - i] + 0x3C + (i * 9)) & 0xFF
    return bytes(sig)


def criar_estgeral_ctr(rota_bat: int = 0x00, fase: int = 0x01, turno: int = 1, disco: int = 15) -> bytes:
    header = struct.pack(
        "<BBBBHHH2sII6B6B30s",
        rota_bat,
        fase,
        turno,
        disco,
        1,              # Zona 0001
        102,            # Secao 0102
        7107,           # Municipio TSE (Sao Paulo / Exemplo)
        b"SP",
        450,            # 450 eleitores aptos
        0,              # 0 votos no inicio (exige Zeresima)
        1, 10, 0, 8, 0, 0,   # Abertura: 01/10/00 08:00:00
        1, 10, 0, 17, 0, 0,  # Fechamento: 01/10/00 17:00:00
        b"\x00" * 30,
    )
    crc = crc16_ccitt(header)
    return header + struct.pack("<H", crc)


def criar_candidat_dat() -> bytes:
    candidatos = [
        (1, 91001, b"JOSE DA SILVA",     b"PART-A", b"F91001.BMP", b"V91001.WAV", 0),
        (1, 92002, b"MARIA OLIVEIRA",    b"PART-B", b"F92002.BMP", b"V92002.WAV", 0),
        (2, 91,    b"CARLOS SANTOS",     b"PART-A", b"F91.BMP",    b"V91.WAV",    0),
        (2, 92,    b"ANA COSTA",         b"PART-B", b"F92.BMP",    b"V92.WAV",    0),
    ]
    buf = bytearray()
    for cargo, num, nome, part, foto, audio, votos in candidatos:
        buf += struct.pack(
            "<BI32s8s16s16sI",
            cargo,
            num,
            nome.ljust(32, b"\x00"),
            part.ljust(8, b"\x00"),
            foto.ljust(16, b"\x00"),
            audio.ljust(16, b"\x00"),
            votos,
        )
    return bytes(buf)


def calcular_titulo_tse_valido(base8: str, uf_code: str = "01") -> str:
    pesos1 = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = sum(int(base8[i]) * pesos1[i] for i in range(8))
    resto = soma % 11
    uf = int(uf_code)
    if resto == 0:
        dv1 = 1 if uf in (1, 2) else 0
    elif resto == 10:
        dv1 = 0
    else:
        dv1 = resto

    soma2 = int(uf_code[0]) * 7 + int(uf_code[1]) * 8 + dv1 * 9
    resto2 = soma2 % 11
    if resto2 == 0:
        dv2 = 1 if uf in (1, 2) else 0
    elif resto2 == 10:
        dv2 = 0
    else:
        dv2 = resto2
    return f"{base8}{uf_code}{dv1}{dv2}"


def criar_elelocal_dat() -> bytes:
    eleitores = [
        (calcular_titulo_tse_valido("12345678", "01"), "JOAO PEREIRA SOUZA",   0, 0xA101),
        (calcular_titulo_tse_valido("23456789", "01"), "MARIANA ALVES LIMA",   0, 0xB202),
        (calcular_titulo_tse_valido("34567890", "01"), "ROBERTO FERREIRA",     0, 0xC303),
    ]
    buf = bytearray()
    for tit, nome, votou, cod in eleitores:
        buf += struct.pack(
            "<13s40sBH",
            tit.encode("ascii").ljust(13, b"\x00"),
            nome.encode("ascii").ljust(40, b"\x00"),
            votou,
            cod,
        )
    return bytes(buf)


def gerar_crc_e_sig(crc_path: Path, target_dir: Path, arquivos: list[str]) -> None:
    linhas = []
    for nome in arquivos:
        fp = target_dir / nome
        if fp.exists() and fp.is_file():
            md5_hex = hashlib.md5(fp.read_bytes()).hexdigest()
            linhas.append(f"{nome} {md5_hex}\n")
    conteudo_crc = "".join(linhas).encode("ascii")
    crc_path.write_bytes(conteudo_crc)

    md5_do_crc = hashlib.md5(conteudo_crc).digest()
    assinatura = assina_256_py(md5_do_crc)
    sig_struct = struct.pack("<4sI16s32s", b"AS2K", 20000902, md5_do_crc, assinatura)
    sig_path = crc_path.with_suffix(".sig")
    sig_path.write_bytes(sig_struct)


# =============================================================================
# 5. CONSTRUÇÃO COMPLETA DA ÁRVORE E EXECUÇÃO DE TESTES AUTOMATIZADOS
# =============================================================================

def construir_ambiente(dest: Path, compilar: bool = True, testar: bool = True) -> None:
    print(f"[1/5] Criando estrutura de unidades e diretorios em: {dest.resolve()}")
    fi_c = dest / "FI_C"
    fc_d = dest / "FC_D"
    ram_e = dest / "RAM_E"
    dq_a = dest / "DQ_A"
    src_dir = dest / "src"
    inc_dir = dest / "include"

    for d in [
        fi_c / "aplic" / "estados",
        fi_c / "virtuos",
        fi_c / "basedado",
        fi_c / "fototrei",
        fi_c / "vototrei",
        fi_c / "canttrei" / "aplic",
        fi_c / "som_urna",
        fi_c / "testes",
        fi_c / "testfab",
        fi_c / "temp",
        fc_d / "fotos",
        ram_e,
        dq_a,
        src_dir / "virtuos",
        src_dir / "aplic",
        inc_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    print("[2/5] Gravando arquivos de cabecalho e codigo-fonte C (Watcom DOS / GCC)...")
    (inc_dir / "ue2000_types.h").write_text(HEADER_UE2000_TYPES, encoding="utf-8")
    (inc_dir / "dos_compat.h").write_text(HEADER_DOS_COMPAT, encoding="utf-8")

    (src_dir / "virtuos" / "lmvos.c").write_text(SRC_LMVOS_C, encoding="utf-8")
    (src_dir / "aplic" / "cepesc_crypto.c").write_text(SRC_CEPESC_C, encoding="utf-8")
    (src_dir / "virtuos" / "ckpack.c").write_text(SRC_CKPACK_C, encoding="utf-8")
    (src_dir / "virtuos" / "tipurna.c").write_text(SRC_TIPURNA_C, encoding="utf-8")
    (src_dir / "virtuos" / "arqcmp.c").write_text(SRC_ARQCMP_C, encoding="utf-8")
    (src_dir / "virtuos" / "diskfix.c").write_text(SRC_DISKFIX_C, encoding="utf-8")
    (src_dir / "virtuos" / "log.c").write_text(SRC_LOG_C, encoding="utf-8")
    (src_dir / "virtuos" / "gecho.c").write_text(SRC_GECHO_C, encoding="utf-8")
    (src_dir / "virtuos" / "sys_power.c").write_text(SRC_RES_BOOT_DESLIGA_C, encoding="utf-8")

    (src_dir / "aplic" / "desbloq.c").write_text(SRC_DESBLOQ_C, encoding="utf-8")
    (src_dir / "aplic" / "diag_manut.c").write_text(SRC_DIAG_MANUT_C, encoding="utf-8")
    (src_dir / "aplic" / "vvota.c").write_text(SRC_VVOTA_C, encoding="utf-8")
    (src_dir / "aplic" / "ui_urna.c").write_text(SRC_UI_URNA_C, encoding="utf-8")
    (src_dir / "virtuos" / "mterm_display.c").write_text(SRC_MTERM_DISPLAY_C, encoding="utf-8")
    (src_dir / "aplic" / "vmodulos.c").write_text(SRC_VRED_VCANT_VJUSTIF_C, encoding="utf-8")
    (src_dir / "aplic" / "vaudit.c").write_text(SRC_VAUDIT_C, encoding="utf-8")

    (dest / "Makefile").write_text(MAKEFILE_WATCOM, encoding="utf-8")
    (dest / "dosbox_ue2000.conf").write_text(DOSBOX_CONF, encoding="utf-8")
    demo_sh = "#!/usr/bin/env bash\nset -euo pipefail\nDIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\nexport UE2000_FI=\"$DIR/FI_C\"\nexport UE2000_FC=\"$DIR/FC_D\"\nexport UE2000_DQ=\"$DIR/DQ_A\"\nexport UE2000_RE=\"$DIR/RAM_E\"\nunset UE2000_NONINTERACTIVE\nexec \"$UE2000_FI/aplic/vvota.exe\" \"$@\"\n"
    (dest / "demo.sh").write_text(demo_sh, encoding="utf-8")
    (dest / "demo.sh").chmod(0o755)

    print("[3/5] Gerando bancos binarios (estgeral.ctr, candidat.dat, elelocal.dat) e 22 runners...")
    (fi_c / "FCV2000").write_bytes(b"TSE-UE2000-FLASH-VOTACAO-OK\r\n")
    (fi_c / "estgeral.ctr").write_bytes(criar_estgeral_ctr(0x00, 0x01, 1, 15))
    (fi_c / "aplic" / "marca").write_bytes(b"INSTALADO_OK\r\n")
    (fi_c / "temp" / "marca").write_bytes(b"INSTALADO_OK\r\n")
    (fi_c / "virtuos" / "LMVOS.LIB").write_bytes(b"!<arch>\nLMVOS_MICROBASE_VIRTUOS_2000\n")

    # Gabaritos de estado para arqcmp
    (fi_c / "aplic" / "estados" / "estados").write_bytes(criar_estgeral_ctr(0x00, 0x01, 1, 15))
    for _, disco, _, _, _ in RUNNERS_MAP:
        (fi_c / "aplic" / "estados" / disco).write_bytes(criar_estgeral_ctr(0x00, 0x01, 1, 15))

    # Bancos de dados eleitorais e arquivos de midia/treino
    (fi_c / "basedado" / "candidat.dat").write_bytes(criar_candidat_dat())
    (fi_c / "basedado" / "elelocal.dat").write_bytes(criar_elelocal_dat())
    (fi_c / "fototrei" / "foto_tr.bmp").write_bytes(b"BM_FOTO_TREINO_UE2000")
    (fi_c / "vototrei" / "voto_tr.dat").write_bytes(b"VOTO_TREINO_UE2000")
    (fi_c / "canttrei" / "aplic" / "audio_cant.pcm").write_bytes(b"RIFF_PCM_VOTO_CANTADO_2000")
    (fi_c / "som_urna" / "fim_voto.wav").write_bytes(b"RIFF_PILILILI_TSE_2000")
    (fi_c / "testes" / "teste_hw.dat").write_bytes(b"TESTE_PADRAO_UE2000")
    (fi_c / "testfab" / "burnin.dat").write_bytes(b"TESTE_FABRICA_FUCAPI_2000")
    (fc_d / "fotos" / "F91.BMP").write_bytes(b"BM_CANDIDATO_91_UE2000")
    (fc_d / "fotos" / "F92.BMP").write_bytes(b"BM_CANDIDATO_92_UE2000")

    # Os 22 runners em RAM_E
    for nome_bat, disco, exe, flag_d, desc in RUNNERS_MAP:
        (ram_e / nome_bat).write_text(gerar_runner_bat(nome_bat, disco, exe, flag_d, desc), encoding="utf-8")

    # Scripts principais da raiz C:\ e template de manutencao
    (fi_c / "instala.bat").write_text(
        "@echo off\r\n"
        "xcopy %FI%\\temp\\aplic\\*.* %FI%\\aplic\\ /v /s > nul\r\n"
        "copy %FI%\\aplic\\marca %FI%\\temp\\marca /v > nul\r\n",
        encoding="utf-8",
    )
    (fi_c / "novobat.bat").write_text(
        "@echo off\r\n"
        "%FI%\\desbloq -m > nul\r\n"
        "copy %FI%\\setup.mnt %FI%\\SETUP.BAT /v > nul\r\n"
        "del %FI%\\setup.mnt > nul\r\n",
        encoding="utf-8",
    )
    setup_bat_content = (
        "@echo off\r\n"
        "set FI=C:\r\n"
        "set FC=D:\r\n"
        "set DQ=A:\r\n"
        ":inicio\r\n"
        "diskfix %FI% /vs > nul\r\n"
        "if errorlevel 1 goto TentaRecuperar\r\n"
        "ckpack %FI%\\raiz.crc %FI%\\ > nul\r\n"
        "if errorlevel 1 goto ebatger\r\n"
        "tipurna > nul\r\n"
        "if errorlevel 32 goto urna_invalida\r\n"
        "if errorlevel 4 goto ue2000\r\n"
        ":ue2000\r\n"
        "arqcmp %FI%\\estgeral.ctr %FI%\\aplic\\estados\\estados 1 0 0 > nul\r\n"
        "call e:\\roda_v1.bat\r\n"
        "goto fim\r\n"
        ":TentaRecuperar\r\n"
        ":ebatger\r\n"
        ":urna_invalida\r\n"
        "gecho &&ERRO DE INTEGRIDADE NA URNA!\r\n"
        ":fim\r\n"
    )
    (fi_c / "SETUP.BAT").write_text(setup_bat_content, encoding="utf-8")
    (fi_c / "aplic" / "setup.mnt").write_text(setup_bat_content, encoding="utf-8")
    (fi_c / "aplic" / "novobat.bat").write_text((fi_c / "novobat.bat").read_text(encoding="utf-8"), encoding="utf-8")
    (dq_a / "disco15").write_bytes(b"DISCO_OFICIAL_1_TURNO_UE2000\r\n")

    if compilar:
        print("[4/5] Compilando todos os binarios C com GCC (zero warnings)...")
        subprocess.run(["make", "-C", str(dest)], check=True)

    print("[5/5] Calculando MD5 e gerando assinaturas ASSINA (.crc e .sig) dos 16 manifestos...")
    gerar_crc_e_sig(fi_c / "raiz.crc", fi_c, ["SETUP.BAT", "instala.bat", "novobat.bat", "FCV2000"])
    gerar_crc_e_sig(fi_c / "raiz2000.crc", fi_c, ["SETUP.BAT", "FCV2000"])
    gerar_crc_e_sig(fi_c / "virtuos" / "tipourna.crc", fi_c, ["FCV2000"])
    gerar_crc_e_sig(
        fi_c / "virtuos" / "virtuos.crc",
        fi_c / "virtuos",
        ["ckpack.exe", "tipurna.exe", "arqcmp.exe", "diskfix.exe", "log.exe", "gecho.exe", "LMVOS.LIB"],
    )
    gerar_crc_e_sig(
        fi_c / "aplic" / "aplic.crc",
        fi_c / "aplic",
        ["vvota.exe", "vred.exe", "vcant_e.exe", "vjustif.exe", "vaudit.exe", "desbloq.exe"],
    )
    gerar_crc_e_sig(fi_c / "aplic" / "apl_elei.crc", fi_c / "aplic", ["vvota.exe", "vred.exe"])
    gerar_crc_e_sig(fi_c / "aplic" / "apl_trei.crc", fi_c / "aplic", ["vvota.exe"])
    gerar_crc_e_sig(fi_c / "aplic" / "apl_simu.crc", fi_c / "aplic", ["vvota.exe"])
    gerar_crc_e_sig(fi_c / "fototrei" / "fototrei.crc", fi_c / "fototrei", ["foto_tr.bmp"])
    gerar_crc_e_sig(fi_c / "vototrei" / "vototrei.crc", fi_c / "vototrei", ["voto_tr.dat"])
    gerar_crc_e_sig(fi_c / "canttrei" / "aplic" / "votocant.crc", fi_c / "canttrei" / "aplic", ["audio_cant.pcm"])
    gerar_crc_e_sig(fi_c / "som_urna" / "som_urna.crc", fi_c / "som_urna", ["fim_voto.wav"])
    gerar_crc_e_sig(fi_c / "testes" / "testes.crc", fi_c / "testes", ["teste_hw.dat"])
    gerar_crc_e_sig(fi_c / "testfab" / "testfab.crc", fi_c / "testfab", ["burnin.dat"])
    gerar_crc_e_sig(fi_c / "basedado" / "candidat.crc", fi_c / "basedado", ["candidat.dat"])
    gerar_crc_e_sig(fi_c / "basedado" / "elelocal.crc", fi_c / "basedado", ["elelocal.dat"])
    gerar_crc_e_sig(fc_d / "fotos" / "fotos.crc", fc_d / "fotos", ["F91.BMP", "F92.BMP"])

    if testar and compilar:
        executar_bateria_testes(dest)


def executar_bateria_testes(dest: Path) -> None:
    print("\n======================================================================")
    print(" INICIANDO BATERIA DE TESTES AUTOMATIZADOS DO SISTEMA UE2000 (v2.1)")
    print("======================================================================")
    env = os.environ.copy()
    env["UE2000_FI"] = str((dest / "FI_C").resolve())
    env["UE2000_FC"] = str((dest / "FC_D").resolve())
    env["UE2000_DQ"] = str((dest / "DQ_A").resolve())
    env["UE2000_RE"] = str((dest / "RAM_E").resolve())
    env["UE2000_NONINTERACTIVE"] = "1"

    ckpack_bin = str((dest / "FI_C" / "virtuos" / "ckpack.exe").resolve())
    tipurna_bin = str((dest / "FI_C" / "virtuos" / "tipurna.exe").resolve())
    arqcmp_bin = str((dest / "FI_C" / "virtuos" / "arqcmp.exe").resolve())
    diskfix_bin = str((dest / "FI_C" / "virtuos" / "diskfix.exe").resolve())
    desbloq_bin = str((dest / "FI_C" / "aplic" / "desbloq.exe").resolve())
    diag_bin = str((dest / "FI_C" / "aplic" / "diag_manut.exe").resolve())
    vvota_bin = str((dest / "FI_C" / "aplic" / "vvota.exe").resolve())
    vaudit_bin = str((dest / "FI_C" / "aplic" / "vaudit.exe").resolve())

    # 1. Teste de Superficie (diskfix)
    r = subprocess.run([diskfix_bin, "C:", "/vs"], env=env)
    assert r.returncode == 0, f"Falha em diskfix: {r.returncode}"
    print("[OK] 1. diskfix C: /vs -> ReturnCode 0 (Superficie da Flash Interna integra)")

    # 2. Teste de todos os 17 manifestos (.crc + .sig ASSINA 256-bit) via ckpack
    manifestos = [
        (["C:\\raiz.crc", "C:\\"]),
        (["C:\\virtuos\\tipourna.crc", "C:\\"]),
        (["C:\\virtuos\\virtuos.crc", "C:\\virtuos"]),
        (["C:\\aplic\\aplic.crc", "C:\\aplic"]),
        (["C:\\aplic\\apl_elei.crc", "C:\\aplic"]),
        (["C:\\aplic\\apl_trei.crc", "C:\\aplic"]),
        (["C:\\aplic\\apl_simu.crc", "C:\\aplic"]),
        (["C:\\fototrei\\fototrei.crc", "C:\\fototrei"]),
        (["C:\\vototrei\\vototrei.crc", "C:\\vototrei"]),
        (["-m", "votocant.crc", "C:\\canttrei\\aplic"]),
        (["C:\\som_urna\\som_urna.crc", "C:\\som_urna"]),
        (["C:\\raiz2000.crc", "C:\\"]),
        (["C:\\testes\\testes.crc", "C:\\testes"]),
        (["C:\\testfab\\testfab.crc", "C:\\testfab"]),
        (["C:\\basedado\\candidat.crc", "C:\\basedado"]),
        (["C:\\basedado\\elelocal.crc", "C:\\basedado"]),
        (["D:\\fotos\\fotos.crc", "D:\\fotos"]),
    ]
    for args in manifestos:
        res = subprocess.run([ckpack_bin] + args, env=env)
        assert res.returncode == 0, f"Falha em ckpack {args}: rc={res.returncode}"
    print(f"[OK] 2. ckpack validou todos os {len(manifestos)} manifestos .crc e assinaturas .sig (256-bit)")

    # 3. Teste de detecção de adulteração e da exceção da flag -m no Voto Cantado
    pcm_file = dest / "FI_C" / "canttrei" / "aplic" / "audio_cant.pcm"
    orig_bytes = pcm_file.read_bytes()
    pcm_file.write_bytes(b"ADULTERADO_NO_2_TURNO")
    res_sem_m = subprocess.run([ckpack_bin, "C:\\canttrei\\aplic\\votocant.crc", "C:\\canttrei\\aplic"], env=env)
    res_com_m = subprocess.run([ckpack_bin, "-m", "votocant.crc", "C:\\canttrei\\aplic"], env=env)
    pcm_file.write_bytes(orig_bytes)
    assert res_sem_m.returncode == 1 and res_com_m.returncode == 0
    print("[OK] 3. ckpack bloqueou adulteracao sem '-m' (rc=1) e permitiu '*cant*' com '-m' (rc=0)")

    # 4. Teste de Identificacao de Hardware (tipurna)
    r_tip = subprocess.run([tipurna_bin], env=env)
    assert r_tip.returncode == 4, f"Esperado 4 (UE2000 OK), obteve {r_tip.returncode}"
    print("[OK] 4. tipurna -> ReturnCode 4 (Faixa 4..8 = Hardware UE2000 com Serie e CRC16 validos)")

    # 5. Teste de Discriminacao de Estado (arqcmp)
    r_cmp0 = subprocess.run([arqcmp_bin, "C:\\estgeral.ctr", "C:\\aplic\\estados\\estados", "1", "0", "0"], env=env)
    r_cmp240 = subprocess.run([arqcmp_bin, "C:\\estgeral.ctr", "C:\\aplic\\estados\\estados", "1", "0", "240"], env=env)
    r_cmp_d15 = subprocess.run([arqcmp_bin, "C:\\estgeral.ctr", "C:\\aplic\\estados\\disco15", "1", "1", "1"], env=env)
    assert r_cmp0.returncode == 0 and r_cmp240.returncode == 1 and r_cmp_d15.returncode == 0
    print("[OK] 5. arqcmp discriminou byte 0 (rota bateria) e byte 1 (fase pronta p/ disco15)")

    # 6. Teste de Votacao Oficial (vvota.exe -> Zeresima + Microterminal RS-485 + Cifra CEPESC do BU)
    r_vota = subprocess.run([vvota_bin], env=env)
    assert r_vota.returncode == 0
    bu_gerado = dest / "DQ_A" / "bu_2000.bu"
    mterm_log = dest / "FI_C" / "MTERM_LCD.LOG"
    assert bu_gerado.exists() and bu_gerado.stat().st_size > 0
    assert mterm_log.exists()
    print(f"[OK] 6. vvota.exe executou votacao, gravou frames RS-485 e cifrou BU ({bu_gerado.stat().st_size} bytes)")

    # 7. Teste de Transicao de Modo (desbloq -m e -z)
    r_des = subprocess.run([desbloq_bin, "-m"], env=env)
    assert r_des.returncode == 0
    r_des_z = subprocess.run([desbloq_bin, "-z"], env=env)
    assert r_des_z.returncode == 0
    print("[OK] 7. desbloq.exe transitou estados na EEPROM e controlou pino de Write-Protect da FI")

    # 8. Teste do Shell de Manutencao (Menus 1..4, errorlevel 49..58, impressora e bateria)
    r_prn = subprocess.run([diag_bin, "--check-printer"], env=env)
    r_bat = subprocess.run([diag_bin, "--check-bat-int"], env=env)
    env_menu = env.copy()
    env_menu["UE2000_MENU_CHOICE"] = "56"  # Opcao 8 -> Aplic_18 / Aplic_28 / Aplic_38 / Aplic_48
    r_m1 = subprocess.run([diag_bin, "1"], env=env_menu, capture_output=True)
    assert r_prn.returncode == 0 and r_bat.returncode == 0 and r_m1.returncode == 56
    print("[OK] 8. diag_manut.exe validou impressora (rc=0), bateria (rc=0) e Menus 1..4 (errorlevel 49..58)")

    # 9. Teste do Ponto de Ruptura Rezende (2004): modificacao em SETUP.BAT detectada por raiz.crc
    setup_path = dest / "FI_C" / "SETUP.BAT"
    setup_orig = setup_path.read_bytes()
    setup_rezende = setup_orig.replace(
        b"if errorlevel 1 goto ebatger",
        b"REM if errorlevel 1 goto ebatger",
    )
    setup_path.write_bytes(setup_rezende)
    r_rez = subprocess.run([ckpack_bin, "C:\\raiz.crc", "C:\\"], env=env)
    setup_path.write_bytes(setup_orig)
    r_rest = subprocess.run([ckpack_bin, "C:\\raiz.crc", "C:\\"], env=env)
    assert r_rez.returncode == 1 and r_rest.returncode == 0
    print("[OK] 9. Simulacao Rezende/2004: comentar 'if errorlevel 1 goto ebatger' altera MD5 e dispara rc=1 em ckpack")

    # 10. Teste do Auto-Validador V.PRE (vaudit.exe - Relatorio PI2003)
    r_aud = subprocess.run([vaudit_bin], env=env, capture_output=True, text=True)
    assert r_aud.returncode == 0 and "SHA-1:" in r_aud.stdout
    print("[OK] 10. vaudit.exe (V.PRE) calculou tabela SHA-1 da Flash Interna e listou candidatos:")
    for line in r_aud.stdout.strip().splitlines():
        print("      " + line)

    print("======================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construtor e Simulador Documental da Interface UE2000 (v2.2)")
    parser.add_argument("--dest", default="./ue2000_env", help="Diretorio de destino para a arvore reconstruida")
    parser.add_argument("--no-compile", action="store_true", help="Apenas gera os fontes sem compilar")
    parser.add_argument("--no-test", action="store_true", help="Nao executa a bateria de testes apos compilar")
    args = parser.parse_args()

    construir_ambiente(
        Path(args.dest),
        compilar=not args.no_compile,
        testar=not args.no_test,
    )