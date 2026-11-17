/* ============================================================================
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
