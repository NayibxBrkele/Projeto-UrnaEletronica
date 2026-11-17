/* ============================================================================
 * ARQUIVO     : aplic/diag_manut.c
 * BINARIO     : C:\APLIC\DIAG_MANUT.EXE
 * DESCRICAO   : Verificador de Impressora (1..4), Bateria (3..4) e Shell dos
 *               4 Menus de Manutencao (errorlevel 49..58) e 11 rotinas Aplic_*
 * ============================================================================ */

#include "../include/dos_compat.h"

int verifica_impressora(void) {
    uint8_t st = (uint8_t)inp(IO_PORT_HW_STATUS);
    if ((st & 0x01) == 0) return 2; /* 2 = Nao detectada */
    if (st & 0x02)        return 1; /* 1 = Erro critico  */
    if (st & 0x04)        return 3; /* 3 = Atolamento    */
    if (st & 0x08)        return 4; /* 4 = Sem papel     */
    return 0;
}

int verifica_bateria(int externa) {
    uint8_t st = (uint8_t)inp(IO_PORT_HW_STATUS);
    if (!externa) {
        if (st & 0x10) return 4; /* 4 = Interna ausente */
        if (st & 0x20) return 3; /* 3 = Interna critica */
    } else {
        if (st & 0x40) return 4; /* 4 = Externa ausente */
        if (st & 0x80) return 3; /* 3 = Externa critica */
    }
    return 0;
}

int main(int argc, char *argv[]) {
    int menu = 1;
    int tecla;

    if (argc >= 2) {
        if (strcmp(argv[1], "--check-printer") == 0) return verifica_impressora();
        if (strcmp(argv[1], "--check-bat-int") == 0) return verifica_bateria(0);
        if (strcmp(argv[1], "--check-bat-ext") == 0) return verifica_bateria(1);
        menu = atoi(argv[1]);
    }

    if (getenv("UE2000_MENU_CHOICE") != NULL) {
        int c = atoi(getenv("UE2000_MENU_CHOICE"));
        if (c >= 48 && c <= 58) return c;
    }

    printf("\n=== TSE UE2000 - MENU DE MANUTENCAO %d ===\n", menu);
    if (menu == 1) {
        printf("1(49):Diagnostico | 2(50):RelatorioSimples | 3(51):AutonomiaVotoImpresso\n");
        printf("4(52):AutonomiaSemVotoImpresso | 5(53):Menu2 | 6(54):Menu3 | 7(55):Menu4\n");
        printf("8(56):Aplic_18 | 9(57):Aplic_19 | 0(58):Sair\n");
    } else if (menu == 2) {
        printf("1(49):ImpBrasao | 2(50):ImpCodBar | 3(51):ImpTipCar | 4(52):AtolaPapel\n");
        printf("5(53):TesteImpGen | 6(54):ZeresimaPeq | 7(55):ZeresimaGrd | 8(56):Aplic_28\n");
    } else if (menu == 3) {
        printf("1(49):CmdMicroterm | 2(50):TxRxMicroterm | 3(51):CmdFonte | 4(52):LeituraBat\n");
        printf("5(53):ImpMicroterm | 6(54):Aplic_36 | 7(55):Aplic_37 | 8(56):Aplic_38\n");
    } else if (menu == 4) {
        printf("1(49):TesteSom | 2(50):LeituraNumInterno | 3(51):ManutFabrica\n");
        printf("4(52):Aplic_44 | 5(53):Aplic_45 | 6(54):Aplic_46 | 7(55):Aplic_47 | 8(56):Aplic_48\n");
    }

    tecla = getch();
    if (tecla >= '1' && tecla <= '9') return tecla;
    return 58;
}
