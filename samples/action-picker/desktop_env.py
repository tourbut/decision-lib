"""A mock settings app as an accessibility tree: screens of buttons and toggles, about 20
elements in all. Nothing touches the real OS; every action is applied to a dict and
logged, like a dry run.
"""

from __future__ import annotations

from typing import NamedTuple

# screen -> [(element id, role, label, effect)]; effect is ("go", screen) or ("set", key, value)
SCREENS = {
    "main": [
        ("btn_display", "button", "디스플레이", ("go", "display")),
        ("btn_sound", "button", "소리", ("go", "sound")),
        ("btn_network", "button", "네트워크", ("go", "network")),
        ("btn_privacy", "button", "개인정보 보호", ("go", "privacy")),
    ],
    "display": [
        ("tgl_dark", "toggle", "다크 모드", ("set", "dark_mode", True)),
        ("sld_bright_70", "slider", "밝기 70%로", ("set", "brightness", 70)),
        ("tgl_night", "toggle", "야간 조명", ("set", "night_light", True)),
        ("btn_back", "button", "뒤로", ("go", "main")),
    ],
    "sound": [
        ("tgl_mute", "toggle", "음소거", ("set", "muted", True)),
        ("sld_vol_30", "slider", "음량 30%로", ("set", "volume", 30)),
        ("btn_back", "button", "뒤로", ("go", "main")),
    ],
    "network": [
        ("tgl_wifi", "toggle", "와이파이 켜기", ("set", "wifi", True)),
        ("tgl_airplane", "toggle", "비행기 모드", ("set", "airplane", True)),
        ("btn_vpn", "button", "VPN 설정", ("go", "vpn")),
        ("btn_back", "button", "뒤로", ("go", "main")),
    ],
    "vpn": [
        ("btn_vpn_connect", "button", "회사 VPN 연결", ("set", "vpn", "connected")),
        ("btn_back", "button", "뒤로", ("go", "network")),
    ],
    "privacy": [
        ("tgl_camera", "toggle", "카메라 접근 허용", ("set", "camera", True)),
        ("tgl_location", "toggle", "위치 서비스", ("set", "location", True)),
        ("btn_back", "button", "뒤로", ("go", "main")),
    ],
}

TITLES = {"main": "설정", "display": "설정 > 디스플레이", "sound": "설정 > 소리", "network": "설정 > 네트워크",
          "vpn": "설정 > 네트워크 > VPN", "privacy": "설정 > 개인정보 보호"}


class State(NamedTuple):
    screen: str
    settings: tuple[tuple[str, object], ...]  # sorted pairs, so the state is hashable and comparable

    def get(self, key: str):
        return dict(self.settings).get(key)


START = State("main", ())


class DesktopEnv:
    def __init__(self) -> None:
        self.log: list[str] = []  # the dry-run record of what would have been clicked

    def observe(self, state: State) -> tuple[str, dict[str, str]]:
        current = ", ".join(f"{k}={v}" for k, v in state.settings) or "기본값"
        # Like a real accessibility tree, each control reports its current state.
        tree = {el: f"[{role}] {label}" + (" (이미 적용됨)" if effect[0] == "set" and state.get(effect[1]) == effect[2] else "")
                for el, role, label, effect in SCREENS[state.screen]}
        return f"창: {TITLES[state.screen]}\n바뀐 설정: {current}", tree

    def step(self, state: State, action: str) -> State:
        _, role, label, effect = next(e for e in SCREENS[state.screen] if e[0] == action)
        self.log.append(f"{TITLES[state.screen]}: {role} '{label}' 누름")
        if effect[0] == "go":
            return State(effect[1], state.settings)
        settings = dict(state.settings)
        settings[effect[1]] = effect[2]
        return State(state.screen, tuple(sorted(settings.items())))


GOALS = [
    {"goal": "화면을 다크 모드로 바꿔 줘.", "expect": ("dark_mode", True)},
    {"goal": "회의 들어가야 하니까 소리 꺼 줘.", "expect": ("muted", True)},
    {"goal": "재택이라 회사 VPN에 붙어야 해.", "expect": ("vpn", "connected")},
    {"goal": "화상회의 앱이 카메라를 못 써. 허용해 줘.", "expect": ("camera", True)},
    {"goal": "밤이라 눈이 부셔. 야간 조명 켜 줘.", "expect": ("night_light", True)},
    {"goal": "프린터 용지 걸린 거 해결해 줘.", "expect": None},  # no such control: should stop with NONE
]
