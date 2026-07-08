import streamlit as st
import itertools
import random
import pandas as pd
import json
from collections import defaultdict
import math

# --- Настройка страницы ---
st.set_page_config(page_title="Ping-Pong Pro Tournament", page_icon="🏓", layout="wide")

# --- Инициализация состояния ---
def init_state():
    if 'stage' not in st.session_state:
        st.session_state.stage = 'setup'          # setup, group, playoff, end
        st.session_state.players = []
        st.session_state.matches = []             # список сыгранных матчей (группа)
        st.session_state.pairs = []               # все пары для группового этапа
        st.session_state.playoff_bracket = []     # сетка плей-офф
        st.session_state.current_round_idx = 0    # индекс текущего раунда для отображения
        st.session_state.champion = None
        st.session_state.third_place = None
        st.session_state.target_score = 11        # очков для победы
        st.session_state.tournament_name = "Ping-Pong Pro"

init_state()

# --- Стили (Premium Dark UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .st-emotion-cache-16txtl3 { padding: 2rem 1rem; }
    h1, h2, h3, .player-name { font-family: 'Montserrat', sans-serif; font-weight: 800; }
    .main-card {
        background: linear-gradient(145deg, #1e293b, #172033);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 20px;
        transition: all 0.2s;
    }
    .main-card:hover { border-color: #f97316; }
    .player-name { font-size: 28px; color: #f1f5f9; margin: 10px 0; text-transform: uppercase; letter-spacing: 1px; }
    .vs-text { font-size: 16px; color: #f97316; font-weight: 800; letter-spacing: 2px; }
    .stButton>button {
        background: linear-gradient(to right, #f97316, #ea580c);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(to right, #ea580c, #c2410c);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(249, 115, 22, 0.5);
    }
    .bracket-container {
        display: flex;
        overflow-x: auto;
        padding: 20px 0;
        gap: 40px;
        justify-content: center;
        min-height: 300px;
    }
    .round-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        min-width: 200px;
        gap: 20px;
        position: relative;
    }
    .round-column::before {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: -20px;
        border-left: 2px dashed #334155;
    }
    .round-column:first-child::before { display: none; }
    .bracket-match {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        position: relative;
        transition: all 0.2s;
    }
    .bracket-match:hover { border-color: #f97316; }
    .bracket-match.bye-match { opacity: 0.6; border-style: dashed; }
    .bracket-team {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
    }
    .team-name { color: #cbd5e1; }
    .team-score { color: #94a3b8; font-weight: 800; }
    .winner-bg { background-color: rgba(34, 197, 94, 0.15); border-left: 4px solid #22c55e; }
    .winner-text { color: #4ade80 !important; }
    .loser-text { color: #64748b !important; }
    .champion-banner {
        background: radial-gradient(circle, #1e293b, #0f172a);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #f97316;
        box-shadow: 0 0 30px rgba(249, 115, 22, 0.3);
        animation: glow 2s infinite alternate;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 20px rgba(249,115,22,0.3); }
        100% { box-shadow: 0 0 40px rgba(249,115,22,0.7); }
    }
    .dataframe { width: 100%; }
    th { background-color: #1e293b !important; color: #f97316 !important; text-transform: uppercase; }
    td { color: #f1f5f9 !important; background-color: #0f172a !important; }
    .highlight-match {
        border: 2px solid #f97316 !important;
        box-shadow: 0 0 15px rgba(249,115,22,0.5);
    }
    .small-text { font-size: 0.8rem; color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# --- Логика ---
def calculate_standings():
    """Возвращает статистику и отсортированный список игроков."""
    stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'points_for': 0, 'points_against': 0, 'gd': 0, 'played': 0})
    for m in st.session_state.matches:
        p1, p2, o1, o2 = m['p1'], m['p2'], m['o1'], m['o2']
        winner = p1 if o1 > o2 else p2
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
            stats[p2]['losses'] += 1
        else:
            stats[p2]['wins'] += 1
            stats[p1]['losses'] += 1
    sorted_players = sorted(st.session_state.players,
                            key=lambda p: (-stats[p]['wins'], -stats[p]['gd'], -stats[p]['points_for']))
    return stats, sorted_players

def parse_score(score_str, target):
    """Парсит строку счёта, проверяет валидность относительно target."""
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
    """Размещает игроков в сетке по стандартному сеянию, возвращает слоты."""
    slots = ["TBD"] * size
    n = len(players)
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
    """Генерирует полную сетку плей-офф с учётом баев и автоматически завершает матчи с TBD."""
    stats, sorted_players = calculate_standings()
    n_players = len(sorted_players)
    # ближайшая степень двойки, не меньше n_players
    size = 1
    while size < n_players:
        size *= 2
    if size < 4:
        size = 4  # минимум 4 для полуфиналов + финал + матч за 3 место
    # размещаем игроков
    slots = seed_players(sorted_players, size)
    # формируем первый раунд
    matches_round1 = []
    for i in range(0, size, 2):
        matches_round1.append({
            "p1": slots[i],
            "p2": slots[i+1],
            "winner": None,
            "score": ""
        })
    rounds = [{"name": "1/8 финала" if size == 16 else ("1/4 финала" if size == 8 else "1/2 финала"),
               "matches": matches_round1}]
    # создаём следующие раунды
    current_size = size
    while current_size > 1:
        current_size //= 2
        if current_size == 1:
            round_name = "Финал"
        elif current_size == 2:
            round_name = "Полуфиналы"
        elif current_size == 4:
            round_name = "Четвертьфиналы"
        else:
            round_name = f"1/{current_size*2} финала"  # например, 1/8
        empty_matches = [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""} for _ in range(current_size)]
        rounds.append({"name": round_name, "matches": empty_matches})
    # матч за 3-е место
    rounds.append({"name": "Матч за 3-е место", "matches": [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""}]})
    st.session_state.playoff_bracket = rounds
    # Автоматически обрабатываем баи (матчи с TBD) в первом раунде
    process_byes(0)

def process_byes(round_idx):
    """Проверяет матчи в указанном раунде: если один из участников TBD, победителем становится другой,
       и прокидка происходит автоматически."""
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
        # если оба TBD – ничего не делаем (такого быть не должно)
    # После обработки текущего раунда прокидваем победителей в следующий раунд
    propagate_winners(round_idx)

def propagate_winners(round_idx):
    """Прокидывает победителей из раунда round_idx в следующий раунд."""
    bracket = st.session_state.playoff_bracket
    if round_idx >= len(bracket) - 1:
        return  # последний раунд (матч за 3 место) не прокидвается дальше
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
    # Рекурсивно обрабатываем следующий раунд (если там уже все победители известны – они и так записаны)
    process_byes(round_idx + 1)

def render_bracket_html():
    """Генерирует HTML для визуализации сетки с подсветкой текущего матча."""
    html = "<div class='bracket-container'>"
    bracket = st.session_state.playoff_bracket
    for r_idx, round_data in enumerate(bracket):
        html += f"<div class='round-column'><h4 style='color:#f97316; text-align:center; margin-bottom:15px;'>{round_data['name']}</h4>"
        for m in round_data['matches']:
            p1, p2, sc, winner = m['p1'], m['p2'], m['score'], m['winner']
            # Определяем, является ли матч баем
            is_bye = (p1 == "TBD" or p2 == "TBD") and winner is not None and sc == "Бай"
            p1_class = "winner-text" if winner == p1 else ("loser-text" if winner else "team-name")
            p2_class = "winner-text" if winner == p2 else ("loser-text" if winner else "team-name")
            match_class = "winner-bg" if winner else ""
            if is_bye:
                match_class += " bye-match"
            # Подсветка текущего матча (если ещё не сыгран и оба участника известны)
            if not winner and p1 != "TBD" and p2 != "TBD" and r_idx == st.session_state.get('current_round_idx', 0):
                match_class += " highlight-match"
            score_parts = sc.split(":") if sc and sc != "Бай" else ["", ""]
            s1 = score_parts[0] if len(score_parts) > 0 else ""
            s2 = score_parts[1] if len(score_parts) > 1 else ""
            if is_bye:
                s1, s2 = "—", "—"  # для бая не показываем счёт
            html += f"""
                <div class='bracket-match {match_class}'>
                    <div class='bracket-team'><span class='{p1_class}'>{p1 if p1!="TBD" else "—"}</span> <span class='team-score'>{s1}</span></div>
                    <div class='bracket-team'><span class='{p2_class}'>{p2 if p2!="TBD" else "—"}</span> <span class='team-score'>{s2}</span></div>
                </div>
            """
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# --- Интерфейс ---
st.markdown("<h1 style='text-align:center; color:#f97316;'>🏓 PING-PONG PRO</h1>", unsafe_allow_html=True)

# Боковое меню
with st.sidebar:
    st.markdown("### ⚙️ Управление")
    if st.session_state.stage != 'setup':
        if st.button("🔄 Сбросить турнир", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_state()
            st.rerun()
    st.markdown("---")
    st.markdown("### 💾 Сохранение")
    if st.session_state.stage != 'setup':
        # Создаём копию состояния для сохранения
        save_data = {k: v for k, v in st.session_state.items()}
        st.download_button("⬇️ Скачать прогресс (.json)",
                           data=json.dumps(save_data, ensure_ascii=False, default=str),
                           file_name="tournament_save.json")
    uploaded = st.file_uploader("⬆️ Загрузить прогресс", type=['json'])
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
    st.caption(f"Версия 2.0 • {st.session_state.tournament_name}")

# --- ЭТАП 1: НАСТРОЙКА ---
if st.session_state.stage == 'setup':
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("<h2>Настройка турнира</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        num_players = st.number_input("Игроков", 2, 16, min(4, 4), 1)
        target = st.selectbox("Очков для победы", [11, 15, 21], index=0)
    with col2:
        st.write("Введите имена участников:")
        names = []
        for i in range(int(num_players)):
            names.append(st.text_input(f"Игрок {i+1}", key=f"p_{i}"))
    # Кнопка редактирования (очищает имена для повторного ввода)
    if st.button("СТАРТ 🚀", use_container_width=True):
        if any(n.strip() == "" for n in names):
            st.error("Заполните все имена!")
        else:
            st.session_state.players = [n.strip() for n in names]
            st.session_state.target_score = target
            st.session_state.pairs = list(itertools.combinations(st.session_state.players, 2))
            random.shuffle(st.session_state.pairs)
            st.session_state.stage = 'group'
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- ЭТАП 2: ГРУППОВОЙ ЭТАП ---
elif st.session_state.stage == 'group':
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Текущий матч</h3>", unsafe_allow_html=True)

        played_idxs = {m['pair_idx'] for m in st.session_state.matches}
        idx, current_match = next(((i, p) for i, p in enumerate(st.session_state.pairs) if i not in played_idxs), (None, None))

        if current_match:
            p1, p2 = current_match
            st.markdown(f"<div class='player-name'>{p1}</div><div class='vs-text'>VS</div><div class='player-name'>{p2}</div>", unsafe_allow_html=True)
            with st.form("score_form"):
                score = st.text_input("Счёт (например, 11:8)", placeholder=f"11:{st.session_state.target_score-2}")
                if st.form_submit_button("Сохранить результат", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score, st.session_state.target_score)
                        st.session_state.matches.append({
                            'p1': p1, 'p2': p2,
                            'o1': o1, 'o2': o2,
                            'pair_idx': idx
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
            if st.button("Сгенерировать Плей-офф 🏆", use_container_width=True):
                generate_playoff_bracket()
                st.session_state.stage = 'playoff'
                st.session_state.current_round_idx = 0
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
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
                "Разница": stats[p]['gd']
            })
        df = pd.DataFrame(data)
        # Стилизация строк
        def style_df(row):
            colors = []
            for _ in row:
                if row.name < 4:
                    colors.append('background-color: rgba(34, 197, 94, 0.15); color: #4ade80;')
                else:
                    colors.append('background-color: #0f172a; color: #f1f5f9;')
            return colors
        st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

# --- ЭТАП 3: ПЛЕЙ-ОФФ ---
elif st.session_state.stage == 'playoff':
    st.markdown("<h2 style='text-align:center;'>🏆 Турнирная сетка</h2>", unsafe_allow_html=True)
    render_bracket_html()

    st.markdown("---")

    # Поиск текущего несыгранного матча (где оба участника известны, победитель не определён)
    current_match = None
    current_round_idx = None
    current_match_idx = None
    bracket = st.session_state.playoff_bracket
    for r_idx, round_data in enumerate(bracket):
        for m_idx, m in enumerate(round_data['matches']):
            if m['winner'] is None and m['p1'] != "TBD" and m['p2'] != "TBD":
                current_match = m
                current_round_idx = r_idx
                current_match_idx = m_idx
                break
        if current_match:
            break

    # Если есть матч для ввода счёта
    if current_match:
        st.session_state.current_round_idx = current_round_idx
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{bracket[current_round_idx]['name']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='player-name'>{current_match['p1']}</div><div class='vs-text'>VS</div><div class='player-name'>{current_match['p2']}</div>", unsafe_allow_html=True)
            with st.form("po_score"):
                score = st.text_input("Счёт", placeholder=f"{st.session_state.target_score}:{st.session_state.target_score-2}")
                if st.form_submit_button("Записать", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score, st.session_state.target_score)
                        winner = current_match['p1'] if o1 > o2 else current_match['p2']
                        loser = current_match['p2'] if o1 > o2 else current_match['p1']
                        # Сохраняем результат
                        bracket[current_round_idx]['matches'][current_match_idx]['winner'] = winner
                        bracket[current_round_idx]['matches'][current_match_idx]['score'] = f"{o1}:{o2}"
                        # Прокидываем победителя в следующий раунд
                        propagate_winners(current_round_idx)
                        # Проверяем, не закончился ли турнир
                        if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
                            st.session_state.champion = bracket[-2]['matches'][0]['winner']
                            st.session_state.third_place = bracket[-1]['matches'][0]['winner']
                            st.session_state.stage = 'end'
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Все матчи сыграны – переходим в финал
        if bracket[-2]['matches'][0]['winner'] is not None and bracket[-1]['matches'][0]['winner'] is not None:
            st.session_state.champion = bracket[-2]['matches'][0]['winner']
            st.session_state.third_place = bracket[-1]['matches'][0]['winner']
            st.session_state.stage = 'end'
            st.rerun()
        else:
            st.info("Все возможные матчи завершены. Ожидайте...")

# --- ЭТАП 4: ФИНИШ ---
elif st.session_state.stage == 'end':
    third_place = st.session_state.playoff_bracket[-1]['matches'][0]['winner']
    st.markdown(f"""
    <div class='champion-banner'>
        <h2 style='color:#f97316; letter-spacing:3px; margin-bottom:10px;'>ЧЕМПИОН ТУРНИРА</h2>
        <h1 style='font-size:50px; color:#fbbf24; text-shadow: 0 0 20px rgba(251, 191, 36, 0.5);'>{st.session_state.champion}</h1>
        <h3 style='color:#94a3b8; margin-top:20px;'>🥉 3-е место: {third_place}</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; margin-top:40px;'>Итоговая сетка</h3>", unsafe_allow_html=True)
    render_bracket_html()
