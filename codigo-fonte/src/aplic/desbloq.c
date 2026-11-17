/* ============================================================================
 * ARQUIVO     : aplic/desbloq.c
 * BINARIO     : C:\APLIC\DESBLOQ.EXE
 * CONTRATO L4 : desbloq <-s|-r|-a|-d|-m|-h|-g|-z|-x|-y|-w>
 * ============================================================================ */

#include "../include/dos_compat.h"

static uint16_t ler_modo_eeprom(void) {
    uint16_t lo, hi;
    outp(IO_PORT_EEPROM_ADDR, 10);
    lo = (uint16_t)inp(IO_PORT_EEPROM_DATA);
    outp(IO_PORT_EEPROM_ADDR, 11);
    hi = (uint16_t)inp(IO_PORT_EEPROM_DATA);
    return (uint16_t)((hi << 8) | lo);
}

static void gravar_modo_eeprom(uint16_t modo) {
    outp(IO_PORT_EEPROM_ADDR, 10);
    outp(IO_PORT_EEPROM_DATA, modo & 0xFF);
    outp(IO_PORT_EEPROM_ADDR, 11);
    outp(IO_PORT_EEPROM_DATA, (modo >> 8) & 0xFF);
}

static void atualizar_estgeral_fase(uint8_t nova_fase) {
    char path[1024];
    FILE *f;
    ESTGERAL_CTR est;

    ue2000_resolve_path("C:\\estgeral.ctr", path, sizeof(path));
    f = fopen(path, "r+b");
    if (!f) return;
    if (fread(&est, sizeof(ESTGERAL_CTR), 1, f) == 1) {
        est.fase_operacao = nova_fase;
        est.crc16_estrutura = ue2000_crc16_ccitt((const uint8_t *)&est, sizeof(ESTGERAL_CTR) - 2);
        fseek(f, 0L, SEEK_SET);
        fwrite(&est, sizeof(ESTGERAL_CTR), 1, f);
    }
    fclose(f);
}

int main(int argc, char *argv[]) {
    char flag;
    uint16_t modo_atual;

    if (argc != 2 || argv[1][0] != '-') return 1;
    flag = argv[1][1];
    modo_atual = ler_modo_eeprom();

    switch (flag) {
        case 's': /* Status de reserva */
            return (modo_atual == EEPROM_MODO_FCC2) ? 0 : 1;

        case 'r': /* Transicao de Urna de Reserva FCC2 -> FCC4 */
            if (modo_atual == EEPROM_MODO_FCC2) {
                outp(IO_PORT_FLASH_WP, 0x00);
                gravar_modo_eeprom(EEPROM_MODO_FCC4);
                atualizar_estgeral_fase(FASE_PRONTA_VOTACAO);
                return 0;
            }
            return 1;

        case 'a': /* Modo Auditoria (V.PRE) */
            gravar_modo_eeprom(EEPROM_MODO_AUDIT);
            return 0;

        case 'd': /* Modo Diagnostico */
            gravar_modo_eeprom(EEPROM_MODO_DIAG);
            return 0;

        case 'm': /* Modo Manutencao: destrava escrita fisica na Flash Interna */
            outp(IO_PORT_FLASH_WP, 0x00);
            gravar_modo_eeprom(EEPROM_MODO_MANUT);
            atualizar_estgeral_fase(FASE_MANUTENCAO);
            return 0;

        case 'h': /* Hardware lock / Help */
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        case 'g': /* Retorno ao estado operacional FCC0 */
            gravar_modo_eeprom(EEPROM_MODO_FCC0);
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        case 'z': /* Encerramento Eleicao Oficial */
        case 'x': /* Encerramento Voto Cantado    */
        case 'y': /* Encerramento Justificativa   */
        case 'w': /* Encerramento Simulado/Treino */
            gravar_modo_eeprom(EEPROM_MODO_ENCERRADO);
            atualizar_estgeral_fase(FASE_ENCERRADA_1T);
            outp(IO_PORT_FLASH_WP, 0x01);
            return 0;

        default:
            return 1;
    }
}
