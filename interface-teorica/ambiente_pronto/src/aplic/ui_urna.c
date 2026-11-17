/*
 * Interface textual reconstruida para demonstracao UE2000.
 * Mensagens e fluxo de teclado sao inferidos do material fornecido;
 * nao e uma transcricao autenticada da interface original.
 */
#include "../include/dos_compat.h"

#define TECLA_BRANCO   'B'
#define TECLA_CORRIGE  'C'
#define TECLA_CONFIRMA 'F' /* tecla F mapeia o botao CONFIRMA no PC */
#define TECLA_ESC      0x1B

static int ui_em_modo_teste(void) {
    return getenv("UE2000_NONINTERACTIVE") != NULL;
}

static void ui_moldura(const char *titulo, const char *instrucao) {
    if (ui_em_modo_teste()) return;
    clrscr();
    printf("+--------------------------------------------------------------+\n");
    printf("| JUSTICA ELEITORAL                            SIMULADOR UE2000 |\n");
    printf("+--------------------------------------------------------------+\n");
    printf("|                                                              |\n");
    printf("|  %-60.60s|\n", titulo ? titulo : "");
    printf("|                                                              |\n");
    printf("+--------------------------------------------------------------+\n");
    printf("| %-60.60s |\n", instrucao ? instrucao : "");
    printf("+--------------------------------------------------------------+\n");
    fflush(stdout);
}

static int ui_wait_key(void) {
    if (ui_em_modo_teste()) return TECLA_CONFIRMA;
    return getch();
}

void ui_tela_aguarde(void) {
    ui_moldura("AGUARDE A LIBERACAO DO MESARIO",
               "O MESARIO IRA HABILITAR SUA VOTACAO");
    (void)ui_wait_key();
}

void ui_tela_liberado(void) {
    ui_moldura("ELEITOR HABILITADO",
               "DIRIJA-SE A CABINE E COMECE A VOTAR");
    (void)ui_wait_key();
}

/* Retorno 1: candidato selecionado; retorno 0: branco confirmado. */
int ui_votar_cargo(uint8_t cargo_code, int num_digitos, const char *cargo_nome,
                   const REGISTRO_CANDIDATO *cands, int n_cands,
                   REGISTRO_CANDIDATO *cand_encontrado) {
    char buffer[8] = {0};
    int pos = 0, tecla, i;
    char instrucao[80];

    if (ui_em_modo_teste()) {
        for (i = 0; i < n_cands; i++) {
            if (cands[i].cargo == cargo_code) {
                *cand_encontrado = cands[i];
                return 1;
            }
        }
        return 0;
    }

    for (;;) {
        snprintf(instrucao, sizeof(instrucao),
                 "DIGITE O NUMERO DO %s (%d DIGITOS)", cargo_nome, num_digitos);
        ui_moldura(cargo_nome, instrucao);
        printf("|  NUMERO: [ %-*s ]                                           |\n",
               num_digitos, buffer);
        printf("+--------------------------------------------------------------+\n");
        printf("| [0-9] DIGITAR  [B] BRANCO  [C] CORRIGE  [F] CONFIRMA         |\n");
        printf("+--------------------------------------------------------------+\n");
        fflush(stdout);
        tecla = getch();

        if (tecla >= '0' && tecla <= '9' && pos < num_digitos) {
            buffer[pos++] = (char)tecla;
            buffer[pos] = '\0';
        } else if (tecla == TECLA_CORRIGE || tecla == TECLA_ESC) {
            pos = 0;
            buffer[0] = '\0';
        } else if (tecla == TECLA_BRANCO) {
            ui_moldura("VOTO EM BRANCO",
                       "APERTE F PARA GRAVAR OU C PARA VOLTAR");
            printf("|  CARGO: %-51.51s|\n", cargo_nome);
            printf("|  VOTO : EM BRANCO                                            |\n");
            printf("+--------------------------------------------------------------+\n");
            for (;;) {
                int t2 = getch();
                if (t2 == TECLA_CONFIRMA) return 0;
                if (t2 == TECLA_CORRIGE) break;
            }
            pos = 0;
            buffer[0] = '\0';
        } else if (tecla == TECLA_CONFIRMA) {
            if (pos != num_digitos) {
                ui_moldura("NUMERO INCOMPLETO", "DIGITE TODOS OS NUMEROS E CONFIRME");
                (void)getch();
                continue;
            }
            for (i = 0; i < n_cands; i++) {
                if (cands[i].cargo == cargo_code &&
                    cands[i].numero == (uint32_t)atol(buffer)) {
                    *cand_encontrado = cands[i];
                    return 1;
                }
            }
            ui_moldura("CANDIDATO INEXISTENTE", "APERTE UMA TECLA E CORRIJA");
            (void)getch();
            pos = 0;
            buffer[0] = '\0';
        }
    }
}

/* Retorno 1: confirma; retorno 0: corrige. */
int ui_confirmar_voto(const REGISTRO_CANDIDATO *cand, const char *cargo_nome) {
    if (ui_em_modo_teste()) return 1;
    ui_moldura("CONFIRA SEU VOTO", "APERTE F PARA GRAVAR OU C PARA CORRIGIR");
    printf("|  CARGO   : %-47.47s|\n", cargo_nome);
    printf("|  NUMERO  : %-47lu|\n", (unsigned long)cand->numero);
    printf("|  CANDIDATO: %-46.46s|\n", cand->nome_urna);
    printf("|  PARTIDO : %-47.47s|\n", cand->partido_sigla);
    printf("+--------------------------------------------------------------+\n");
    fflush(stdout);
    for (;;) {
        int tecla = getch();
        if (tecla == TECLA_CONFIRMA) return 1;
        if (tecla == TECLA_CORRIGE) return 0;
    }
}

void ui_tela_fim(void) {
    ui_moldura("FIM", "OBRIGADO. VOCE PODE SE RETIRAR.");
    (void)ui_wait_key();
}
