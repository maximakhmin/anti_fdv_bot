import fastf1
import datetime
import pandas as pd


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
                time_str = f"  +{gap_seconds:.3f}"
            
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
                    delta =f"{time0.seconds//60}:{time0.seconds%60:02}.{time0.microseconds//1000}"

                else:
                    if pos<=10: q="Q3"
                    elif pos<=16: q="Q2"
                    else: q="Q1"
                    if pd.isna(results.iloc[i][q]):
                        delta = "No time"
                    else:
                        timedelta = results.iloc[i][q] - time0
                        delta = f"  +{timedelta.seconds}.{timedelta.microseconds//1000}"

            elif t in ["R", "S"]:
                if i==0:
                    lap0 = int(results.iloc[i]["Laps"])
                    delta = f"{lap0} L"
                elif results.iloc[i]["Status"] == "Finished":
                    time = results.iloc[i]["Time"]
                    delta = f"+{time.seconds}.{time.microseconds//1000}"
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

