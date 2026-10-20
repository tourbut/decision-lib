"""Offline tests: the picker's hold rule, the loop's stops, and each environment."""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

import desktop_env
import grid_env
import web_env
from agent import DONE, NONE, pick, run


def choose(prefer):
    """Stub that puts 0.9 on the action `prefer(candidates, screen)` returns."""
    def answer(request) -> ClassifierResponse:
        labels = request["questions"]["action"].criteria
        want = prefer(labels, request["state"]["screen"])
        probs = {k: (0.9 if k == want else 0.1 / (len(labels) - 1)) for k in labels}
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            "action": {"type": "choice", "choice": want, "probabilities": probs, "confidence": 0.9}}})
    return RunnableLambda(answer)


def test_unsure_pick_holds() -> None:
    def flat(request) -> ClassifierResponse:
        labels = list(request["questions"]["action"].criteria)
        probs = {k: 1 / len(labels) for k in labels}
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            "action": {"type": "choice", "choice": labels[0], "probabilities": probs, "confidence": 0.1}}})
    assert pick(RunnableLambda(flat), "g", "o", {"a": "x", "b": "y"})[0] == NONE


def test_web_never_offers_external_links_and_reaches_a_page() -> None:
    env = web_env.WebEnv()
    _, candidates = env.observe(web_env.START)
    assert all("외부" not in label for label in candidates.values())

    route = ["IT 지원", "네트워크·VPN", "VPN 접속 오류 해결"]

    def prefer(labels, screen):
        if screen.startswith("제목: VPN 접속 오류 해결"):
            return DONE
        return next(k for k, v in labels.items() if any(v.startswith(r) for r in route))

    r = run(choose(prefer), env, "VPN 오류", web_env.START, lambda u: web_env.title_of(u) == "VPN 접속 오류 해결")
    assert r["verified"] and [t["label"].split(" (")[0] for t in r["trace"][:3]] == route


def test_done_is_checked_independently() -> None:
    r = run(choose(lambda labels, screen: DONE), web_env.WebEnv(), "급여명세서", web_env.START, lambda u: False)
    assert r["stopped"] == DONE and not r["verified"]


def test_desktop_reports_applied_state_and_logs_clicks() -> None:
    env = desktop_env.DesktopEnv()
    s = env.step(env.step(desktop_env.START, "btn_display"), "tgl_dark")
    _, tree = env.observe(s)
    assert tree["tgl_dark"].endswith("(이미 적용됨)") and s.get("dark_mode") is True
    assert env.log == ["설정: button '디스플레이' 누름", "설정 > 디스플레이: toggle '다크 모드' 누름"]


def test_loop_stops_when_an_action_changes_nothing() -> None:
    env = desktop_env.DesktopEnv()
    s = env.step(env.step(desktop_env.START, "btn_display"), "tgl_dark")
    r = run(choose(lambda labels, screen: "tgl_dark"), env, "다크 모드", s, lambda st: True)
    assert r["stopped"] == NONE and r["trace"][-1]["label"] == "반복 감지로 중단"


def test_grid_offers_only_legal_moves() -> None:
    env = grid_env.GridEnv("offset")
    _, candidates = env.observe(grid_env.start("corridor"))
    assert set(candidates) == {"east"}  # walls on three sides


def test_grid_macro_with_stage_guard_walks_the_shortest_route() -> None:
    order = ["pick_key", "open_door", "goto_K", "goto_D", "goto_E"]

    def prefer(labels, screen):  # decoys (goto_T, goto_C) are never in `order`
        return next((a for a in order if a in labels), DONE)

    for name in grid_env.MAPS:
        env = grid_env.GridEnv("macro")
        r = run(choose(prefer), env, "탈출", grid_env.start(name), grid_env.at_exit, max_steps=10)
        assert r["verified"], name
        assert env.moves + 2 == grid_env.optimal_steps(name)  # + pick + open
        assert [x.split("(")[0] for x in env.replans] == ["단계 변경", "단계 변경"]
