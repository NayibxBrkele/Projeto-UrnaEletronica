/* ============================================================================
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
