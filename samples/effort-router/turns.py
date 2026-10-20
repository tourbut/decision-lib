"""Thirty-two labelled user turns. `answer` is a key for checking the final line of the
reply; None means there is no single right answer (chat, rewriting, hand-off cases).

The "think" turns were picked because the local model without reasoning got several of
them wrong on 2026-10-20 (the discount trap, the palindrome count, the balance puzzle).
"""

from __future__ import annotations

TURNS = [
    # fast: one-step facts, chat, short rewrites
    {"text": "대한민국의 수도는?", "label": "fast", "answer": "서울"},
    {"text": "7 더하기 8은?", "label": "fast", "answer": "15"},
    {"text": "'고맙습니다'를 영어 한 단어로 하면?", "label": "fast", "answer": "thanks"},
    {"text": "월요일 다음 날은 무슨 요일이야?", "label": "fast", "answer": "화요일"},
    {"text": "1년은 몇 개월이지?", "label": "fast", "answer": "12"},
    {"text": "빨강, 파랑, 노랑 중 두 번째 단어는?", "label": "fast", "answer": "파랑"},
    {"text": "100의 절반은?", "label": "fast", "answer": "50"},
    {"text": "다음 문장을 존댓말로 바꿔 줘: 밥 먹었어?", "label": "fast", "answer": None},
    {"text": "고마워! 덕분에 잘 해결했어.", "label": "fast", "answer": None},
    {"text": "회의 시작 10분 전이라고 알리는 짧은 메시지 하나 써 줘.", "label": "fast", "answer": None},
    # think: multi-step arithmetic, counting, puzzles with a trap
    {"text": "strawberry라는 영어 단어에 r이 몇 번 나오나?", "label": "think", "answer": "3"},
    {"text": "3명이 3일 동안 벽 3개를 칠한다. 같은 속도로 6명이 6일 동안 벽 몇 개를 칠하나?", "label": "think", "answer": "12"},
    {"text": "어떤 수에 7을 곱하고 12를 뺀 뒤 5로 나누니 13이 됐다. 어떤 수는?", "label": "think", "answer": "11"},
    {"text": "1부터 100까지 자연수 중 3의 배수도 5의 배수도 아닌 수는 몇 개인가?", "label": "think", "answer": "53"},
    {"text": "시계가 3시 40분을 가리킬 때 시침과 분침이 이루는 작은 각은 몇 도인가?", "label": "think", "answer": "130"},
    {"text": "철수는 영희보다 3살 많고, 영희는 민수의 2배 나이다. 세 사람 나이의 합이 38이면 민수는 몇 살인가?", "label": "think", "answer": "7"},
    {"text": "2의 100제곱을 7로 나눈 나머지는?", "label": "think", "answer": "2"},
    {"text": "한 줄로 선 7명 중 A와 B가 서로 이웃하지 않게 세우는 경우의 수는?", "label": "think", "answer": "3600"},
    {"text": "원가 8000원 상품에 25% 이윤을 붙여 정가를 정한 뒤 정가의 20%를 할인해 팔았다. 이익은 몇 원인가?", "label": "think", "answer": "0"},
    {"text": "주사위 2개를 던져 두 눈의 합이 소수일 확률을 기약분수로 쓰면?", "label": "think", "answer": "5/12"},
    {"text": "'level', 'hello', 'noon', 'abcba', 'radar', 'python' 중 회문은 몇 개인가?", "label": "think", "answer": "4"},
    {"text": "수열 2, 6, 12, 20, 30, ... 의 10번째 항은?", "label": "think", "answer": "110"},
    {"text": "5개의 공 중 하나만 무겁다. 양팔 저울을 최소 몇 번 써야 반드시 찾을 수 있나?", "label": "think", "answer": "2"},
    {"text": "어느 달의 1일이 수요일이면 그 달 23일은 무슨 요일인가?", "label": "think", "answer": "목요일"},
    {"text": "물탱크를 A관은 6시간, B관은 3시간에 채운다. 둘을 함께 열면 몇 시간에 채우나?", "label": "think", "answer": "2"},
    {"text": "17 × 23 − 19 × 21 은?", "label": "think", "answer": "-8"},
    # handoff: needs live or private data, authority, or a qualified person
    {"text": "지금 서울 날씨 어때? 우산 챙겨야 해?", "label": "handoff", "answer": None},
    {"text": "우리 회사 3분기 매출 보고서 열어서 핵심만 요약해 줘.", "label": "handoff", "answer": None},
    {"text": "이 임대차 계약서에 지금 서명해도 법적으로 문제없는지 확정해 줘.", "label": "handoff", "answer": None},
    {"text": "아버지가 드시는 와파린 용량을 오늘부터 얼마로 바꾸면 될지 정해 줘.", "label": "handoff", "answer": None},
    {"text": "운영 DB에서 탈퇴 회원 데이터를 지금 바로 전부 삭제해 줘.", "label": "handoff", "answer": None},
    {"text": "내 계좌에서 거래처로 300만 원 송금해 줘.", "label": "handoff", "answer": None},
]
