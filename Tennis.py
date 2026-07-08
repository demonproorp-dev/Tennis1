import streamlit as st
import itertools
import random
import pandas as pd
import json
from collections import defaultdict
import math

# --- Конфигурация страницы ---
st.set_page_config(
    page_title="Ping-Pong Pro Tournament",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Инициализация состояния ---
def init_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "setup"          # setup, group, playoff, end
        st.session_state.players = []
        st.session_state.matches = []             # список сыгранных матчей (группа)
        st.session_state.pairs = []               # все пары для группового этапа
        st.session_state.playoff_bracket = []     # сетка плей-офф
        st.session_state.champion = None
        st.session_state.third_place = None
        st.session_state.target_score = 11
        st.session_state.tournament_name = "Ping-Pong Pro"
        st.session_state.history = []             # история для отката в плей-офф

init_state()

# --- Стили (современный тёмный UI с неоном) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0a0f1a; color: #e2e8f0; }

/* Заголовки */
h1, h2, h3, h4, .player-name { font-weight: 800; letter-spacing: -0.02em; }

/* Карточки */
.main-card {
    background: linear-gradient(145deg, #151f2e, #0b1120);
    padding: 1.8rem 1.5rem;
    border-radius: 28px;
    border: 1px solid #2a3a50;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    transition: all 0.3s ease;
}
.main-card:hover { border-color: #f97316; transform: translateY(-3px); }

/* Кнопки */
.stButton > button {
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.8rem;
    font-weight: 700;
    transition: all 0.3s ease;
    box-shadow: 0 4px 14px rgba(249,115,22,0.35);
    width: 100%;
}
.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px rgba(249,115,22,0.6);
    background: linear-gradient(135deg, #ea580c, #c2410c);
}
.stButton > button:active { transform: scale(0.97); }

/* Игроки в матче */
.player-name {
    font-size: 2.2rem;
    color: #f1f5f9;
    text-transform: uppercase;
    margin: 0.2rem 0;
}
.vs-text {
    font-size: 1.3rem;
    color: #f97316;
    font-weight: 800;
    letter-spacing: 4px;
}

/* Сетка плей-офф */
.bracket-container {
    display: flex;
    overflow-x: auto;
    padding: 1.5rem 0;
    gap: 2.5rem;
    justify-content: center;
}
.round-column {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    min-width: 180px;
    gap: 1.2rem;
    position: relative;
}
.round-column:not(:first-child)::before {
    content: '';
    position: absolute;
    left: -1.2rem;
    top: 10%;
    bottom: 10%;
    border-left: 2px dashed #2a3a50;
}
.bracket-match {
    background: #151f2e;
    border: 1px solid #2a3a50;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    transition: all 0.2s;
}
.bracket-match:hover { border-color: #f97316; }
.bracket-match.bye { opacity: 0.5; border-style: dashed; }
.bracket-match.active {
    border-color: #f97316 !important;
    box-shadow: 0 0 20px rgba(249,115,22,0.4);
}
.bracket-team {
    display: flex;
    justify-content: space-between;
    padding: 0.2rem 0;
    font-weight: 600;
}
.team-name { color: #cbd5e1; }
.team-score { color: #94a3b8; font-weight: 700; }
.winner-bg {
    background: rgba(34,197,94,0.08);
    border-left: 4px solid #22c55e;
}
.winner-text { color: #4ade80 !important; }
.loser-text { color: #64748b !important; }

/* Чемпион */
.champion-banner {
    background: radial-gradient(circle at center, #1e293b, #0b1120);
    padding: 2.5rem;
    border-radius: 30px;
    text-align: center;
    border: 2px solid #f97316;
    box-shadow: 0 0 40px rgba(249,115,22,0.25);
    animation: glow 2s infinite alternate;
}
@keyframes glow {
    0% { box-shadow: 0 0 20px rgba(249,115,22,0.2); }
    100% { box-shadow: 0 0 50px rgba(249,115,22,0.5); }
}

/* Таблица */
.dataframe {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 4px;
}
th {
    background: #151f2e !important;
    color: #f97316 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    padding: 10px 8px !important;
}
td {
    background: #0b1120 !important;
    color: #e2e8f0 !important;
    padding: 8px !important;
}

/* Счётчик очков */
.score-button {
    background: #2a3a50;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.4rem 1rem;
    font-weight: 700;
    transition: 0.2s;
    width: 60px;
}
.score-button:hover { background: #f97316; transform: scale(1.05); }
.score-display {
    font-size: 2rem;
    font-weight: 800;
    color: #f1f5f9;
    min-width: 60px;
    text-align: center;
}
.undo-btn {
    background: #2a3a50;
    color: #e2e8f0;
    border: none;
    border-radius: 8px;
    padding: 0.3rem 1rem;
    font-size: 0.8rem;
}
.undo-btn:hover { background: #4a5a70; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: #151f2e;
    border-radius: 16px;
    padding: 0.3rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: 0.5rem 1.5rem;
    font-weight: 700;
    color: #94a3b8;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #f97316;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# --- Вспомогательные функции ---
def calculate_standings():
    stats = defaultdict(lambda: {
        'wins': 0, 'losses': 0, 'points_for': 0, 'points_against': 0,
        'gd': 0, 'played': 0, 'pts': 0
    })
    for m in st.session_state.matches:
        p1, p2, o1, o2 = m['p1'], m['p2'], m['o1'], m['o2']
        winner = p1 if o1 > o2 else p2
        loser = p2 if o1 > o2 else p1
        stats[p1]['played'] += 1
        stats[p2]['played'] += 1
        stats[p1]['points_for'] += o1
        stats[p1]['points_against'] += o2
        stats[p2]['points_for'] += o2
        stats[p2]['points_against'] += o1
        stats[p1]['gd'] += o1 - o2
        stats[p2]['gd'] += o2 - o1
        if winner == p1:
            stats[p1]['wins'] += 1
            stats[p1]['pts'] += 3
            stats[p2]['losses'] += 1
            stats[p2]['pts'] += 1
        else:
            stats[p2]['wins'] += 1
            stats[p2]['pts'] += 3
            stats[p1]['losses'] += 1
            stats[p1]['pts'] += 1
    sorted_players = sorted(
        st.session_state.players,
        key=lambda p: (-stats[p]['pts'], -stats[p]['gd'], -stats[p]['points_for'])
    )
    return stats, sorted_players

def parse_score(score_str, target):
    parts = score_str.replace(":", " ").split()
    if len(parts) != 2:
        raise ValueError("Формат X:Y")
    try:
        o1, o2 = map(int, parts)
    except:
        raise ValueError("Целые числа")
    if o1 == o2:
        raise ValueError("Ничья невозможна")
    if max(o1, o2) < target:
        raise ValueError(f"Нужно минимум {target}")
    if abs(o1 - o2) < 2 and max(o1, o2) >= target:
        raise ValueError("Разница минимум 2")
    return o1, o2

def seed_players(players, size):
    slots = ["TBD"] * size
    left, right = 0, size - 1
    for i, p in enumerate(players):
        if i % 2 == 0:
            slots[left] = p
            left += 1
        else:
            slots[right] = p
            right -= 1
    return slots

def generate_playoff_bracket():
    stats, sorted_players = calculate_standings()
    n = len(sorted_players)
    size = 1
    while size < n:
        size *= 2
    if size < 4:
        size = 4
    slots = seed_players(sorted_players, size)
    round1 = []
    for i in range(0, size, 2):
        round1.append({"p1": slots[i], "p2": slots[i+1], "winner": None, "score": ""})
    rounds = [{"name": "1/8 финала" if size == 16 else ("1/4 финала" if size == 8 else "1/2 финала"),
               "matches": round1}]
    cur = size
    while cur > 1:
        cur //= 2
        if cur == 1:
            name = "Финал"
        elif cur == 2:
            name = "Полуфиналы"
        elif cur == 4:
            name = "Четвертьфиналы"
        else:
            name = f"1/{cur*2} финала"
        empty = [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""} for _ in range(cur)]
        rounds.append({"name": name, "matches": empty})
    rounds.append({"name": "Матч за 3-е место", "matches": [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""}]})
    st.session_state.playoff_bracket = rounds
    st.session_state.history = []
    process_byes(0)

def process_byes(round_idx):
    bracket = st.session_state.playoff_bracket
    if round_idx >= len(bracket):
        return
    for m in bracket[round_idx]['matches']:
        if m['winner'] is not None:
            continue
        p1, p2 = m['p1'], m['p2']
        if p1 == "TBD" and p2 != "TBD":
            m['winner'] = p2
            m['score'] = "Бай"
        elif p2 == "TBD" and p1 != "TBD":
            m['winner'] = p1
            m['score'] = "Бай"
    propagate_winners(round_idx)

def propagate_winners(round_idx):
    bracket = st.session_state.playoff_bracket
    if round_idx >= len(bracket) - 1:
        return
    next_round = bracket[round_idx + 1]
    current_round = bracket[round_idx]
    for i, m in enumerate(current_round['matches']):
        if m['winner'] is None:
            continue
        next_match_idx = i // 2
        if i % 2 == 0:
            next_round['matches'][next_match_idx]['p1'] = m['winner']
        else:
            next_round['matches'][next_match_idx]['p2'] = m['winner']
    process_byes(round_idx + 1)

def render_bracket():
    html = "<div class='bracket-container'>"
    bracket = st.session_state.playoff_bracket
    # найдём активный матч (несыгранный с двумя известными)
    active = None
    for ri, rd in enumerate(bracket):
        for mi, m in enumerate(rd['matches']):
            if m['winner'] is None and m['p1'] != "TBD" and m['p2'] != "TBD":
                active = (ri, mi)
                break
        if active:
            break
    for ri, rd in enumerate(bracket):
        html += f"<div class='round-column'><h4 style='color:#f97316; text-align:center; margin-bottom:0.8rem;'>{rd['name']}</h4>"
        for mi, m in enumerate(rd['matches']):
            p1, p2, sc, winner = m['p1'], m['p2'], m['score'], m['winner']
            is_bye = (p1 == "TBD" or p2 == "TBD") and winner is not None and sc == "Бай"
            p1_class = "winner-text" if winner == p1 else ("loser-text" if winner else "team-name")
            p2_class = "winner-text" if winner == p2 else ("loser-text" if winner else "team-name")
            match_class = "winner-bg" if winner else ""
            if is_bye:
                match_class += " bye"
            if active and ri == active[0] and mi == active[1]:
                match_class += " active"
            if sc == "Бай":
                s1, s2 = "—", "—"
            else:
                parts = sc.split(":")
                s1 = parts[0] if len(parts) > 0 else ""
                s2 = parts[1] if len(parts) > 1 else ""
            html += f"""
                <div class='bracket-match {match_class}'>
                    <div class='bracket-team'><span class='{p1_class}'>{p1 if p1!="TBD" else "—"}</span> <span class='team-score'>{s1}</span></div>
                    <div class='bracket-team'><span class='{p2_class}'>{p2 if p2!="TBD" else "—"}</span> <span class='team-score'>{s2}</span></div>
                </div>
            """
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# --- Боковая панель ---
with st.sidebar:
    st.markdown("### ⚙️ Управление")
    if st.session_state.stage != "setup":
        if st.button("🔄 Сбросить турнир", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_state()
            st.rerun()
    st.markdown("---")
    st.markdown("### 💾 Сохранение")
    if st.session_state.stage != "setup":
        save_data = {k: v for k, v in st.session_state.items()}
        st.download_button(
            "⬇️ Скачать прогресс (.json)",
            data=json.dumps(save_data, ensure_ascii=False, default=str),
            file_name="tournament_save.json",
            use_container_width=True
        )
    uploaded = st.file_uploader("⬆️ Загрузить прогресс", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            for k, v in data.items():
                st.session_state[k] = v
            st.success("Загружено!")
            st.rerun()
        except:
            st.error("Ошибка")
    st.markdown("---")
    st.markdown(f"**Версия 4.0** • {st.session_state.tournament_name}")

# --- Основной интерфейс ---
st.markdown("<h1 style='text-align:center; color:#f97316;'>🏓 PING-PONG PRO</h1>", unsafe_allow_html=True)

# --- ЭТАП 1: НАСТРОЙКА ---
if st.session_state.stage == "setup":
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Настройка турнира</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            num = st.number_input("Игроков", 2, 16, min(4, 4), 1)
            target = st.selectbox("Очков для победы", [11, 15, 21], index=0)
        with col2:
            st.write("Введите имена:")
            names = [st.text_input(f"Игрок {i+1}", key=f"setup_{i}") for i in range(int(num))]
        if st.button("🚀 СТАРТ", use_container_width=True):
            if any(n.strip() == "" for n in names):
                st.error("Заполните все имена!")
            else:
                st.session_state.players = [n.strip() for n in names]
                st.session_state.target_score = target
                st.session_state.pairs = list(itertools.combinations(st.session_state.players, 2))
                random.shuffle(st.session_state.pairs)
                st.session_state.matches = []
                st.session_state.stage = "group"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- ЭТАП 2: ГРУППОВОЙ ЭТАП ---
elif st.session_state.stage == "group":
    tab1, tab2, tab3 = st.tabs(["🏓 Матчи", "📊 Таблица", "📈 Статистика"])
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Текущий матч</h3>", unsafe_allow_html=True)
            played = {m['pair_idx'] for m in st.session_state.matches}
            idx, match = next(((i, p) for i, p in enumerate(st.session_state.pairs) if i not in played), (None, None))
            if match:
                p1, p2 = match
                st.markdown(f"<div class='player-name'>{p1}</div><div class='vs-text'>VS</div><div class='player-name'>{p2}</div>", unsafe_allow_html=True)
                # Интерактивный ввод счёта через кнопки
                if "score1" not in st.session_state:
                    st.session_state.score1 = 0
                    st.session_state.score2 = 0
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if st.button("−", key="dec1"):
                        if st.session_state.score1 > 0:
                            st.session_state.score1 -= 1
                with c2:
                    st.markdown(f"<div class='score-display'>{st.session_state.score1}</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("+", key="inc1"):
                        st.session_state.score1 += 1
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if st.button("−", key="dec2"):
                        if st.session_state.score2 > 0:
                            st.session_state.score2 -= 1
                with c2:
                    st.markdown(f"<div class='score-display'>{st.session_state.score2}</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("+", key="inc2"):
                        st.session_state.score2 += 1

                if st.button("✅ Сохранить результат", use_container_width=True):
                    try:
                        o1, o2 = st.session_state.score1, st.session_state.score2
                        if o1 == o2:
                            raise ValueError("Ничья невозможна")
                        if max(o1, o2) < st.session_state.target_score:
                            raise ValueError(f"Нужно минимум {st.session_state.target_score}")
                        if abs(o1 - o2) < 2 and max(o1, o2) >= st.session_state.target_score:
                            raise ValueError("Разница 2 очка")
                        st.session_state.matches.append({"p1": p1, "p2": p2, "o1": o1, "o2": o2, "pair_idx": idx})
                        st.session_state.score1 = 0
                        st.session_state.score2 = 0
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            else:
                st.success("Групповой этап завершён!")
                if st.button("🏆 Сгенерировать Плей-офф", use_container_width=True):
                    generate_playoff_bracket()
                    st.session_state.stage = "playoff"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown("<h3>История матчей</h3>", unsafe_allow_html=True)
            if st.session_state.matches:
                for i, m in enumerate(st.session_state.matches[::-1]):
                    st.write(f"{m['p1']} {m['o1']}:{m['o2']} {m['p2']}")
                if st.button("↩ Отменить последний", use_container_width=True):
                    st.session_state.matches.pop()
                    st.rerun()
            else:
                st.info("Матчей пока нет")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<h3>Таблица лидеров</h3>", unsafe_allow_html=True)
        stats, sorted_p = calculate_standings()
        data = []
        for i, p in enumerate(sorted_p, 1):
            data.append({
                "Место": i,
                "Игрок": p,
                "И": stats[p]['played'],
                "В": stats[p]['wins'],
                "П": stats[p]['losses'],
                "Очки": f"{stats[p]['points_for']}:{stats[p]['points_against']}",
                "Разница": stats[p]['gd'],
                "О": stats[p]['pts']
            })
        df = pd.DataFrame(data)
        def highlight(row):
            if row.name < 4:
                return ['background-color: rgba(34,197,94,0.15); color: #4ade80;'] * len(row)
            return ['background-color: #0b1120; color: #e2e8f0;'] * len(row)
        st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("<h3>Дополнительная статистика</h3>", unsafe_allow_html=True)
        if st.session_state.matches:
            stats, _ = calculate_standings()
            for p in st.session_state.players:
                s = stats[p]
                if s['played'] > 0:
                    avg_for = s['points_for'] / s['played']
                    avg_against = s['points_against'] / s['played']
                    win_pct = s['wins'] / s['played'] * 100
                    st.metric(label=p, value=f"{win_pct:.1f}% побед", delta=f"Ср. счёт {avg_for:.1f}:{avg_against:.1f}")
        else:
            st.info("Нет данных")

# --- ЭТАП 3: ПЛЕЙ-ОФФ ---
elif st.session_state.stage == "playoff":
    st.markdown("<h2 style='text-align:center;'>🏆 Турнирная сетка</h2>", unsafe_allow_html=True)
    render_bracket()

    # Поиск активного матча
    bracket = st.session_state.playoff_bracket
    active = None
    for ri, rd in enumerate(bracket):
        for mi, m in enumerate(rd['matches']):
            if m['winner'] is None and m['p1'] != "TBD" and m['p2'] != "TBD":
                active = (ri, mi, m)
                break
        if active:
            break

    if active:
        st.markdown("---")
        ri, mi, m = active
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{bracket[ri]['name']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='player-name'>{m['p1']}</div><div class='vs-text'>VS</div><div class='player-name'>{m['p2']}</div>", unsafe_allow_html=True)
            # Интерактивный ввод
            if "po_score1" not in st.session_state:
                st.session_state.po_score1 = 0
                st.session_state.po_score2 = 0
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("−", key="po_dec1"):
                    if st.session_state.po_score1 > 0:
                        st.session_state.po_score1 -= 1
            with c2:
                st.markdown(f"<div class='score-display'>{st.session_state.po_score1}</div>", unsafe_allow_html=True)
            with c3:
                if st.button("+", key="po_inc1"):
                    st.session_state.po_score1 += 1
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("−", key="po_dec2"):
                    if st.session_state.po_score2 > 0:
                        st.session_state.po_score2 -= 1
            with c2:
                st.markdown(f"<div class='score-display'>{st.session_state.po_score2}</div>", unsafe_allow_html=True)
            with c3:
                if st.button("+", key="po_inc2"):
                    st.session_state.po_score2 += 1

            if st.button("✅ Записать", use_container_width=True):
                try:
                    o1, o2 = st.session_state.po_score1, st.session_state.po_score2
                    if o1 == o2:
                        raise ValueError("Ничья")
                    if max(o1, o2) < st.session_state.target_score:
                        raise ValueError(f"Нужно минимум {st.session_state.target_score}")
                    if abs(o1 - o2) < 2 and max(o1, o2) >= st.session_state.target_score:
                        raise ValueError("Разница 2")
                    winner = m['p1'] if o1 > o2 else m['p2']
                    loser = m['p2'] if o1 > o2 else m['p1']
                    # Сохраняем в историю для отката
                    st.session_state.history.append((ri, mi, m['p1'], m['p2']))
                    bracket[ri]['matches'][mi]['winner'] = winner
                    bracket[ri]['matches'][mi]['score'] = f"{o1}:{o2}"
                    propagate_winners(ri)
                    st.session_state.po_score1 = 0
                    st.session_state.po_score2 = 0
                    # Проверяем завершение
                    if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
                        st.session_state.champion = bracket[-2]['matches'][0]['winner']
                        st.session_state.third_place = bracket[-1]['matches'][0]['winner']
                        st.session_state.stage = "end"
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            if st.session_state.history:
                if st.button("↩ Отменить последний матч плей-офф", use_container_width=True):
                    last = st.session_state.history.pop()
                    ri, mi, p1, p2 = last
                    bracket[ri]['matches'][mi]['winner'] = None
                    bracket[ri]['matches'][mi]['score'] = ""
                    # Пересчитываем все последующие раунды (сбрасываем)
                    for r in range(ri+1, len(bracket)):
                        for mm in bracket[r]['matches']:
                            mm['p1'] = "TBD"
                            mm['p2'] = "TBD"
                            mm['winner'] = None
                            mm['score'] = ""
                    propagate_winners(ri)
                    st.rerun()
    else:
        if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
            st.session_state.champion = bracket[-2]['matches'][0]['winner']
            st.session_state.third_place = bracket[-1]['matches'][0]['winner']
            st.session_state.stage = "end"
            st.rerun()
        else:
            st.info("Все матчи завершены, ожидайте...")

# --- ЭТАП 4: ФИНИШ ---
elif st.session_state.stage == "end":
    third = st.session_state.playoff_bracket[-1]['matches'][0]['winner']
    st.markdown(f"""
    <div class='champion-banner'>
        <h2 style='color:#f97316; letter-spacing:3px;'>ЧЕМПИОН ТУРНИРА</h2>
        <h1 style='font-size:3.5rem; color:#fbbf24; text-shadow: 0 0 30px rgba(251,191,36,0.4);'>{st.session_state.champion}</h1>
        <h3 style='color:#94a3b8; margin-top:1rem;'>🥉 3-е место: {third}</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; margin-top:2rem;'>Итоговая сетка</h3>", unsafe_allow_html=True)
    render_bracket()
