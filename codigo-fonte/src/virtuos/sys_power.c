/* ============================================================================
 * ARQUIVO     : virtuos/sys_power.c (Gera RES.EXE, BOOT.COM e DESLIGA.COM)
 * CONTRATO L4 : res %FI% | boot | desliga
 * ============================================================================ */

#include "../include/dos_compat.h"

int main(int argc, char *argv[]) {
    (void)argc;
    /* Flush de buffers do sistema de arquivos e sinalizacao de desligamento/reboot */
    fflush(stdout);
    if (argv[0] && (strstr(argv[0], "desliga") || strstr(argv[0], "DESLIGA"))) {
        outp(IO_PORT_POWER_RELAY, 0xFF);
    }
    return 0;
}
