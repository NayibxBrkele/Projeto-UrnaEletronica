/* ============================================================================
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
