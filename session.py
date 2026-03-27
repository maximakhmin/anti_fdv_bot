import fastf1
import datetime
import pandas as pd

fastf1.set_log_level('ERROR')

def load_data(s, r, t):
    session = fastf1.get_session(s, r, t)
    session.load()
    results = session.results
    if len(results)==0:
        return -1, "No results, try later"
    print(results)
    table = []

    if t in ["FP1", "FP2", "FP3"]:
        fastest_laps = session.laps.pick_quicklaps().sort_values(by='LapTime').reset_index()

        if fastest_laps.empty:
            return -1, "No results, try later"
        
        merged = pd.merge(fastest_laps, session.results, left_on='Driver', right_on='Abbreviation')
        merged = merged.sort_values(by='LapTime').reset_index(drop=True)

        best_time_overall = merged.iloc[0]['LapTime']
        
        table = []
        added_drivers = []
        pos = 1
        for i, row in merged.iterrows():
            driver_name = row['FullName']
            current_lap_time = row['LapTime']

            if driver_name in added_drivers:
                continue
            
            if i == 0:
                total_seconds = current_lap_time.total_seconds()
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                time_str = f"{minutes}:{seconds:06.3f}"
            else:
                gap = current_lap_time - best_time_overall
                gap_seconds = gap.total_seconds()
                time_str = f"+{gap_seconds:.3f}"
            
            added_drivers.append(driver_name)
            table.append((pos, driver_name, time_str))
            pos += 1
            

    else:
        for i in range(len(results)):
            pos = i+1
            name = results.iloc[i]["FullName"]
            delta = ""


            if t in ["Q", "SQ"]:
                if pos==1:
                    time0 = results.iloc[i]["Q3"]
                    delta =f"{time0.seconds//60}:{(time0.seconds%60 + time0.microseconds/1000000):06.3f}"

                else:
                    if pos<=10: q="Q3"
                    elif pos<=16: q="Q2"
                    else: q="Q1"
                    if pd.isna(results.iloc[i][q]):
                        delta = "No time"
                    else:
                        timedelta = results.iloc[i][q] - time0
                        delta = f"+{(timedelta.seconds + timedelta.microseconds/1000000):.3f}"

            elif t in ["R", "S"]:
                if i==0:
                    lap0 = int(results.iloc[i]["Laps"])
                    delta = f"{lap0} L"
                elif results.iloc[i]["Status"] == "Finished":
                    time = results.iloc[i]["Time"]
                    delta = f"+{(timedelta.seconds + timedelta.microseconds/1000000):.3f}"
                elif results.iloc[i]["Status"] == "Lapped":
                    laps = int(results.iloc[i]["Laps"])
                    delta = f"+{lap0-laps} L"
                else:
                    delta = "No data"

            table.append((pos, name, delta))

    mes = f"Season {s}, round {r}, {t} results\n\n"
    mes += "<pre>"
    for elem in table:
        pos = f"{elem[0]}.".ljust(3)
        name = f"{elem[1]}".ljust(19)
        delta = f"{elem[2]}".ljust(10)
        mes += f"{pos} {name} {delta}\n"
    mes += "</pre>"

    return 0, mes


def get_f1_session_results(year, round_num, session_type):
    try:
    
        session = fastf1.get_session(year, round_num, session_type)
        # Загружаем данные. Для Квалы и Гонки нам важны результаты (results)
        session.load(laps=True, telemetry=False, weather=False)

        if session.laps.empty or session.results.empty:
            return -1, "Try later"
    
    except Exception as e:
        return -1, f"Try later, {e}"

    results_array = []

    # --- ЛОГИКА ДЛЯ ПРАКТИК (FP1, FP2, FP3) ---
    if 'FP' in session_type.upper():
        # Сортируем по самому быстрому кругу
        fastest_laps = session.laps.pick_quicklaps().sort_values(by='LapTime').reset_index()
        best_time_overall = fastest_laps.iloc[0]['LapTime']
        added = []
        pos = 0
        for i, row in fastest_laps.iterrows():
            full_name = session.results.loc[session.results['Abbreviation'] == row['Driver'], 'FullName'].iloc[0]
            if full_name in added:
                continue
            added.append(full_name)
            pos += 1
            if i == 0:
                t = row['LapTime'].total_seconds()
                time_str = f"{int(t // 60)}:{t % 60:06.3f}"
            else:
                gap = (row['LapTime'] - best_time_overall).total_seconds()
                time_str = f"+{gap:.3f}"
            results_array.append((pos, full_name, time_str))

    # --- ЛОГИКА ДЛЯ КВАЛИФИКАЦИИ (Q) ---
    elif 'Q' in session_type.upper():
        # В квалификации FastF1 заполняет session.results почти сразу.
        # Нам нужно выбрать лучшее время из Q1, Q2 или Q3.
        for i in range(len(session.results)):
            row = session.results.iloc[i]
            pos = f"{i + 1:02}"
            full_name = row['FullName']
            
            # Берем лучшее время из всех сегментов
            times = [row['Q1'], row['Q2'], row['Q3']]
            valid_times = [t for t in times if pd.notna(t)]
            
            if i == 0:
                best_q_time = valid_times[-1] if valid_times else None
                if best_q_time:
                    t = best_q_time.total_seconds()
                    time_str = f"{int(t // 60)}:{t % 60:06.3f}"
                else:
                    time_str = "No Time"
                best_overall = best_q_time
            else:
                current_best = valid_times[-1] if valid_times else None
                if current_best and best_overall:
                    gap = (current_best - best_overall).total_seconds()
                    time_str = f"+{gap:.3f}"
                else:
                    time_str = "No Time"
            
            results_array.append((pos, full_name, time_str))

    # --- ЛОГИКА ДЛЯ ГОНОК (R, S) ---
    else:
        last_laps = session.laps.groupby('Driver').last().reset_index()
        last_laps = last_laps.sort_values(by=['LapNumber', 'Time'], ascending=[False, True]).reset_index(drop=True)
        
        winner_finish_time = last_laps.iloc[0]['Time']
        max_laps = last_laps.iloc[0]['LapNumber']

        for i, row in last_laps.iterrows():
            pos = f"{i + 1:02}"
            driver_code = row['Driver']
            full_name = session.results.loc[session.results['Abbreviation'] == driver_code, 'FullName'].iloc[0]

            if i == 0:
                time_str = "WINNER"
            else:
                current_laps = row['LapNumber']
                if current_laps < max_laps:
                    time_str = f"-{int(max_laps - current_laps)} lp"
                else:
                    gap = (row['Time'] - winner_finish_time).total_seconds()
                    time_str = f"+{gap:.3f}"
            results_array.append((pos, full_name, time_str))

    mes = f"Season {year}, round {round_num}, {session_type} results\n\n"
    mes += "<pre>"
    for elem in results_array:
        pos = f"{elem[0]}.".ljust(3)
        name = f"{elem[1]}".ljust(19)
        delta = f"{elem[2]}".ljust(10)
        mes += f"{pos} {name} {delta}\n"
    mes += "</pre>"

    return 0, mes


# print(get_f1_session_results(2026, 2, "Q"))