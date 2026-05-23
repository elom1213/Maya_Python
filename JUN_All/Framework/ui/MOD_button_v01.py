import maya.cmds as cmds
from functools import partial
from dataclasses import dataclass, field
from typing import Callable, Optional

# from Framework.ui import JUN_buttonSpec


class Buttons:
    def __init__(self, btn_spec = None):
        self.btn_spec = btn_spec

        self.label              = self.btn_spec.label
        self.height             = self.btn_spec.height
        self.width              = self.btn_spec.width
        self.backgroundcolor    = self.btn_spec.backgroundcolor

        self.callback           = self.btn_spec.callback
        self.args               = self.btn_spec.args
        self.kwargs             = self.btn_spec.kwargs

    def build(self):
        cmds.button(
            label=self.label,
            h=self.height,
            w=self.width,
            bgc=self.backgroundcolor,
            command=lambda _: self.callback(*self.args, **self.kwargs)
        )


@dataclass
class ButtonSpec:

    label: str

    callback: Optional[Callable] = None

    height: int = 30

    width: int = 120

    backgroundcolor: list = field(default_factory=list)

    args: tuple = field(default_factory=tuple)

    kwargs: dict = field(default_factory=dict)
