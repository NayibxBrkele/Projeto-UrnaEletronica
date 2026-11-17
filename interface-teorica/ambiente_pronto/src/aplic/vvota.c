/* ============================================================================
 * ARQUIVO     : aplic/vvota.c
 * INTERFACE   : TUI interativa de demonstracao, reconstruida a partir dos
 *               materiais do projeto; nao e codigo oficial autenticado.
 * ============================================================================ */
#include "../include/dos_compat.h"

extern void lmvos_init(void);
extern void lmvos_mterm_send_frame(uint8_t cmd, const char *l1, const char *l2);
extern int cepesc_cifra_e_assina_bu(const char *bu_claro_dos, const char *bu_cifrado_dos);
extern void ui_tela_aguarde(void);
extern void ui_tela_liberado(void);
extern int ui_votar_cargo(uint8_t cargo_code, int num_digitos, const char *cargo_nome,
                          const REGISTRO_CANDIDATO *cands, int n_cands,
                          REGISTRO_CANDIDATO *cand_encontrado);
extern int ui_confirmar_voto(const REGISTRO_CANDIDATO *cand, const char *cargo_nome);
extern void ui_tela_fim(void);
extern void mterm_exibir_ultimo_frame(void);

static int carregar_candidatos(REGISTRO_CANDIDATO *lista, int max_cand) {
    char path[1024]; FILE *f; int n = 0;
    ue2000_resolve_path("C:\\basedado\\candidat.dat", path, sizeof(path));
    f = fopen(path, "rb");
    if (!f) return 0;
    while (n < max_cand && fread(&lista[n], sizeof(REGISTRO_CANDIDATO), 1, f) == 1) n++;
    fclose(f); return n;
}

static int salvar_candidatos(const REGISTRO_CANDIDATO *lista, int n) {
    char path[1024]; FILE *f;
    ue2000_resolve_path("C:\\basedado\\candidat.dat", path, sizeof(path));
    f = fopen(path, "wb"); if (!f) return -1;
    if (fwrite(lista, sizeof(REGISTRO_CANDIDATO), (size_t)n, f) != (size_t)n) {
        fclose(f); return -1;
    }
    fclose(f); return 0;
}

static int votar_cargo_completo(uint8_t cargo, int digitos, const char *nome,
                                const REGISTRO_CANDIDATO *cands, int n,
                                REGISTRO_CANDIDATO *escolhido) {
    for (;;) {
        int r = ui_votar_cargo(cargo, digitos, nome, cands, n, escolhido);
        if (r == 0) return 0; /* branco confirmado pela interface */
        if (ui_confirmar_voto(escolhido, nome)) return 1;
        /* CORRIGE: retorna à digitação do mesmo cargo. */
    }
}

int main(int argc, char **argv) {
    char est_path[1024], bu_claro_path[1024];
    ESTGERAL_CTR est;
    REGISTRO_CANDIDATO cands[32], vereador, prefeito;
    int n, i, r_ver, r_pre;
    FILE *fe, *fb;
    (void)argc; (void)argv;

    lmvos_init();
    ue2000_resolve_path("C:\\estgeral.ctr", est_path, sizeof(est_path));
    fe = fopen(est_path, "r+b"); if (!fe) return 2;
    if (fread(&est, sizeof(est), 1, fe) != 1) { fclose(fe); return 2; }
    n = carregar_candidatos(cands, 32);
    if (n <= 0) { fclose(fe); return 2; }

    if (est.total_comparecim == 0) {
        lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "EMITINDO ZERESIMA...", "AGUARDE IMPRESSAO");
    }
    lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "DIGITE TITULO ELEIT.", "SECAO 0102 ZONA 0001");
    ui_tela_aguarde();
    lmvos_mterm_send_frame(MTERM_CMD_LED_LIBERADO, "ELEITOR HABILITADO", "CABINE LIBERADA");
    ui_tela_liberado();
    mterm_exibir_ultimo_frame();

    r_ver = votar_cargo_completo(CARGO_VEREADOR, 5, "VEREADOR", cands, n, &vereador);
    r_pre = votar_cargo_completo(CARGO_PREFEITO, 2, "PREFEITO", cands, n, &prefeito);

    if (r_ver) for (i = 0; i < n; i++)
        if (cands[i].cargo == CARGO_VEREADOR && cands[i].numero == vereador.numero) {
            cands[i].total_votos++; break;
        }
    if (r_pre) for (i = 0; i < n; i++)
        if (cands[i].cargo == CARGO_PREFEITO && cands[i].numero == prefeito.numero) {
            cands[i].total_votos++; break;
        }
    if (salvar_candidatos(cands, n) != 0) { fclose(fe); return 1; }

    est.total_comparecim++;
    est.fase_operacao = (est.turno_atual == 1) ? FASE_ENCERRADA_1T : FASE_ENCERRADA_2T;
    est.crc16_estrutura = ue2000_crc16_ccitt((const uint8_t *)&est, sizeof(est) - 2);
    rewind(fe);
    if (fwrite(&est, sizeof(est), 1, fe) != 1) { fclose(fe); return 1; }
    fclose(fe);

    ue2000_resolve_path("C:\\aplic\\bu_claro.tmp", bu_claro_path, sizeof(bu_claro_path));
    fb = fopen(bu_claro_path, "wb"); if (!fb) return 1;
    fprintf(fb, "BOLETIM DE DEMONSTRACAO UE2000 - NAO OFICIAL\r\n");
    fprintf(fb, "UF: %c%c | ZONA: %04u | SECAO: %04u | TURNO: %u\r\n",
            est.uf_sigla[0], est.uf_sigla[1], est.zona_eleitoral, est.secao_eleitoral, est.turno_atual);
    fprintf(fb, "COMPARECIMENTO SIMULADO: %lu\r\n", (unsigned long)est.total_comparecim);
    for (i = 0; i < n; i++)
        fprintf(fb, "CARGO %u | NUM %05lu | %-24s | %-6s | VOTOS %04lu\r\n",
                cands[i].cargo, (unsigned long)cands[i].numero, cands[i].nome_urna,
                cands[i].partido_sigla, (unsigned long)cands[i].total_votos);
    fclose(fb);

    /* A rotina criptografica do gerador e um placeholder de simulacao,
       nao a implementacao proprietaria CEPESC/ABIN. */
    if (cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "C:\\aplic\\bu_2000.bu") != 0) return 1;
    (void)cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "A:\\bu_2000.bu");
    (void)cepesc_cifra_e_assina_bu("C:\\aplic\\bu_claro.tmp", "D:\\bu_2000.bu");
    lmvos_mterm_send_frame(MTERM_CMD_DISPLAY, "VOTACAO ENCERRADA", "BU GRAVADO NO DISCO");
    mterm_exibir_ultimo_frame();
    ui_tela_fim();
    return 0;
}
