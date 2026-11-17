/* ============================================================================
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
