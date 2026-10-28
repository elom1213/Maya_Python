# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# Framework - Pin(Always on Top) 토글 버튼의 "켜짐" 표시 색.
#
# 여러 툴(A00240_PathTool · A00220_BackupTool · A00370_ToolLauncher …)이 같은 모양의 체크형
# `Pin` 버튼을 갖는다. 켜지면 라벨이 `Pinned` 로 바뀌는데, 테마 qss 에는 QPushButton:checked 규칙이
# 없어 색은 그대로라 켜진 줄 알기 어려웠다. 여기 한 곳의 qss 를 버튼에 붙이면 **켜진 동안 연한
# 빨강**이 된다(hover / pressed 도 같은 계열). 툴마다 색을 따로 적지 않도록 공용으로 둔다.
#
# 쓰는 법
# ------
#     from Framework.qt.pin_style import apply_pin_style
#     self.pin_button = QPushButton("Pin")
#     self.pin_button.setCheckable(True)
#     apply_pin_style(self.pin_button)
#
# 버튼 자신의 qss 는 테마(앱/창 qss)의 QPushButton 규칙 **위에** 겹쳐진다. 여기서는 `:checked`
# 상태의 색만 적고 padding · border-radius 는 적지 않으므로 평소 모양 · 크기는 테마 그대로다
# (위젯 qss 가 padding 을 덮어쓰면 버튼 높이가 달라진다 - A00240 색 버튼에서 겪은 일).

# 켜진 동안의 색 - 연한 빨강 바탕 + 어두운 글자 (밝은 바탕이라 흰 글자는 안 보인다)
PINNED_BG = "#f2a0a0"
PINNED_BG_HOVER = "#f6b4b4"
PINNED_BG_PRESSED = "#e68c8c"
PINNED_BORDER = "#dd8888"
PINNED_TEXT = "#4a1414"

PIN_BUTTON_QSS = """
QPushButton:checked {{
    background-color: {bg};
    color: {text};
    border: 1px solid {border};
}}
QPushButton:checked:hover {{
    background-color: {hover};
}}
QPushButton:checked:pressed {{
    background-color: {pressed};
}}
""".format(bg=PINNED_BG, text=PINNED_TEXT, border=PINNED_BORDER,
           hover=PINNED_BG_HOVER, pressed=PINNED_BG_PRESSED)


def apply_pin_style(button, extra_qss=""):
    """체크형 Pin 버튼에 "켜짐 = 연한 빨강" qss 를 붙인다. 버튼을 그대로 돌려준다.

    extra_qss : 이 버튼에만 따로 필요한 규칙(예: A00480 의 `padding: 0px 4px`). setStyleSheet 는
    덮어쓰기라 따로 부르면 한쪽이 사라지므로 여기서 함께 붙인다(2026-10-29).
    """
    button.setStyleSheet((extra_qss + "\n" if extra_qss else "") + PIN_BUTTON_QSS)
    return button
