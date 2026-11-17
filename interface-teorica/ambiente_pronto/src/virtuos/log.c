/* ============================================================================
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
