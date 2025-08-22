import urwid
from typing import Callable, Dict, Optional


class EnterEdit(urwid.Edit):
    def __init__(
        self, *args, on_enter: Optional[Callable[[urwid.Edit], None]] = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.on_enter = on_enter

    def keypress(self, size, key):
        if key == "enter" and self.on_enter:
            self.on_enter(self)
            return None
        return super().keypress(size, key)


def message_screen(
    msg: str, on_back: Callable[[Optional[urwid.Button]], None]
) -> urwid.Widget:
    pile = urwid.Pile(
        [
            urwid.Text(msg, align="center"),
            urwid.Divider(),
            urwid.Button("Voltar", on_back),
        ]
    )
    return urwid.Filler(pile, valign="middle")


def menu_screen(
    title: str,
    items: Dict[str, Callable[[Optional[urwid.Button]], None]],
    footer: Optional[urwid.Widget] = None,
) -> urwid.Widget:
    body = [urwid.Text(title, align="center"), urwid.Divider()]
    for label, cb in items.items():
        btn = urwid.Button(label)
        urwid.connect_signal(btn, "click", cb)
        body.append(urwid.AttrMap(btn, None, focus_map="reversed"))
    if footer is not None:
        body.append(urwid.Divider())
        body.append(footer)
    pile = urwid.Pile(body)
    return urwid.Filler(pile, valign="middle")
