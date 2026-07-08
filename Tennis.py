import streamlit as st
import itertools
import random
import pandas as pd
import json
from collections import defaultdict

# --- Настройка страницы ---
st.set_page_config(page_title="Ping-Pong Pro Tournament", page_icon="🏓", layout="wide")

# --- Инициализация состояния ---
def init_state():
    if 'stage' not in st.session_state:
        st.session_state.stage = 'setup'
        st.session_state.players = []
        st.session_state.matches = []
        st.session_state.pairs = []
        st.session_state.playoff_bracket = []
        st.session_state.playoff_round = 0
        st.session_state.champion = None
        st.session_state.third_place = None

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
    }
    
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
    
    /* Сетка плей-офф */
    .bracket-container { display: flex; overflow-x: auto; padding: 20px 0; gap: 40px; }
    .round-column { display: flex; flex-direction: column; justify-content: space-around; min-width: 200px; gap: 20px; }
    .bracket-match {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        position: relative;
    }
    .bracket-team {
        display: flex; justify-content: space-between; padding: 5px 0;
        font-family: 'Montserrat', sans-serif; font-weight: 600;
    }
    .team-name { color: #cbd5e1; }
    .team-score { color: #94a3b8; font-weight: 800; }
    .winner-bg { background-color: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; }
    .winner-text { color: #4ade80 !important; }
    .loser-text { color: #64748b !important; }
    
    .champion-banner {
        background: radial-gradient(circle, #1e293b, #0f172a);
        padding: 40px; border-radius: 20px; text-align: center;
        border: 2px solid #f97316;
        box-shadow: 0 0 30px rgba(249, 115, 22, 0.3);
    }
    
    /* Таблица */
    .dataframe { width: 100%; }
    th { background-color: #1e293b !important; color: #f97316 !important; text-transform: uppercase; }
    td { color: #f1f5f9 !important; background-color: #0f172a !important; }
    </style>
""", unsafe_allow_html=True)

# --- Логика ---
def calculate_standings():
    stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'points_for': 0, 'points_against': 0, 'gd': 0, 'played': 0})
    for m in st.session_state.matches:
        p1, p2, o1, o2 = m['p1'], m['p2'], m['o1'], m['o2']
        winner = p1 if o1 > o2 else p2
        
        stats[p1]['played'] += 1; stats[p2]['played'] += 1
        stats[p1]['points_for'] += o1; stats[p1]['points_against'] += o2
        stats[p2]['points_for'] += o2; stats[p2]['points_against'] += o1
        stats[p1]['gd'] += o1 - o2; stats[p2]['gd'] += o2 - o1
        
        if winner == p1: stats[p1]['wins'] += 1; stats[p2]['losses'] += 1
        else: stats[p2]['wins'] += 1; stats[p1]['losses'] += 1

    sorted_players = sorted(st.session_state.players, key=lambda p: (-stats[p]['wins'], -stats[p]['gd'], -stats[p]['points_for']))
    return stats, sorted_players

def generate_playoff_bracket():
    stats, sorted_players = calculate_standings()
    
    # Определяем размер сетки (4, 8 или 16)
    if len(sorted_players) <= 4: size = 4
    elif len(sorted_players) <= 8: size = 8
    else: size = 16
        
    seeds = sorted_players[:size]
    # Стандартное сеяние: 1 vs 8, 4 vs 5, 2 vs 7, 3 vs 6...
    seeded_bracket = []
    pairs_seed = [(1,8), (4,5), (2,7), (3,6), (1,8), (4,5), (2,7), (3,6)] # Упрощенно для до 16
    
    # Формируем первый раунд
    round_1 = []
    temp_seeds = seeds[:]
    while len(temp_seeds) < size: temp_seeds.append("TBD")
    
    # Сеяние по стандарту
    if size == 4:
        matchups = [(0,3), (1,2)]
    elif size == 8:
        matchups = [(0,7), (3,4), (1,6), (2,5)]
    else:
        matchups = [(0,15), (7,8), (3,12), (4,11), (1,14), (6,9), (2,13), (5,10)]
        
    for a, b in matchups:
        round_1.append({"p1": temp_seeds[a], "p2": temp_seeds[b], "winner": None, "score": ""})
        
    rounds = [{"name": f"Раунд 1", "matches": round_1}]
    
    # Создаем пустые раунды
    current_size = size
    while current_size > 1:
        current_size //= 2
        round_name = "Финал" if current_size == 1 else ("Полуфиналы" if current_size == 2 else "Четвертьфиналы")
        empty_matches = [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""} for _ in range(current_size)]
        rounds.append({"name": round_name, "matches": empty_matches})
        
    # Добавляем матч за 3-е место
    rounds.append({"name": "Матч за 3-е место", "matches": [{"p1": "TBD", "p2": "TBD", "winner": None, "score": ""}]})
    
    st.session_state.playoff_bracket = rounds
    st.session_state.playoff_round = 0

def render_bracket_html():
    html = "<div class='bracket-container'>"
    for r_idx, round_data in enumerate(st.session_state.playoff_bracket):
        html += f"<div class='round-column'><h4 style='color:#f97316; text-align:center; margin-bottom:15px;'>{round_data['name']}</h4>"
        for m in round_data['matches']:
            p1, p2, sc, winner = m['p1'], m['p2'], m['score'], m['winner']
            
            p1_class = "winner-text" if winner == p1 else ("loser-text" if winner else "team-name")
            p2_class = "winner-text" if winner == p2 else ("loser-text" if winner else "team-name")
            match_class = "winner-bg" if winner else ""
            
            score_parts = sc.split(":") if sc else ["", ""]
            s1 = score_parts[0] if len(score_parts) > 0 else ""
            s2 = score_parts[1] if len(score_parts) > 1 else ""
            
            html += f"""
                <div class='bracket-match {match_class}'>
                    <div class='bracket-team'><span class='{p1_class}'>{p1}</span> <span class='team-score'>{s1}</span></div>
                    <div class='bracket-team'><span class='{p2_class}'>{p2}</span> <span class='team-score'>{s2}</span></div>
                </div>
            """
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def parse_score(score_str):
    parts = score_str.replace(":", " ").split()
    if len(parts) != 2: raise ValueError("Формат: X:Y")
    o1, o2 = map(int, parts)
    if o1 == o2: raise ValueError("Ничья невозможна!")
    if max(o1, o2) < 11: raise ValueError("Нужно минимум 11 очков!")
    if abs(o1 - o2) < 2 and max(o1, o2) >= 11: raise ValueError("Разница должна быть 2 очка!")
    return o1, o2

# --- Интерфейс ---
st.markdown("<h1 style='text-align:center; color:#f97316;'>🏓 PING-PONG PRO</h1>", unsafe_allow_html=True)

# Боковое меню
with st.sidebar:
    st.markdown("### ⚙️ Управление")
    if st.session_state.stage != 'setup':
        if st.button("🔄 Сбросить турнир", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            init_state()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 💾 Сохранение")
    if st.session_state.stage != 'setup':
        download_data = {k: v for k, v in st.session_state.items()}
        st.download_button("⬇️ Скачать прогресс (.json)", data=json.dumps(download_data, ensure_ascii=False), file_name="tournament_save.json")
        
    uploaded = st.file_uploader("⬆️ Загрузить прогресс", type=['json'])
    if uploaded:
        try:
            data = json.load(uploaded)
            for k, v in data.items(): st.session_state[k] = v
            st.success("Прогресс загружен!")
            st.rerun()
        except:
            st.error("Ошибка файла")

# --- ЭТАП 1: НАСТРОЙКА ---
if st.session_state.stage == 'setup':
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("<h2>Настройка турнира</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        num_players = st.number_input("Игроков", 2, 16, 4, 1)
    with col2:
        st.write("Список участников:")
        names = []
        for i in range(int(num_players)):
            names.append(st.text_input(f"Игрок {i+1}", key=f"p_{i}"))
            
    if st.button("СТАРТ 🚀", use_container_width=True):
        if any(n.strip()=="" for n in names):
            st.error("Заполните все имена!")
        else:
            st.session_state.players = names
            st.session_state.pairs = list(itertools.combinations(names, 2))
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
        
        played_idxs = [m['pair_idx'] for m in st.session_state.matches]
        idx, current_match = next(((i, p) for i, p in enumerate(st.session_state.pairs) if i not in played_idxs), (None, None))
        
        if current_match:
            p1, p2 = current_match
            st.markdown(f"<div class='player-name'>{p1}</div><div class='vs-text'>VS</div><div class='player-name'>{p2}</div>", unsafe_allow_html=True)
            
            with st.form("score_form"):
                score = st.text_input("Счет (11:8)", placeholder="Например: 11:8")
                if st.form_submit_button("Сохранить результат", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score)
                        st.session_state.matches.append({'p1':p1, 'p2':p2, 'o1':o1, 'o2':o2, 'pair_idx':idx})
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                        
            if st.session_state.matches:
                if st.button("↩ Отменить последний", use_container_width=True):
                    st.session_state.matches.pop()
                    st.rerun()
        else:
            st.success("Групповой этап завершен!")
            if st.button("Сгенерировать Плей-офф 🏆", use_container_width=True):
                generate_playoff_bracket()
                st.session_state.stage = 'playoff'
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h3>Таблица лидеров</h3>", unsafe_allow_html=True)
        stats, sorted_p = calculate_standings()
        data = []
        for i, p in enumerate(sorted_p, 1):
            data.append({
                "Место": i, "Игрок": p, "И": stats[p]['played'], "В": stats[p]['wins'], 
                "П": stats[p]['losses'], "Очки": f"{stats[p]['points_for']}:{stats[p]['points_against']}",
                "Разница": stats[p]['gd']
            })
        df = pd.DataFrame(data)
        
        def style_df(row):
            colors = []
            for _ in row:
                if row.name < 4: colors.append('background-color: rgba(34, 197, 94, 0.15); color: #4ade80;')
                else: colors.append('background-color: #0f172a; color: #f1f5f9;')
            return colors
            
        st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

# --- ЭТАП 3: ПЛЕЙ-ОФФ ---
elif st.session_state.stage == 'playoff':
    st.markdown("<h2 style='text-align:center;'>🏆 Турнирная сетка</h2>", unsafe_allow_html=True)
    render_bracket_html()
    
    st.markdown("---")
    
    # Логика поиска текущего матча в плей-офф
    # Идем по раундам, ищем первый матч без победителя, где оба игрока известны
    current_match_info = None
    for r_idx, round_data in enumerate(st.session_state.playoff_bracket[:-1]): # Исключаем матч за 3 место, он идет отдельно
        for m_idx, m in enumerate(round_data['matches']):
            if not m['winner'] and m['p1'] != "TBD" and m['p2'] != "TBD":
                current_match_info = (r_idx, m_idx, m)
                break
        if current_match_info: break
            
    # Если основных матчей нет, проверяем матч за 3-е место
    if not current_match_info and not st.session_state.playoff_bracket[-1]['matches'][0]['winner']:
        third_match = st.session_state.playoff_bracket[-1]['matches'][0]
        if third_match['p1'] != "TBD" and third_match['p2'] != "TBD":
            current_match_info = (len(st.session_state.playoff_bracket)-1, 0, third_match)
            
    if current_match_info:
        r_idx, m_idx, match = current_match_info
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{st.session_state.playoff_bracket[r_idx]['name']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='player-name'>{match['p1']}</div><div class='vs-text'>VS</div><div class='player-name'>{match['p2']}</div>", unsafe_allow_html=True)
            
            with st.form("po_score"):
                score = st.text_input("Счет", placeholder="11:7")
                if st.form_submit_button("Записать", use_container_width=True):
                    try:
                        o1, o2 = parse_score(score)
                        winner = match['p1'] if o1 > o2 else match['p2']
                        loser = match['p2'] if o1 > o2 else match['p1']
                        
                        st.session_state.playoff_bracket[r_idx]['matches'][m_idx]['winner'] = winner
                        st.session_state.playoff_bracket[r_idx]['matches'][m_idx]['score'] = f"{o1}:{o2}"
                        
                        # Прокидываем победителя в следующий раунд
                        if r_idx < len(st.session_state.playoff_bracket) - 2: # Не финал
                            next_r = r_idx + 1
                            next_m_idx = m_idx // 2
                            if m_idx % 2 == 0:
                                st.session_state.playoff_bracket[next_r]['matches'][next_m_idx]['p1'] = winner
                            else:
                                st.session_state.playoff_bracket[next_r]['matches'][next_m_idx]['p2'] = winner
                                
                            # Если это полуфинал (next_r - последний перед матчем за 3 место), записываем проигравших
                            if st.session_state.playoff_bracket[next_r]['name'] == "Финал":
                                third_match = st.session_state.playoff_bracket[-1]['matches'][0]
                                if m_idx == 0: third_match['p1'] = loser
                                else: third_match['p2'] = loser
                        else:
                            # Финал сыгран
                            st.session_state.champion = winner
                            st.session_state.stage = 'end'
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        # Если все матчи сыграны, но мы еще не в end (на случай сбоев)
        if st.session_state.playoff_bracket[-2]['matches'][0]['winner'] and st.session_state.playoff_bracket[-1]['matches'][0]['winner']:
            st.session_state.champion = st.session_state.playoff_bracket[-2]['matches'][0]['winner']
            st.session_state.third_place = st.session_state.playoff_bracket[-1]['matches'][0]['winner']
            st.session_state.stage = 'end'
            st.rerun()

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
