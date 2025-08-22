import os
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import urwid
from dotenv import load_dotenv

from clients.project_client import ProjectClientFactory
from services.env_service import (
    ensure_env_file,
    read_env,
    set_env_var,
)
from services.inference_service import InferenceService
from services.projects_service import ProjectsService

from ui.screens import EnterEdit, menu_screen, message_screen


@dataclass
class AppState:
    vector_store_name: Optional[str] = None
    error_msg: Optional[str] = None


class App:
    def __init__(self) -> None:
        if not os.path.exists("logs"):
            os.makedirs("logs")
        log_filename = (
            f"logs/rag_management_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_filename, encoding="utf-8")],
        )
        logging.getLogger("azure").setLevel(logging.WARNING)
        logging.getLogger("azure.identity").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        load_dotenv()
        ensure_env_file()

        self.palette = [("reversed", "standout", "")]
        self.main = urwid.WidgetPlaceholder(urwid.SolidFill())
        self.screen = urwid.raw_display.Screen()
        self.loop = urwid.MainLoop(
            self.main,
            self.palette,
            screen=self.screen,
            event_loop=urwid.AsyncioEventLoop(),
        )

        self.client_factory = ProjectClientFactory()
        self.projects_service = (
            ProjectsService()
        )  # now uses repository adapter internally
        self.inference_service = InferenceService()
        self.state = AppState()

        endpoint = os.environ.get("PROJECT_ENDPOINT")
        try:
            if not endpoint:
                self.state.error_msg = "A variável PROJECT_ENDPOINT não está definida ou não foi alterada no .env."
            else:
                self.client_factory.configure(endpoint)
                client = self.client_factory.get()
                self.projects_service.set_client(client)
        except Exception as e:  # noqa: BLE001
            self.state.error_msg = f"Erro de autenticação: {e}"

    def run(self) -> None:
        try:
            self.show_main_menu()
            self.loop.run()
        finally:
            self.screen.clear()

    def redraw(self) -> None:
        try:
            urwid.MainLoop(self.main, self.palette).draw_screen()
        except Exception:  # noqa: BLE001
            pass

    def show_main_menu(self, button: Optional[urwid.Button] = None) -> None:
        if self.state.error_msg:
            self.main.original_widget = message_screen(
                self.state.error_msg, self.show_main_menu
            )
            return

        user_name, organization = self.client_factory.get_user_info()
        welcome_text = "--- Menu Principal ---"
        if user_name and organization:
            welcome_text = f"Seja bem-vindo {user_name} da {organization}!"
        elif user_name:
            welcome_text = f"Seja bem-vindo {user_name}!"

        header = [urwid.Text(welcome_text, align="center"), urwid.Divider()]
        current_vs = (
            self.state.vector_store_name or "Nenhum (selecione em 'Vector Stores')"
        )
        header.append(urwid.Text(f"Vector Store atual: {current_vs}", align="center"))
        header.append(urwid.Divider())
        items = {
            "Conectar": self.show_connect,
            "Vector Stores": self.show_vector_stores,
            "Arquivos: Listar/Pesquisar": self.show_files_search,
            "Arquivos: Incluir": self.show_file_add,
            "Agentes": self.show_agents_stub,
            "Chat": self.show_chat_stub,
            "Utilidades": self.show_utilities,
            "Sair": self.exit,
        }
        footer = None
        self.main.original_widget = menu_screen(welcome_text, items, footer)

    def exit(self, button: Optional[urwid.Button] = None) -> None:
        raise urwid.ExitMainLoop()

    def back(self, button: Optional[urwid.Button] = None) -> None:
        self.show_main_menu()

    def show_connect(self, button: Optional[urwid.Button] = None) -> None:
        env = read_env()
        endpoint = env.get("PROJECT_ENDPOINT") or ""
        status = "Configurado" if self.client_factory.endpoint() else "Não configurado"
        result_text = urwid.Text("")

        def on_save(widget: urwid.Edit) -> None:
            value = edit.edit_text.strip()
            set_env_var("PROJECT_ENDPOINT", value)
            result_text.set_text("Salvo no .env. Reconfigurando...")

            def do_reconfig(loop, user_data) -> None:
                try:
                    self.client_factory.configure(value)
                    client = self.client_factory.get()
                    self.projects_service.set_client(client)
                    result_text.set_text("Reconfigurado com sucesso.")
                    self.state.error_msg = None
                except Exception as e:  # noqa: BLE001
                    self.state.error_msg = f"Erro de autenticação: {e}"
                    result_text.set_text(self.state.error_msg)

            self.loop.set_alarm_in(0, do_reconfig)

        edit = EnterEdit("PROJECT_ENDPOINT: ", edit_text=endpoint, on_enter=on_save)
        save_btn = urwid.Button("Salvar e Reconfigurar")
        urwid.connect_signal(save_btn, "click", lambda btn: on_save(edit))

        pile = urwid.Pile(
            [
                urwid.Text("Conectar ao Projeto", align="center"),
                urwid.Divider(),
                urwid.Text(f"Status: {status}", align="center"),
                urwid.Divider(),
                edit,
                urwid.AttrMap(save_btn, None, focus_map="reversed"),
                urwid.Divider(),
                result_text,
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                ),
            ]
        )
        self.main.original_widget = urwid.Filler(pile, valign="top", top=2, bottom=2)

    def show_utilities(self, button: Optional[urwid.Button] = None) -> None:
        env = read_env()
        lines = [f"{k}={v}" for k, v in env.items()]
        text = urwid.Text("\n".join(lines) or "(vazio)")
        back = urwid.AttrMap(
            urwid.Button("Voltar", self.back), None, focus_map="reversed"
        )
        pile = urwid.Pile(
            [urwid.Text(".env atual"), urwid.Divider(), text, urwid.Divider(), back]
        )
        self.main.original_widget = urwid.Filler(pile, valign="top", top=1)

    def show_agents_stub(self, button: Optional[urwid.Button] = None) -> None:
        pile = urwid.Pile(
            [
                urwid.Text("Agentes (stub)", align="center"),
                urwid.Divider(),
                urwid.Text("Em breve."),
                urwid.Divider(),
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                ),
            ]
        )
        self.main.original_widget = urwid.Filler(pile, valign="middle")

    def show_chat_stub(self, button: Optional[urwid.Button] = None) -> None:
        status = urwid.Text("")

        def on_send(widget: urwid.Edit) -> None:
            msg = widget.edit_text
            status.set_text("Enviando...")

            def do_send(loop, user_data) -> None:
                ok, resp = self.inference_service.send_message(msg)
                status.set_text(resp if ok else f"Erro: {resp}")

            self.loop.set_alarm_in(0, do_send)

        edit = EnterEdit("Mensagem: ", on_enter=on_send)
        send_btn = urwid.Button("Enviar")
        urwid.connect_signal(send_btn, "click", lambda btn: on_send(edit))
        cfg_btn = urwid.Button("Configurar Stub")

        def on_cfg(btn) -> None:
            self.inference_service.configure(model="dummy")
            status.set_text("Stub configurado.")

        urwid.connect_signal(cfg_btn, "click", on_cfg)

        pile = urwid.Pile(
            [
                urwid.Text("Chat (stub)", align="center"),
                urwid.Divider(),
                edit,
                urwid.AttrMap(send_btn, None, focus_map="reversed"),
                urwid.AttrMap(cfg_btn, None, focus_map="reversed"),
                urwid.Divider(),
                status,
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                ),
            ]
        )
        self.main.original_widget = urwid.Filler(pile, valign="top", top=2, bottom=2)

    def show_vector_stores(self, button: Optional[urwid.Button] = None) -> None:
        body = [
            urwid.Text("Selecione um Vector Store:", align="center"),
            urwid.Divider(),
        ]

        def fill_body(loop, user_data) -> None:
            try:
                stores = list(self.projects_service.list_vector_stores())
                if not stores:
                    body.append(urwid.Text("Nenhum Vector Store encontrado."))
                else:
                    for vs in stores:
                        label = f"{vs.name} (ID: {vs.id})"
                        btn = urwid.Button(label)
                        urwid.connect_signal(
                            btn,
                            "click",
                            lambda _b, store=vs: on_select_vector_store(store),
                        )
                        body.append(urwid.AttrMap(btn, None, focus_map="reversed"))
            except Exception as e:  # noqa: BLE001
                body.append(urwid.Text(str(e)))
            body.append(urwid.Divider())
            body.append(
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                )
            )
            pile = urwid.Pile(body)
            self.main.original_widget = urwid.Filler(pile, valign="middle")

        def on_select_vector_store(store) -> None:
            self.projects_service.set_vector_store(store)
            self.state.vector_store_name = getattr(store, "name", None) or store.name
            self.main.original_widget = message_screen(
                f"Vector Store selecionado: {self.state.vector_store_name}", self.back
            )

        self.loop.set_alarm_in(0, fill_body)
        self.main.original_widget = urwid.Filler(urwid.Pile(body), valign="middle")

    def show_files_search(self, button: Optional[urwid.Button] = None) -> None:
        if not self.projects_service.vector_store_id:
            self.main.original_widget = message_screen(
                "Nenhum Vector Store selecionado. Use 'Vector Stores' primeiro.",
                self.back,
            )
            return
        result_text = urwid.Text("")

        def on_search(widget: urwid.Edit) -> None:
            search_term = widget.edit_text.strip().lower()
            result_text.set_text("Executando...")

            def do_search(loop, user_data) -> None:
                try:
                    file_map = self.projects_service.list_vector_store_files()
                    matching = [
                        d
                        for d in file_map.values()
                        if not search_term or search_term in d.filename.lower()
                    ]
                    if matching:
                        result = f"Resultados ({len(matching)}):" + "\n".join(
                            [f"- {f.filename} (ID: {f.id})" for f in matching]
                        )
                    else:
                        result = "Nenhum arquivo encontrado."
                except Exception as e:  # noqa: BLE001
                    result = f"Erro ao buscar arquivos: {e}"
                result_text.set_text(result)

            self.loop.set_alarm_in(0, do_search)

        edit = EnterEdit(
            "Digite parte do nome (Enter para pesquisar/listar): ", on_enter=on_search
        )
        search_btn = urwid.Button("Pesquisar/Listar")
        urwid.connect_signal(search_btn, "click", lambda btn: on_search(edit))

        pile = urwid.Pile(
            [
                edit,
                urwid.AttrMap(search_btn, None, focus_map="reversed"),
                urwid.Divider(),
                result_text,
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                ),
            ]
        )
        self.main.original_widget = urwid.Padding(
            urwid.Filler(pile, valign="top", top=2, bottom=2), left=2, right=2
        )

    def show_file_add(self, button: Optional[urwid.Button] = None) -> None:
        if not self.projects_service.vector_store_id:
            self.main.original_widget = message_screen(
                "Nenhum Vector Store selecionado. Use 'Vector Stores' primeiro.",
                self.back,
            )
            return
        result_text = urwid.Text("")

        def on_add(widget: urwid.Edit) -> None:
            file_path = widget.edit_text.strip()
            if not file_path:
                result_text.set_text("O caminho do arquivo não pode ser vazio.")
                self.redraw()
                return
            if not os.path.isfile(file_path):
                result_text.set_text(f"Arquivo não encontrado em: {file_path}")
                self.redraw()
                return
            result_text.set_text("Executando...")

            def do_add(loop, user_data) -> None:
                ok, msg = self.projects_service.upload_and_attach_file(file_path)
                result_text.set_text(msg)
                if ok:
                    widget.set_edit_text("")

            self.loop.set_alarm_in(0, do_add)

        edit = EnterEdit(
            "Digite o caminho do arquivo (Enter para incluir): ", on_enter=on_add
        )
        add_btn = urwid.Button("Incluir")
        urwid.connect_signal(add_btn, "click", lambda btn: on_add(edit))

        pile = urwid.Pile(
            [
                edit,
                urwid.AttrMap(add_btn, None, focus_map="reversed"),
                urwid.Divider(),
                result_text,
                urwid.AttrMap(
                    urwid.Button("Voltar", self.back), None, focus_map="reversed"
                ),
            ]
        )
        self.main.original_widget = urwid.Padding(
            urwid.Filler(pile, valign="top", top=2, bottom=2), left=2, right=2
        )
