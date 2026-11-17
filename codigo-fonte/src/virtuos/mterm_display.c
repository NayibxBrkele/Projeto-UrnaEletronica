/* Painel local de demonstracao do microterminal; nao abre porta serial. */
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
