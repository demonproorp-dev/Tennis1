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
        st.session_state.matches = []             # сыгранные матчи группового этапа
        st.session_state.pairs = []               # все пары для группового этапа
        st.session_state.playoff_bracket = []     # сетка плей-офф
        st.session_state.champion = None
        st.session_state.third_place = None
        st.session_state.target_score = 11
        st.session_state.tournament_name = "Ping-Pong Pro"

init_state()

# --- Стили (Premium Dark UI с анимациями) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: #0b1120;
    color: #e2e8f0;
}

/* Заголовки */
h1, h2, h3, h4, .player-name {
    font-weight: 800;
    letter-spacing: -0.02em;
}

/* Карточки */
.main-card {
    background: linear-gradient(145deg, #1a2332, #0f172a);
    padding: 2rem 1.5rem;
    border-radius: 24px;
    border: 1px solid #2d3a4f;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    transition: transform 0.2s, border-color 0.2s;
}
.main-card:hover {
    border-color: #f97316;
    transform: translateY(-2px);
}

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
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(249,115,22,0.5);
    background: linear-gradient(135deg, #ea580c, #c2410c);
}

/* Игроки */
.player-name {
    font-size: 2rem;
    color: #f1f5f9;
    text-transform: uppercase;
    margin: 0.2rem 0;
}
.vs-text {
    font-size: 1.2rem;
    color: #f97316;
    font-weight: 800;
    letter-spacing: 3px;
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
    min-width: 200px;
    gap: 1.2rem;
    position: relative;
}
.round-column:not(:first-child)::before {
    content: '';
    position: absolute;
    left: -1.2rem;
    top: 10%;
    bottom: 10%;
    border-left: 2px dashed #334155;
}
.bracket-match {
    background: #1a2332;
    border: 1px solid #2d3a4f;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    transition: all 0.2s;
}
.bracket-match:hover {
    border-color: #f97316;
}
.bracket-match.bye-match {
    opacity: 0.6;
    border-style: dashed;
}
.bracket-match.highlight {
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

/* Баннер чемпиона */
.champion-banner {
    background: radial-gradient(circle at center, #1e293b, #0b1120);
    padding: 2.5rem;
    border-radius: 30px;
    text-align: center;
    border: 2px solid #f97316;
    box-shadow: 0 0 40px rgba(249,115,22,0.25);
    animation: pulse-glow 2s infinite alternate;
}
@keyframes pulse-glow {
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
    background: #1a2332 !important;
    color: #f97316 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.8rem !important;
    padding: 10px 8px !important;
}
td {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    padding: 8px !important;
}

/* Прочие элементы */
.small-text {
    font-size: 0.8rem;
    color: #94a3b8;
}
hr {
    border-color: #2d3a4f;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# --- Вспомогательные функции ---
def calculate_standings():
    """Возвращает статистику и отсортированный список игроков по очкам (3 за победу, 1 за поражение)."""
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
            stats[p2]['pts'] += 1   # за поражение даём 1 очко (можно настроить)
        else:
            stats[p2]['wins'] += 1
            stats[p2]['pts'] += 3
            stats[p1]['losses'] += 1
            stats[p1]['pts'] += 1

    # Сортировка: по очкам, потом по разнице, потом по забитым
    sorted_players = sorted(
        st.session_state.players,
        key=lambda p: (-stats[p]['pts'], -stats[p]['gd'], -stats[p]['points_for'])
    )
    return stats, sorted_players

def parse_score(score_str, target):
    """Парсит строку счёта, проверяет валидность."""
    parts = score_str.replace(":", " ").split()
    if len(parts) != 2:
        raise ValueError("Формат: X:Y (например, 11:8)")
    try:
        o1, o2 = map(int, parts)
    except ValueError:
        raise ValueError("Используйте целые числа")
    if o1 == o2:
        raise ValueError("Ничья невозможна!")
    if max(o1, o2) < target:
        raise ValueError(f"Нужно минимум {target} очков!")
    if abs(o1 - o2) < 2 and max(o1, o2) >= target:
        raise ValueError("Разница должна быть 2 очка!")
    return o1, o2

def seed_players(players, size):
    """Размещает игроков по слотам сетки согласно стандартному сеянию."""
    slots = ["TBD"] * size
    n = len(players)
    # Заполняем с краёв поочерёдно
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
    """Строит сетку плей-офф и обрабатывает баи."""
    stats, sorted_players = calculate_standings()
    n = len(sorted_players)
    # Определяем размер сетки (ближайшая степень двойки, но не менее 4)
    size = 1
    while size < n:
        size *= 2
    if size < 4:
        size = 4

    slots = seed_players(sorted_players, size)

    # Первый раунд
    round1_matches = []
    for i in range(0, size, 2):
        round1_matches.append({
            "p1": slots[i],
            "p2": slots[i+1],
            "winner": None,
            "score": ""
        })
    rounds = [{"name": "1/8 финала" if size == 16 else ("1/4 финала" if size == 8 else "1/2 финала"),
               "matches": round1_matches}]

    # Последующие раунды
    cur_size = size
    while cur_size > 1:
        cur_size //= 2
        if cur_size == 1:
            name = "Финал"
        elif cur_size == 2:
            name = "Полуфиналы"
        elif cur_size == 4:
            name = "Четвертьфиналы"
        else:
            name = f"1/{cur_size*2} финала"
        empty = [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""} for _ in range(cur_size)]
        rounds.append({"name": name, "matches": empty})

    # Матч за 3-е место
    rounds.append({"name": "Матч за 3-е место", "matches": [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""}]})

    st.session_state.playoff_bracket = rounds
    # Автоматическая обработка баев в первом раунде
    process_byes(0)

def process_byes(round_idx):
    """Проверяет матчи раунда, если один из участников TBD – победителем становится другой."""
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
    # Прокидываем победителей в следующий раунд
    propagate_winners(round_idx)

def propagate_winners(round_idx):
    """Передаёт победителей из текущего раунда в следующий."""
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
    # Проверяем следующий раунд на баи (рекурсивно)
    process_byes(round_idx + 1)

def render_bracket_html():
    """Генерирует HTML‑код для отображения сетки."""
    html = "<div class='bracket-container'>"
    bracket = st.session_state.playoff_bracket
    for r_idx, round_data in enumerate(bracket):
        html += f"<div class='round-column'><h4 style='color:#f97316; text-align:center; margin-bottom:0.8rem;'>{round_data['name']}</h4>"
        for m in round_data['matches']:
            p1, p2, sc, winner = m['p1'], m['p2'], m['score'], m['winner']
            is_bye = (p1 == "TBD" or p2 == "TBD") and winner is not None and sc == "Бай"
            p1_class = "winner-text" if winner == p1 else ("loser-text" if winner else "team-name")
            p2_class = "winner-text" if winner == p2 else ("loser-text" if winner else "team-name")
            match_class = "winner-bg" if winner else ""
            if is_bye:
                match_class += " bye-match"
            # Подсветка текущего матча (если ещё не сыгран и оба участника известны)
            if not winner and p1 != "TBD" and p2 != "TBD":
                # отметим, что этот матч активен (можно использовать глобальный флаг)
                match_class += " highlight"

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
            st.success("Прогресс загружен!")
            st.rerun()
        except Exception:
            st.error("Ошибка файла")
    st.markdown("---")
    st.markdown("### ℹ️ Инфо")
    st.caption(f"Версия 3.0 • {st.session_state.tournament_name}")

# --- Основной интерфейс ---
st.markdown("<h1 style='text-align:center; color:#f97316;'>🏓 PING-PONG PRO</h1>", unsafe_allow_html=True)

# --- ЭТАП 1: НАСТРОЙКА ---
if st.session_state.stage == "setup":
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Настройка турнира</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            num_players = st.number_input("Количество игроков", 2, 16, min(4, 4), 1)
            target_score = st.selectbox("Очков для победы", [11, 15, 21], index=0)
        with col2:
            st.write("Введите имена участников:")
            names = []
            for i in range(int(num_players)):
                names.append(st.text_input(f"Игрок {i+1}", key=f"setup_p_{i}"))

        if st.button("🚀 СТАРТ ТУРНИР", use_container_width=True):
            if any(n.strip() == "" for n in names):
                st.error("Заполните все имена!")
            else:
                st.session_state.players = [n.strip() for n in names]
                st.session_state.target_score = target_score
                st.session_state.pairs = list(itertools.combinations(st.session_state.players, 2))
                random.shuffle(st.session_state.pairs)
                st.session_state.matches = []   # очищаем на всякий случай
                st.session_state.stage = "group"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- ЭТАП 2: ГРУППОВОЙ ЭТАП ---
elif st.session_state.stage == "group":
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Текущий матч</h3>", unsafe_allow_html=True)

        played_idxs = {m['pair_idx'] for m in st.session_state.matches}
        idx, current_match = next(
            ((i, p) for i, p in enumerate(st.session_state.pairs) if i not in played_idxs),
            (None, None)
        )

        if current_match:
            p1, p2 = current_match
            st.markdown(f"<div class='player-name'>{p1}</div><div class='vs-text'>VS</div><div class='player-name'>{p2}</div>", unsafe_allow_html=True)
            with st.form("score_form"):
                score = st.text_input("Счёт (например, 11:8)", placeholder=f"{st.session_state.target_score}:{st.session_state.target_score-2}")
                if st.form_submit_button("Сохранить результат", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score, st.session_state.target_score)
                        st.session_state.matches.append({
                            "p1": p1, "p2": p2,
                            "o1": o1, "o2": o2,
                            "pair_idx": idx
                        })
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            if st.session_state.matches:
                if st.button("↩ Отменить последний", use_container_width=True):
                    st.session_state.matches.pop()
                    st.rerun()
        else:
            st.success("Групповой этап завершён!")
            if st.button("🏆 Сгенерировать Плей-офф", use_container_width=True):
                generate_playoff_bracket()
                st.session_state.stage = "playoff"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
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
        # Стилизация
        def highlight_top(row):
            if row.name < 4:
                return ['background-color: rgba(34,197,94,0.15); color: #4ade80;'] * len(row)
            return ['background-color: #0f172a; color: #e2e8f0;'] * len(row)
        st.dataframe(df.style.apply(highlight_top, axis=1), use_container_width=True, hide_index=True)

# --- ЭТАП 3: ПЛЕЙ-ОФФ ---
elif st.session_state.stage == "playoff":
    st.markdown("<h2 style='text-align:center;'>🏆 Турнирная сетка</h2>", unsafe_allow_html=True)
    render_bracket_html()

    # Поиск текущего матча (несыгранного, с двумя известными игроками)
    bracket = st.session_state.playoff_bracket
    current_match = None
    r_idx = None
    m_idx = None
    for i, round_data in enumerate(bracket):
        for j, m in enumerate(round_data['matches']):
            if m['winner'] is None and m['p1'] != "TBD" and m['p2'] != "TBD":
                current_match = m
                r_idx = i
                m_idx = j
                break
        if current_match:
            break

    if current_match:
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{bracket[r_idx]['name']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='player-name'>{current_match['p1']}</div><div class='vs-text'>VS</div><div class='player-name'>{current_match['p2']}</div>", unsafe_allow_html=True)
            with st.form("po_score"):
                score = st.text_input("Счёт", placeholder=f"{st.session_state.target_score}:{st.session_state.target_score-2}")
                if st.form_submit_button("Записать результат", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score, st.session_state.target_score)
                        winner = current_match['p1'] if o1 > o2 else current_match['p2']
                        loser = current_match['p2'] if o1 > o2 else current_match['p1']

                        # Сохраняем результат
                        bracket[r_idx]['matches'][m_idx]['winner'] = winner
                        bracket[r_idx]['matches'][m_idx]['score'] = f"{o1}:{o2}"

                        # Прокидываем победителя дальше
                        propagate_winners(r_idx)

                        # Проверяем, не завершён ли турнир
                        if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
                            st.session_state.champion = bracket[-2]['matches'][0]['winner']
                            st.session_state.third_place = bracket[-1]['matches'][0]['winner']
                            st.session_state.stage = "end"
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Все матчи сыграны – возможно, осталось только финишировать
        if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
            st.session_state.champion = bracket[-2]['matches'][0]['winner']
            st.session_state.third_place = bracket[-1]['matches'][0]['winner']
            st.session_state.stage = "end"
            st.rerun()
        else:
            st.info("Все возможные матчи завершены. Ожидайте...")

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
    render_bracket_html()
