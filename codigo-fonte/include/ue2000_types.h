/* ============================================================================
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
