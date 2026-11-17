/* ============================================================================
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
