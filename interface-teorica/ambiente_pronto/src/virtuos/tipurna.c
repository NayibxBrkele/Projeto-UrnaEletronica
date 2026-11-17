/* ============================================================================
 * ARQUIVO     : virtuos/tipurna.c
 * BINARIO     : C:\VIRTUOS\TIPURNA.EXE
 * CONTRATO L4 : tipurna > nul (Retorna errorlevel nas 10 faixas do SETUP.BAT)
 * ============================================================================ */

#include "../include/dos_compat.h"

static void ler_eeprom_completa(EEPROM_URNA *out) {
    uint8_t *p = (uint8_t *)out;
    size_t i;
    for (i = 0; i < sizeof(EEPROM_URNA); i++) {
        outp(IO_PORT_EEPROM_ADDR, (int)i);
        p[i] = (uint8_t)inp(IO_PORT_EEPROM_DATA);
    }
}

static int serie_valida(uint8_t modelo, uint32_t serie) {
    if (serie == 0 || serie == 0xFFFFFFFFUL) return 0;
    switch (modelo) {
        case MODELO_HW_UE96:   return (serie >= 100000UL && serie <= 199999UL);
        case MODELO_HW_UE98:   return (serie >= 200000UL && serie <= 499999UL);
        case MODELO_HW_UE2000: return (serie >= 500000UL && serie <= 999999UL);
        default:               return 0;
    }
}

int main(void) {
    EEPROM_URNA eep;
    uint16_t crc_calc;

    ler_eeprom_completa(&eep);

    if (memcmp(eep.assinatura, "TSE", 3) != 0) {
        return 32; /* 32..255 -> urna_invalida */
    }

    crc_calc = ue2000_crc16_ccitt((const uint8_t *)&eep, sizeof(EEPROM_URNA) - sizeof(uint16_t));
    if (crc_calc != eep.crc16_eeprom) {
        switch (eep.modelo_urna) {
            case MODELO_HW_UE2000: return 12; /* 12..16 -> ue2000_crc_invalido */
            case MODELO_HW_UE98:   return 10; /* 10..11 -> ue98_crc_invalido   */
            case MODELO_HW_UE96:   return 9;  /* 9      -> ue96_crc_invalido   */
            default:               return 32;
        }
    }

    if (!serie_valida(eep.modelo_urna, eep.numero_serie)) {
        switch (eep.modelo_urna) {
            case MODELO_HW_UE2000: return 20; /* 20..31 -> ue2000_numero_invalido */
            case MODELO_HW_UE98:   return 18; /* 18..19 -> ue98_numero_invalido   */
            case MODELO_HW_UE96:   return 17; /* 17     -> ue96_numero_invalido   */
            default:               return 32;
        }
    }

    switch (eep.modelo_urna) {
        case MODELO_HW_UE2000: return 4; /* 4..8 -> goto ue2000 */
        case MODELO_HW_UE98:   return 2; /* 2..3 -> goto ue98   */
        case MODELO_HW_UE96:   return 1; /* 0..1 -> goto ue96   */
        default:               return 32;
    }
}
