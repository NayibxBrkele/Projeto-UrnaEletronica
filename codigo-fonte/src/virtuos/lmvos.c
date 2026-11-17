/* ============================================================================
 * ARQUIVO     : virtuos/lmvos.c
 * PROJETO     : Microbase VirtuOS - LMVOS.LIB (Multitasking & Microterminal)
 * DESCRICAO   : Escalonador cooperativo de threads (setjmp/longjmp) e driver
 *               serial RS-485 com checksum BCC para o Microterminal do Mesario.
 * ============================================================================ */

#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/dos_compat.h"

#define MAX_VTHREADS        8
#define STACK_SIZE_BYTES    8192

typedef enum {
    VT_FREE = 0,
    VT_READY,
    VT_RUNNING,
    VT_SLEEPING
} VT_STATE;

typedef struct {
    int            id;
    VT_STATE       state;
    jmp_buf        context;
    unsigned long  wake_tick;
    void          (*entry)(void *);
    void          *arg;
} VTHREAD_TCB;

static VTHREAD_TCB   g_threads[MAX_VTHREADS];
static int           g_current_thread = 0;
static unsigned long g_system_ticks   = 0;
static uint8_t       g_mterm_seq      = 0;

void lmvos_init(void) {
    memset(g_threads, 0, sizeof(g_threads));
    g_threads[0].id    = 0;
    g_threads[0].state = VT_RUNNING;
}

int lmvos_thread_create(void (*func)(void *), void *arg) {
    int i;
    for (i = 1; i < MAX_VTHREADS; i++) {
        if (g_threads[i].state == VT_FREE) {
            g_threads[i].id    = i;
            g_threads[i].state = VT_READY;
            g_threads[i].entry = func;
            g_threads[i].arg   = arg;
            return i;
        }
    }
    return -1;
}

void lmvos_yield(void) {
    int prev = g_current_thread;
    volatile int next = (prev + 1) % MAX_VTHREADS;
    g_system_ticks++;

    while (next != prev) {
        if (g_threads[next].state == VT_SLEEPING && g_system_ticks >= g_threads[next].wake_tick) {
            g_threads[next].state = VT_READY;
        }
        if (g_threads[next].state == VT_READY) break;
        next = (next + 1) % MAX_VTHREADS;
    }
    if (next == prev) return;

    if (setjmp(g_threads[prev].context) == 0) {
        if (g_threads[prev].state == VT_RUNNING) g_threads[prev].state = VT_READY;
        g_current_thread = next;
        g_threads[next].state = VT_RUNNING;
        longjmp(g_threads[next].context, 1);
    }
}

/* Envia um quadro RS-485 completo (2x20 chars + BCC) para o Microterminal */
void lmvos_mterm_send_frame(uint8_t cmd, const char *l1, const char *l2) {
    FRAME_MICROTERMINAL frame;
    const uint8_t *raw = (const uint8_t *)&frame;
    uint8_t bcc = 0;
    size_t i;
    char log_path[1024];
    FILE *flog;

    memset(&frame, ' ', sizeof(frame));
    frame.stx = MTERM_STX;
    frame.cmd = cmd;
    frame.seq = ++g_mterm_seq;

    if (l1) memcpy(frame.linha1, l1, strlen(l1) < 20 ? strlen(l1) : 20);
    if (l2) memcpy(frame.linha2, l2, strlen(l2) < 20 ? strlen(l2) : 20);

    for (i = 1; i < offsetof(FRAME_MICROTERMINAL, bcc); i++) {
        bcc ^= raw[i];
    }
    frame.bcc = bcc;
    frame.etx = MTERM_ETX;

    /* Transmite byte a byte pela UART COM2 (0x02F8) */
    for (i = 0; i < sizeof(frame); i++) {
        while ((inp(0x02FD) & 0x20) == 0) {
            lmvos_yield();
        }
        outp(0x02F8, raw[i]);
    }

    /* Registra espelho visual do LCD do Mesario para inspecao e auditoria */
    ue2000_resolve_path("C:\\MTERM_LCD.LOG", log_path, sizeof(log_path));
    flog = fopen(log_path, "ab");
    if (flog) {
        fprintf(flog, "[SEQ=%03u CMD=0x%02X BCC=0x%02X] | %-20.20s | %-20.20s |\r\n",
                frame.seq, frame.cmd, frame.bcc, frame.linha1, frame.linha2);
        fclose(flog);
    }
}

/* Valida Titulo de Eleitor (12 digitos) segundo algoritmo oficial Modulo-11 TSE */
int lmvos_valida_titulo_tse(const char *titulo12) {
    int pesos1[8] = {2, 3, 4, 5, 6, 7, 8, 9};
    int soma = 0, resto, dv1, dv2, uf;
    int i;

    if (!titulo12 || strlen(titulo12) != 12) return 0;
    for (i = 0; i < 12; i++) {
        if (!isdigit((unsigned char)titulo12[i])) return 0;
    }

    for (i = 0; i < 8; i++) {
        soma += (titulo12[i] - '0') * pesos1[i];
    }
    resto = soma % 11;
    uf = (titulo12[8] - '0') * 10 + (titulo12[9] - '0');
    if (resto == 0) {
        dv1 = (uf == 1 || uf == 2) ? 1 : 0;
    } else if (resto == 10) {
        dv1 = 0;
    } else {
        dv1 = resto;
    }
    if ((titulo12[10] - '0') != dv1) return 0;

    soma = (titulo12[8] - '0') * 7 + (titulo12[9] - '0') * 8 + dv1 * 9;
    resto = soma % 11;
    if (resto == 0) {
        dv2 = (uf == 1 || uf == 2) ? 1 : 0;
    } else if (resto == 10) {
        dv2 = 0;
    } else {
        dv2 = resto;
    }
    return ((titulo12[11] - '0') == dv2) ? 1 : 0;
}
