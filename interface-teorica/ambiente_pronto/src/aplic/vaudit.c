/* ============================================================================
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
