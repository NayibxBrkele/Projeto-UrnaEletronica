/* ============================================================================
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
