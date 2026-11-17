#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interface gráfica desktop para o simulador documental UE2000.

Aplicação demonstrativa em Tkinter. Não é software oficial do TSE nem replica
comprovadamente a interface gráfica histórica. Não modifica os arquivos
binários da árvore simulada; grava apenas logs auxiliares da sessão gráfica.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import tkinter as tk
from urllib.request import urlopen
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any


BG = "#202a34"
PANEL = "#2d3945"
PANEL_2 = "#354454"
SCREEN = "#dce7d3"
SCREEN_INK = "#17251d"
SCREEN_MUTED = "#52614f"
ACCENT = "#e4b44f"
BTN_NUM = "#e6e8e9"
BTN_NUM_FG = "#17212b"
BTN_WHITE = "#f7f7f2"
BTN_CORRECT = "#e6a04b"
BTN_CONFIRM = "#39a96b"

def _load_profiles() -> dict[str, list[dict[str, Any]]]:
    """Carrega a base externa; photo_url aceita URL direta de PNG/GIF."""
    data_path = Path(__file__).resolve().with_name("candidatos_2026_sp.json")
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["profiles"]


PROFILES: dict[str, list[dict[str, Any]]] = _load_profiles()



class UrnaGUI:
    def __init__(self, root: tk.Tk, output_dir: Path | None = None):
        self.root = root
        self.root.title("UE2000 — Simulador documental | Interface gráfica")
        self.root.geometry("1220x820")
        self.root.minsize(1080, 740)
        self.root.configure(bg=BG)

        self.output_dir = output_dir or self._default_output_dir()
        self.profile_var = tk.StringVar(value="municipal_2000")
        self.state = "welcome"
        self.profile_key = "municipal_2000"
        self.stages: list[dict[str, Any]] = []
        self.stage_index = 0
        self.digits = ""
        self.selected: dict[str, Any] | None = None
        self.records: list[dict[str, Any]] = []
        self.session_started = ""
        self.session_saved_path: Path | None = None
        self.mterm_line1 = "AGUARDANDO ELEITOR"
        self.mterm_line2 = "SELECIONE UM PERFIL"
        self._build_shell()
        self._bind_keyboard()
        self.render()

    @staticmethod
    def _default_output_dir() -> Path:
        here = Path(__file__).resolve().parent
        env = here / "ambiente_pronto"
        if env.exists():
            return env
        return here

    def _build_shell(self) -> None:
        header = tk.Frame(self.root, bg="#111a23", height=62)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="UE2000", bg="#111a23", fg="#f2f4f5",
                 font=("DejaVu Sans", 21, "bold")).pack(side="left", padx=(24, 14))
        tk.Label(header, text="SIMULADOR DOCUMENTAL · INTERFACE GRÁFICA",
                 bg="#111a23", fg="#b9c6d0", font=("DejaVu Sans", 10, "bold")).pack(side="left")
        tk.Label(header, text="NÃO OFICIAL · AMBIENTE LOCAL",
                 bg="#111a23", fg=ACCENT, font=("DejaVu Sans", 9, "bold")).pack(side="right", padx=24)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=18, pady=16)
        main.grid_columnconfigure(0, weight=7)
        main.grid_columnconfigure(1, weight=4)
        main.grid_rowconfigure(0, weight=1)

        # Monitor / visor do eleitor
        left = tk.Frame(main, bg="#111820", bd=0, highlightthickness=1,
                        highlightbackground="#506070")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)
        monitor_top = tk.Frame(left, bg="#111820")
        monitor_top.grid(row=0, column=0, sticky="ew", padx=18, pady=(12, 9))
        tk.Label(monitor_top, text="VISOR DO ELEITOR", bg="#111820", fg="#d8e1e7",
                 font=("DejaVu Sans", 10, "bold")).pack(side="left")
        tk.Label(monitor_top, text="TELA 4:3 · RECONSTRUÇÃO VISUAL", bg="#111820", fg="#8594a1",
                 font=("DejaVu Sans", 8)).pack(side="right")

        bezel = tk.Frame(left, bg="#34414c", padx=13, pady=13)
        bezel.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        bezel.grid_rowconfigure(0, weight=1)
        bezel.grid_columnconfigure(0, weight=1)
        self.screen = tk.Frame(bezel, bg=SCREEN, padx=25, pady=18,
                               highlightthickness=2, highlightbackground="#a5b49a")
        self.screen.grid(row=0, column=0, sticky="nsew")
        self.screen.grid_columnconfigure(0, weight=1)

        foot = tk.Frame(left, bg="#111820")
        foot.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        tk.Label(foot, text="TECLADO VIRTUAL E TECLAS DO COMPUTADOR ATIVOS",
                 bg="#111820", fg="#97a4af", font=("DejaVu Sans", 8)).pack(side="left")
        tk.Label(foot, text="F = CONFIRMA  ·  C = CORRIGE  ·  B = BRANCO",
                 bg="#111820", fg="#97a4af", font=("DejaVu Sans", 8)).pack(side="right")

        # Side: setup, microterminal and physical keypad
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        setup = tk.Frame(right, bg=PANEL, padx=16, pady=12)
        setup.pack(fill="x", pady=(0, 12))
        tk.Label(setup, text="CONFIGURAÇÃO DA SESSÃO", bg=PANEL, fg="#eff3f6",
                 font=("DejaVu Sans", 10, "bold")).pack(anchor="w", pady=(0, 7))
        self.profile_municipal = tk.Radiobutton(
            setup, text="Municipal 2000 · Vereador + Prefeito",
            variable=self.profile_var, value="municipal_2000", command=self._profile_changed,
            bg=PANEL, fg="#e5edf2", selectcolor="#18232d", activebackground=PANEL,
            activeforeground="white", font=("DejaVu Sans", 9), wraplength=310, justify="left")
        self.profile_municipal.pack(anchor="w", pady=2)
        self.profile_general = tk.Radiobutton(
            setup, text="Eleições 2026 · São Paulo (6 votos)",
            variable=self.profile_var, value="eleicoes_2026_sp", command=self._profile_changed,
            bg=PANEL, fg="#e5edf2", selectcolor="#18232d", activebackground=PANEL,
            activeforeground="white", font=("DejaVu Sans", 9), wraplength=310, justify="left")
        self.profile_general.pack(anchor="w", pady=2)
        self.start_button = tk.Button(setup, text="INICIAR SESSÃO", command=self.start_session,
                                      bg=ACCENT, fg="#17212b", activebackground="#f0c66c",
                                      relief="flat", font=("DejaVu Sans", 10, "bold"),
                                      padx=12, pady=8, cursor="hand2")
        self.start_button.pack(fill="x", pady=(9, 0))

        mterm = tk.Frame(right, bg="#111820", padx=12, pady=10)
        mterm.pack(fill="x", pady=(0, 12))
        tk.Label(mterm, text="MICROTERMINAL DO MESÁRIO · SIMULADO",
                 bg="#111820", fg="#cbd5dc", font=("DejaVu Sans", 8, "bold")).pack(anchor="w")
        lcd = tk.Frame(mterm, bg="#c5d4b8", padx=10, pady=7,
                       highlightthickness=1, highlightbackground="#71816a")
        lcd.pack(fill="x", pady=(7, 8))
        self.mterm_var1 = tk.StringVar(value=self.mterm_line1)
        self.mterm_var2 = tk.StringVar(value=self.mterm_line2)
        tk.Label(lcd, textvariable=self.mterm_var1, bg="#c5d4b8", fg="#263525",
                 anchor="w", font=("DejaVu Sans Mono", 9, "bold")).pack(fill="x")
        tk.Label(lcd, textvariable=self.mterm_var2, bg="#c5d4b8", fg="#263525",
                 anchor="w", font=("DejaVu Sans Mono", 9)).pack(fill="x")
        self.release_button = tk.Button(mterm, text="LIBERAR ELEITOR", command=self.release_voter,
                                        bg="#4c6f86", fg="white", activebackground="#5f89a5",
                                        relief="flat", font=("DejaVu Sans", 9, "bold"),
                                        padx=8, pady=7, cursor="hand2", state="disabled")
        self.release_button.pack(fill="x")

        keypad_box = tk.Frame(right, bg=PANEL, padx=14, pady=12)
        keypad_box.pack(fill="both", expand=True)
        tk.Label(keypad_box, text="TECLADO DO ELEITOR", bg=PANEL, fg="#eff3f6",
                 font=("DejaVu Sans", 10, "bold")).pack(anchor="w", pady=(0, 9))
        grid = tk.Frame(keypad_box, bg=PANEL)
        grid.pack(fill="both", expand=True)
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1, uniform="keycol")
        for r in range(4):
            grid.grid_rowconfigure(r, weight=1, uniform="keyrow")
        key_layout = [["1", "2", "3"], ["4", "5", "6"],
                      ["7", "8", "9"], ["BRANCO", "0", "CORRIGE"]]
        self.digit_buttons: list[tk.Button] = []
        self.action_buttons: dict[str, tk.Button] = {}
        for r, row in enumerate(key_layout):
            for c, key in enumerate(row):
                is_white = key == "BRANCO"
                is_correct = key == "CORRIGE"
                bg = BTN_WHITE if is_white else (BTN_CORRECT if is_correct else BTN_NUM)
                fg = BTN_NUM_FG
                label = "BRANCO" if is_white else ("CORRIGE" if is_correct else key)
                font_size = 9 if (is_white or is_correct) else 17
                cmd = self.press_blank if is_white else (self.press_correct if is_correct else lambda k=key: self.press_digit(k))
                btn = tk.Button(grid, text=label, command=cmd, bg=bg, fg=fg,
                                activebackground=bg, activeforeground=fg,
                                relief="raised", bd=2, font=("DejaVu Sans", font_size, "bold"),
                                cursor="hand2")
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4, ipadx=2, ipady=8)
                if key.isdigit():
                    self.digit_buttons.append(btn)
                else:
                    self.action_buttons[key] = btn
        self.confirm_button = tk.Button(keypad_box, text="CONFIRMA", command=self.press_confirm,
                                        bg=BTN_CONFIRM, fg="#102319", activebackground="#55c381",
                                        relief="raised", bd=2, font=("DejaVu Sans", 12, "bold"),
                                        cursor="hand2", pady=10)
        self.confirm_button.pack(fill="x", pady=(10, 0))
        self.restart_button = tk.Button(right, text="NOVA SESSÃO / REINICIAR",
                                        command=self.reset_session, bg=PANEL_2, fg="#e9eff4",
                                        activebackground="#465b70", relief="flat",
                                        font=("DejaVu Sans", 9, "bold"), pady=8, cursor="hand2")
        self.restart_button.pack(fill="x", pady=(12, 0))

        self.footer_var = tk.StringVar(value="Pronto para iniciar. Os dados de candidatos são fictícios.")
        footer = tk.Label(self.root, textvariable=self.footer_var, bg="#111a23", fg="#abb8c2",
                          anchor="w", padx=18, pady=7, font=("DejaVu Sans", 8))
        footer.pack(fill="x", side="bottom")

    def _bind_keyboard(self) -> None:
        self.root.bind("<Key>", self.on_key)

    def on_key(self, event: tk.Event) -> None:
        key = event.char
        if key in "0123456789" and key:
            self.press_digit(key)
        elif key.lower() == "b":
            self.press_blank()
        elif key.lower() == "c":
            self.press_correct()
        elif key.lower() == "f" or event.keysym in ("Return", "KP_Enter"):
            self.press_confirm()

    def _profile_changed(self) -> None:
        if self.state == "welcome":
            self.render()

    def start_session(self, profile: str | None = None) -> None:
        self.profile_key = profile or self.profile_var.get()
        self.stages = copy.deepcopy(PROFILES[self.profile_key])
        self.stage_index = 0
        self.digits = ""
        self.selected = None
        self.records = []
        self.session_started = datetime.now().astimezone().isoformat(timespec="seconds")
        self.session_saved_path = None
        self.state = "await_release"
        if self.profile_key == "municipal_2000":
            self._set_mterm("AGUARDE A LIBERACAO", "VOTACAO MUNICIPAL")
        else:
            self._set_mterm("AGUARDE A LIBERACAO", "ELEICOES 2026 SP")
        self.footer_var.set("Sessão iniciada. O mesário simulado deve liberar o eleitor.")
        self.render()

    def release_voter(self) -> None:
        if self.state != "await_release":
            return
        self.state = "voting"
        self.digits = ""
        self.selected = None
        stage = self.stages[self.stage_index]
        self._set_mterm("ELEITOR LIBERADO", stage["title"][:20])
        self.footer_var.set("Eleitor liberado. Use os botões na tela ou o teclado físico.")
        self.render()

    def press_digit(self, digit: str) -> None:
        if self.state != "voting" or len(self.digits) >= self.current_stage["digits"]:
            return
        self.digits += digit
        self.selected = None
        self.render()
        expected = self.current_stage["digits"]
        if len(self.digits) == expected:
            candidate = self.current_stage["candidates"].get(self.digits)
            if candidate:
                self.selected = {"number": self.digits, **candidate}
                self.state = "review"
                self._set_mterm("CONFIRA O VOTO", self.current_stage["title"][:20])
            else:
                self.state = "invalid"
                self._set_mterm("NUMERO NAO LOCALIZADO", "CORRIJA A DIGITACAO")
            self.render()

    def press_blank(self) -> None:
        if self.state == "voting":
            self.state = "blank_review"
            self.selected = None
            self._set_mterm("VOTO EM BRANCO", self.current_stage["title"][:20])
            self.render()

    def press_correct(self) -> None:
        if self.state == "review" or self.state == "blank_review" or self.state == "invalid":
            self.state = "voting"
            self.digits = ""
            self.selected = None
        elif self.state == "voting" and self.digits:
            self.digits = self.digits[:-1]
        self.render()

    def press_confirm(self) -> None:
        if self.state == "review" and self.selected:
            stage = self.current_stage
            self.records.append({"cargo": stage["title"], "tipo": "nominal",
                                 "numero": self.selected["number"],
                                 "nome": self.selected["name"], "partido": self.selected["party"]})
            self._advance()
        elif self.state == "blank_review":
            self.records.append({"cargo": self.current_stage["title"], "tipo": "branco"})
            self._advance()

    @property
    def current_stage(self) -> dict[str, Any]:
        return self.stages[self.stage_index]

    def _advance(self) -> None:
        self.stage_index += 1
        self.digits = ""
        self.selected = None
        if self.stage_index >= len(self.stages):
            self.state = "done"
            self._set_mterm("VOTACAO ENCERRADA", "OBRIGADO")
            self._save_session()
            self.footer_var.set("Fim da sessão. Arquivo de demonstração salvo localmente.")
        else:
            self.state = "voting"
            next_stage = self.current_stage
            if next_stage["title"] == "SENADOR - 2ª VAGA":
                first_senator = next((r.get("numero") for r in self.records if r.get("cargo") == "SENADOR - 1ª VAGA" and r.get("tipo") == "nominal"), None)
                if first_senator:
                    next_stage["candidates"].pop(first_senator, None)
            self._set_mterm("PROXIMO CARGO", next_stage["title"][:20])
            self.footer_var.set(f"Voto registrado no simulador. Próximo cargo: {next_stage['title']}.")
        self.render()

    def _set_mterm(self, line1: str, line2: str) -> None:
        self.mterm_line1, self.mterm_line2 = line1[:20], line2[:20]
        if hasattr(self, "mterm_var1"):
            self.mterm_var1.set(self.mterm_line1)
            self.mterm_var2.set(self.mterm_line2)
        try:
            log_dir = self.output_dir / "FI_C"
            log_dir.mkdir(parents=True, exist_ok=True)
            with (log_dir / "MTERM_GUI.LOG").open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat(timespec='seconds')}|{self.mterm_line1}|{self.mterm_line2}\n")
        except OSError:
            pass

    def _save_session(self) -> None:
        try:
            out = self.output_dir / "FI_C" / "aplic" / "SESSOES_GUI"
            out.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = out / f"sessao_{stamp}.json"
            payload = {
                "tipo": "SIMULACAO_DOCUMENTAL_NAO_OFICIAL",
                "perfil": self.profile_key,
                "inicio": self.session_started,
                "fim": datetime.now().astimezone().isoformat(timespec="seconds"),
                "votos": self.records,
                "observacao": "Dados ficticios; arquivo auxiliar de interface, nao e BU eleitoral nem artefato oficial.",
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.session_saved_path = path
        except OSError as exc:
            self.footer_var.set(f"Sessão concluída; não foi possível salvar o log: {exc}")

    def reset_session(self) -> None:
        self.state = "welcome"
        self.stage_index = 0
        self.digits = ""
        self.selected = None
        self.stages = []
        self.records = []
        self.session_saved_path = None
        self._set_mterm("AGUARDANDO ELEITOR", "SELECIONE UM PERFIL")
        self.footer_var.set("Pronto para iniciar. Os dados de candidatos são fictícios.")
        self.render()

    def render(self) -> None:
        for child in self.screen.winfo_children():
            child.destroy()
        self.screen.configure(bg=SCREEN)
        self._screen_next_row = 4

        top = tk.Frame(self.screen, bg=SCREEN)
        top.grid(row=0, column=0, sticky="ew")
        tk.Label(top, text="JUSTIÇA ELEITORAL", bg=SCREEN, fg=SCREEN_INK,
                 font=("DejaVu Sans", 10, "bold")).pack(side="left")
        tk.Label(top, text="SIMULADOR NÃO OFICIAL", bg=SCREEN, fg=SCREEN_MUTED,
                 font=("DejaVu Sans", 8, "bold")).pack(side="right")
        tk.Frame(self.screen, bg="#84947c", height=2).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        if self.state == "welcome":
            self._screen_heading("SIMULADOR DE VOTAÇÃO", "RECONSTRUÇÃO DOCUMENTAL")
            self._screen_center("Selecione o perfil no painel lateral e clique em INICIAR SESSÃO.", 15)
            self._screen_center("Os nomes, partidos e números da demonstração são fictícios.", 10, SCREEN_MUTED)
            self._screen_center("A interface gráfica é uma reconstrução; não é a tela original autenticada.", 9, SCREEN_MUTED)
            self._screen_spacer()
            self._screen_center("PRONTO PARA INICIAR", 13, SCREEN_INK, bold=True)
        elif self.state == "await_release":
            profile_name = "ELEIÇÃO MUNICIPAL 2000" if self.profile_key == "municipal_2000" else "ELEIÇÕES GERAIS · MODELO 2022"
            self._screen_heading(profile_name, "AGUARDE A LIBERAÇÃO DO MESÁRIO")
            self._screen_center("A votação começará quando o mesário clicar em", 12)
            self._screen_center("LIBERAR ELEITOR", 17, SCREEN_INK, bold=True)
            self._screen_center("O terminal do mesário é mostrado separadamente à direita.", 10, SCREEN_MUTED)
        elif self.state in ("voting", "review", "blank_review", "invalid"):
            stage = self.current_stage
            self._screen_heading(f"VOTAÇÃO PARA {stage['title']}", f"DIGITE O NÚMERO · {stage['digits']} DÍGITOS")
            self._screen_center("NÚMERO", 9, SCREEN_MUTED, bold=True)
            number = self.digits.ljust(stage["digits"], "_")
            self._screen_center("   ".join(number), 25, SCREEN_INK, bold=True, family="DejaVu Sans Mono")
            if self.state == "review" and self.selected:
                self._screen_candidate(self.selected)
                self._screen_center("APERTE CONFIRMA PARA REGISTRAR", 11, SCREEN_INK, bold=True)
                self._screen_center("OU CORRIGE PARA ALTERAR O NÚMERO", 9, SCREEN_MUTED)
            elif self.state == "blank_review":
                self._screen_center("VOTO EM BRANCO", 22, SCREEN_INK, bold=True)
                self._screen_center("CONFIRMA para registrar · CORRIGE para voltar", 10, SCREEN_MUTED)
            elif self.state == "invalid":
                self._screen_center("NÚMERO NÃO ENCONTRADO", 16, "#963d30", bold=True)
                self._screen_center("Pressione CORRIGE e tente novamente.", 10, SCREEN_MUTED)
            else:
                self._screen_center("Use o teclado numérico. Para voto em branco, pressione BRANCO.", 10, SCREEN_MUTED)
            self._screen_spacer()
            tk.Label(self.screen, text=f"CARGO {self.stage_index + 1} DE {len(self.stages)}",
                     bg=SCREEN, fg=SCREEN_MUTED, font=("DejaVu Sans", 8, "bold")).grid(row=99, column=0, sticky="w")
        elif self.state == "done":
            self._screen_heading("FIM", "VOTAÇÃO ENCERRADA")
            self._screen_center("OBRIGADO POR VOTAR", 20, SCREEN_INK, bold=True)
            self._screen_center(f"{len(self.records)} votos simulados registrados", 11)
            self._screen_center("A sessão foi salva em arquivo auxiliar local.", 10, SCREEN_MUTED)
            self._screen_spacer()
            self._screen_center("CLIQUE EM NOVA SESSÃO PARA RECOMEÇAR", 10, SCREEN_INK, bold=True)

        self.release_button.configure(state=("normal" if self.state == "await_release" else "disabled"))
        # Teclas numéricas só aceitam entrada durante a digitação.
        for button in self.digit_buttons:
            button.configure(state=("normal" if self.state == "voting" else "disabled"))
        self.action_buttons["BRANCO"].configure(state=("normal" if self.state == "voting" else "disabled"))
        self.action_buttons["CORRIGE"].configure(state=("normal" if self.state in ("voting", "review", "blank_review", "invalid") else "disabled"))
        self.confirm_button.configure(state=("normal" if self.state in ("review", "blank_review") else "disabled"))
        self.start_button.configure(state=("normal" if self.state == "welcome" else "disabled"))
        profile_state = "normal" if self.state == "welcome" else "disabled"
        self.profile_municipal.configure(state=profile_state)
        self.profile_general.configure(state=profile_state)

    def _screen_heading(self, title: str, subtitle: str) -> None:
        tk.Label(self.screen, text=title, bg=SCREEN, fg=SCREEN_INK,
                 font=("DejaVu Sans", 17, "bold")).grid(row=2, column=0, sticky="w", pady=(4, 3))
        tk.Label(self.screen, text=subtitle, bg=SCREEN, fg=SCREEN_MUTED,
                 font=("DejaVu Sans", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 16))

    def _screen_center(self, text: str, size: int, color: str = SCREEN_INK,
                       bold: bool = False, family: str = "DejaVu Sans") -> None:
        row = self._screen_next_row
        self._screen_next_row += 1
        tk.Label(self.screen, text=text, bg=SCREEN, fg=color,
                 font=(family, size, "bold" if bold else "normal"),
                 justify="center", wraplength=630).grid(row=row, column=0, sticky="ew", pady=5)

    def _screen_spacer(self) -> None:
        row = self._screen_next_row
        self._screen_next_row += 1
        tk.Frame(self.screen, bg=SCREEN, height=18).grid(row=row, column=0)

    def _screen_candidate(self, candidate: dict[str, Any]) -> None:
        card = tk.Frame(self.screen, bg="#edf2e9", highlightthickness=1, highlightbackground="#9da993", padx=13, pady=10)
        row = self._screen_next_row
        self._screen_next_row += 1
        card.grid(row=row, column=0, sticky="ew", pady=(12, 7))
        card.grid_columnconfigure(1, weight=1)
        portrait = tk.Canvas(card, width=92, height=112, bg="#c5d3c0", highlightthickness=1,
                             highlightbackground="#8d9c87")
        portrait.grid(row=0, column=0, rowspan=4, padx=(0, 14))
        portrait.create_oval(29, 13, 64, 49, fill="#e9dfcd", outline="#77846f", width=2)
        portrait.create_arc(19, 39, 75, 109, start=0, extent=180, fill="#647e72", outline="#647e72")
        photo_loaded = False
        photo_url = candidate.get("photo_url", "").strip()
        if photo_url:
            try:
                with urlopen(photo_url, timeout=4) as response:
                    encoded = base64.b64encode(response.read()).decode("ascii")
                photo = tk.PhotoImage(data=encoded)
                photo = photo.subsample(max(1, photo.width() // 92), max(1, photo.height() // 112))
                portrait.create_image(46, 56, image=photo)
                portrait.image = photo
                photo_loaded = True
            except Exception:
                pass
        if not photo_loaded:
            portrait.create_oval(29, 13, 64, 49, fill="#e9dfcd", outline="#77846f", width=2)
            portrait.create_arc(19, 39, 75, 109, start=0, extent=180, fill="#647e72", outline="#647e72")
            portrait.create_text(46, 96, text=candidate.get("initials", "??"), fill="white",
                                 font=("DejaVu Sans", 10, "bold"))
        tk.Label(card, text=candidate["name"], bg="#edf2e9", fg=SCREEN_INK,
                 font=("DejaVu Sans", 14, "bold"), anchor="w").grid(row=0, column=1, sticky="ew", pady=(3, 6))
        tk.Label(card, text=f"NÚMERO: {candidate['number']}", bg="#edf2e9", fg=SCREEN_INK,
                 font=("DejaVu Sans Mono", 11, "bold"), anchor="w").grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(card, text=f"PARTIDO: {candidate['party']}", bg="#edf2e9", fg=SCREEN_INK,
                 font=("DejaVu Sans", 10), anchor="w").grid(row=2, column=1, sticky="ew", pady=2)
        if candidate.get("vice"):
            tk.Label(card, text=f"VICE / SUPLENTE DEMO: {candidate['vice']}", bg="#edf2e9", fg=SCREEN_MUTED,
                     font=("DejaVu Sans", 9), anchor="w").grid(row=3, column=1, sticky="ew", pady=2)


def run_self_test() -> None:
    """Teste automatizado do fluxo de ambos os perfis sem exibir janela."""
    import tempfile
    root = tk.Tk()
    root.withdraw()
    with tempfile.TemporaryDirectory(prefix="ue2000_gui_test_") as tmp:
        app = UrnaGUI(root, Path(tmp))
        # municipal: dois votos nominais
        app.start_session("municipal_2000")
        app.release_voter()
        for d in "91001": app.press_digit(d)
        assert app.state == "review", app.state
        app.press_confirm()
        for d in "91": app.press_digit(d)
        assert app.state == "review", app.state
        app.press_confirm()
        assert app.state == "done", app.state
        assert len(app.records) == 2
        # perfil geral: cinco cargos, incluindo deputado, senador e presidente
        app.start_session("eleicoes_2026_sp")
        app.release_voter()
        for number in ("3030", "50500", "111", "222", "10", "13"):
            for d in number: app.press_digit(d)
            assert app.state == "review", (number, app.state)
            app.press_confirm()
        assert app.state == "done", app.state
        assert [r["cargo"] for r in app.records] == [
            "DEPUTADO FEDERAL", "DEPUTADO ESTADUAL", "SENADOR - 1ª VAGA", "SENADOR - 2ª VAGA", "GOVERNADOR", "PRESIDENTE"]
        # branco + correção
        app.start_session("municipal_2000")
        app.release_voter()
        app.press_blank()
        assert app.state == "blank_review"
        app.press_correct()
        assert app.state == "voting"
        for d in "91001": app.press_digit(d)
        app.press_correct()
        assert app.state == "voting" and app.digits == ""
    root.destroy()
    print("GUI SELF-TEST: OK — perfis municipal e geral, branco e correção.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface gráfica do simulador documental UE2000")
    parser.add_argument("--self-test", action="store_true", help="executa testes automatizados da lógica de interface")
    parser.add_argument("--output-dir", type=Path, default=None, help="pasta onde salvar logs auxiliares")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return
    root = tk.Tk()
    UrnaGUI(root, args.output_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
