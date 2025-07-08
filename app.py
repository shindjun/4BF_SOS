import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# ============ 1부: 기준시간 입력 ===============
st.sidebar.header("🕒 현재 시각 입력")
base_date = st.sidebar.date_input("기준일자", value=datetime.date.today())
base_start = st.sidebar.text_input("기준 시작시각", value="07:00")
base_end = st.sidebar.text_input("기준 종료시각", value="07:00")
cur_time = st.sidebar.text_input("현재 시각 입력 (예: 17:32)", value=datetime.datetime.now().strftime("%H:%M"))

# 경과시간(분) 계산
try:
    start_hour, start_min = map(int, base_start.split(":"))
    cur_hour, cur_min = map(int, cur_time.split(":"))
    base_start_dt = datetime.datetime.combine(base_date, datetime.time(start_hour, start_min))
    cur_dt = datetime.datetime.combine(base_date, datetime.time(cur_hour, cur_min))
    # 24시 교대 고려
    if cur_dt < base_start_dt:
        cur_dt += datetime.timedelta(days=1)
    elapsed_minutes = (cur_dt - base_start_dt).total_seconds() / 60
except Exception as e:
    elapsed_minutes = 0

st.sidebar.markdown(f"**경과시간:** {elapsed_minutes:.1f}분")

# =========== 2부: 정상조업 기본입력 ================
st.sidebar.header("① 정상조업 기본입력")
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)
if coke_per_charge > 0:
    oc_ratio = ore_per_charge / coke_per_charge
else:
    oc_ratio = 0
st.sidebar.markdown(f"**O/C 비율:** {oc_ratio:.2f}")

# T.Fe, 슬래그비율, 환원율(자동계산 or 입력값 병행)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
auto_slag_ratio = ore_per_charge / coke_per_charge * 0.15  # 예시 공식, 실측공식으로 대체 가능
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=round(auto_slag_ratio, 2))
auto_red_eff = 1 + (tfe_percent - 55) * 0.01
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=round(auto_red_eff, 3))

melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm3/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm3/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)
humidification = st.sidebar.number_input("조습량 (g/Nm3)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)
wind_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

# ========== 3부: 종료된 Tap별 출선 추적 및 슬래그분리 입력 ==========
st.sidebar.header("② 출선 추적(종료Tap/선행/후행)")
tap_count = st.sidebar.number_input("종료된 Tap 수", min_value=0, step=1, value=5)
fixed_avg_tap_time = st.sidebar.number_input("평균 TAP당 출선소요시간(분)", value=298)
fixed_avg_tap_speed = st.sidebar.number_input("평균 TAP당 출선속도(ton/min)", value=4.62)
fixed_avg_tap_output = st.sidebar.number_input("평균 TAP당 출선량(ton)", value=1120.0)
fixed_avg_slag_time = st.sidebar.number_input("Tap당 슬래그 분리시간(분)", value=32.0)
tap_total_output = st.sidebar.number_input("종료된 Tap 출선량(실측값, ton, 미입력시 계산값 사용)", value=0.0)

# Tap별 상세 입력(선택): 슬래그 분리시간 포함 예시(옵션)
tap_slag_times = []
for i in range(int(tap_count)):
    slag_time = st.sidebar.number_input(f"Tap#{i+1} 슬래그 분리시간(분)", value=fixed_avg_slag_time, key=f"tap_slag_{i}")
    tap_slag_times.append(slag_time)

# Tap 총 출선량 자동계산
if tap_total_output == 0.0:
    tap_total_output = tap_count * fixed_avg_tap_output

# ------------------- 2부: 슬래그 분리시간 자동통계 --------------------
import numpy as np

# 슬래그 분리시간 Tap별 입력값: tap_slag_times (1부에서 생성)
slag_times_array = np.array(tap_slag_times)
slag_avg = np.mean(slag_times_array)
slag_max = np.max(slag_times_array)
slag_min = np.min(slag_times_array)
slag_std = np.std(slag_times_array)

# 메인 화면에 슬래그 분리시간 통계 결과 표시
st.subheader("⏳ Tap별 슬래그 분리시간 통계")
st.write(f"평균 슬래그 분리시간: **{slag_avg:.1f}분**")
st.write(f"최대 슬래그 분리시간: **{slag_max:.1f}분**")
st.write(f"최소 슬래그 분리시간: **{slag_min:.1f}분**")
st.write(f"표준편차: **{slag_std:.2f}분**")

# Tap별 상세 리스트 표
slag_df = pd.DataFrame({
    "Tap No": [f"Tap#{i+1}" for i in range(int(tap_count))],
    "슬래그 분리시간(분)": tap_slag_times
})
st.dataframe(slag_df)

# 차트 시각화(옵션)
plt.figure(figsize=(7, 2.5))
plt.bar(slag_df["Tap No"], slag_df["슬래그 분리시간(분)"])
plt.title("Tap별 슬래그 분리시간")
plt.ylabel("분")
st.pyplot(plt)

# ------------------ 3부: Tap별 출선 상세입력 및 리포트 저장 ------------------

st.sidebar.markdown("---")
st.sidebar.header("💧 Tap별 출선 상세입력")

# Tap 수 입력 (슬래그 분리시간도 이 Tap수와 연동)
tap_count = st.sidebar.number_input("종료된 Tap 수", min_value=1, step=1, value=3)
tap_numbers = [f"{i+1}" for i in range(int(tap_count))]

# Tap별 입력: 비트, 출선시간(분), 출선속도(ton/min), 슬래그분리시간(분)
tap_bits = []
tap_times = []
tap_speeds = []
tap_slag_times = []

for i in range(int(tap_count)):
    with st.sidebar.expander(f"Tap #{i+1}"):
        bit = st.number_input(f"  출선비트 (mm) [Tap#{i+1}]", value=45, key=f'bit_{i}')
        t_time = st.number_input(f"  출선시간 (분) [Tap#{i+1}]", value=150.0, key=f'time_{i}')
        t_speed = st.number_input(f"  출선속도 (ton/min) [Tap#{i+1}]", value=4.5, key=f'speed_{i}')
        s_time = st.number_input(f"  슬래그 분리시간 (분) [Tap#{i+1}]", value=20.0, key=f'slag_{i}')
        tap_bits.append(bit)
        tap_times.append(t_time)
        tap_speeds.append(t_speed)
        tap_slag_times.append(s_time)

# Tap별 정보 테이블 생성
tap_detail_df = pd.DataFrame({
    "Tap No": tap_numbers,
    "출선비트(mm)": tap_bits,
    "출선시간(분)": tap_times,
    "출선속도(ton/min)": tap_speeds,
    "슬래그 분리시간(분)": tap_slag_times
})

# Tap별 상세 데이터 리포트 테이블 메인 화면 표시
st.subheader("📑 Tap별 상세 출선 기록")
st.dataframe(tap_detail_df)

# CSV 저장(선택)
tap_csv = tap_detail_df.to_csv(index=False).encode('utf-8-sig')
st.download_button("Tap별 상세기록 CSV 다운로드", data=tap_csv, file_name="Tap_Detail_Report.csv", mime='text/csv')

# Tap별 슬래그 분리시간 자동통계 (앞 2부 통계와 연동)
slag_times_array = np.array(tap_slag_times)
slag_avg = np.mean(slag_times_array)
slag_max = np.max(slag_times_array)
slag_min = np.min(slag_times_array)
slag_std = np.std(slag_times_array)

st.write(f"**Tap별 평균 슬래그 분리시간**: {slag_avg:.1f}분 / "
         f"최대: {slag_max:.1f}분 / 최소: {slag_min:.1f}분 / 표준편차: {slag_std:.2f}분")

# ------------------ 4부: 누적 조업 리포트 및 대시보드 시각화 ------------------

st.markdown("---")
st.header("📊 누적 조업 리포트 및 대시보드")

# 07시~현재까지 Tap별, 전체 출선 누적 데이터 요약
st.subheader("✅ 07시 기준 누적 Tap별 출선 데이터")

# Tap별 누적 출선량 (tap_times * tap_speeds)
tap_outputs = [round(a * b, 1) for a, b in zip(tap_times, tap_speeds)]
tap_detail_df["Tap별 출선량(ton)"] = tap_outputs

# Tap별 누적 합계
total_tap_output = sum(tap_outputs)

st.write(f"**누적 Tap별 출선량 합계**: {total_tap_output:.1f} ton")
st.dataframe(tap_detail_df)

# 전체 일일 실시간 누적 배출량 = 종료Tap수×평균tap당출선량 + 선행/후행출선량
if "실측 일일 실시간 누적 배출량" in st.session_state:
    total_realtime_output = st.session_state["실측 일일 실시간 누적 배출량"]
else:
    total_realtime_output = total_tap_output + lead_tap_weight + follow_tap_weight

# 실시간 대시보드 통계
st.subheader("🟢 실시간 조업 현황 요약")
st.write(f"**실시간 누적 출선량**: {total_realtime_output:.1f} ton")
st.write(f"**현재시각 누적 예상생산량**: {expected_till_now:.1f} ton")
st.write(f"**현재시각 기준 저선량**: {expected_till_now - total_realtime_output:.1f} ton")

# Tap별 슬래그 분리시간 통계 시각화
st.subheader("⏱️ Tap별 슬래그 분리시간 통계 (분)")
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(tap_numbers, tap_slag_times, color="#96b6e6")
ax.set_xlabel("Tap No")
ax.set_ylabel("슬래그 분리시간 (분)")
ax.set_title("Tap별 슬래그 분리시간")
for i, v in enumerate(tap_slag_times):
    ax.text(i, v + 1, f"{v:.1f}", ha='center', va='bottom')
st.pyplot(fig)

# 전체 리포트 누적 저장 (Tap 정보 포함)
if "full_report_log" not in st.session_state:
    st.session_state["full_report_log"] = []
full_report_record = {
    "날짜": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "Tap별 출선량": tap_outputs,
    "누적 Tap합계": total_tap_output,
    "실시간 누적 출선량": total_realtime_output,
    "현재시각 누적생산량": expected_till_now,
    "현재시각 저선량": expected_till_now - total_realtime_output,
    "슬래그 분리시간(평균)": slag_avg
}
st.session_state["full_report_log"].append(full_report_record)

# 누적 테이블 및 다운로드
full_report_df = pd.DataFrame(st.session_state["full_report_log"])
st.dataframe(full_report_df)
csv = full_report_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("누적조업 리포트 CSV 다운로드", data=csv, file_name="Full_BlastTap_Report.csv", mime="text/csv")

# ------------------ 5부: AI 기반 용선온도 예측, 출선전략, 공취예상 ------------------

st.markdown("---")
st.header("🤖 AI 기반 예측·추천")

# 1) AI 기반 Tf(용선온도) 예측 (참고지수)
try:
    # 송풍/산소/풍온/PCI/실측온도 등 활용한 보정식
    pci_ton_hr = pci_rate * (daily_expected_production / 1000)
    Tf_ai = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1_000_000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except Exception:
    Tf_ai = None

Tf_ai = max(Tf_ai, 1200) if Tf_ai is not None else None
st.subheader("AI 기반 Tf예상온도 (°C, 참고지수)")
st.write(f"{Tf_ai:.1f}" if Tf_ai else "산출불가")

# 2) 비트경/출선전략 추천
st.subheader("🦾 출선전략 & AI 추천")
# 저선량 및 출선율에 따라 추천값 산출
if (expected_till_now - total_realtime_output) < 100:
    recommended_tap_dia = 43
    next_tap_interval = "15~20분"
elif (expected_till_now - total_realtime_output) < 150:
    recommended_tap_dia = 45
    next_tap_interval = "10~15분"
else:
    recommended_tap_dia = 48
    next_tap_interval = "즉시(0~5분)"

st.write(f"추천 비트경: Ø{recommended_tap_dia}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")

# 3) 선행 출선 폐쇄예상 Lap 시간 (공취예상시간)
st.subheader("⏱️ 선행 출선 폐쇄예상 Lap 시간")
# (후행 출선 시작 후 150분 경과시점 → 선행 Tap 폐쇄권고)
if lead_time > 0 and follow_time > 0:
    closure_lap = max(lead_time - (follow_time + 150), 0)
    closure_lap_str = f"{closure_lap:.1f}분 (예상)" if closure_lap > 0 else "즉시 폐쇄권고"
else:
    closure_lap_str = "입력값 필요"
st.write(f"선행 출선구 폐쇄예상 Lap 시간: {closure_lap_str}")

# 4) 출선/공취 관리 종합 현황표
st.subheader("📑 출선·공취 관리 종합 요약")
st.write(f"""
- **Tap평균 출선량**: {fixed_avg_tap_output:.1f} ton
- **평균 TAP당 출선소요시간**: {fixed_avg_tap_time:.1f}분
- **평균 TAP당 출선속도**: {fixed_avg_tap_speed:.2f} ton/min
- **선행 출선시간/속도/실측출선량**: {lead_time}분 / {lead_speed}t/m / {lead_tap_weight}ton
- **후행 출선시간/속도/실측출선량**: {follow_time}분 / {follow_speed}t/m / {follow_tap_weight}ton
""")

# ------------------ 6부: 실시간 수지 시각화 및 Tap별 이력 ------------------

import matplotlib.pyplot as plt

st.markdown("---")
st.header("📊 실시간 누적 생산·출선·저선량 시각화")

# 시간축 생성 (예: 15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량(예상치) 시계열
gen_series = [daily_expected_production * (t / 1440) for t in time_labels]
# 누적 출선량(실측 누적배출량) 시계열
tap_series = [total_realtime_output] * len(time_labels)
# 저선량(예상 생산 - 누적 출선) 시계열
residual_series = [max(g - total_realtime_output, 0) for g in gen_series]

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량(ton)")
plt.plot(time_labels, tap_series, label="누적 출선량(ton)")
plt.plot(time_labels, residual_series, label="저선량(ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("시간대별 누적 생산/출선/저선량")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# 누적 Tap별 출선 이력, 비트, 시간, 속도, 슬래그분리시간 등 기록표
st.subheader("📋 Tap별 종료이력·슬래그분리 기록")

# 예시용 DataFrame 생성 (실제 적용시 DB/입력 연동 필요)
tap_history = pd.DataFrame({
    "Tap No.": list(range(1, int(completed_taps)+1)),
    "출선비트경": [recommended_tap_dia]*int(completed_taps),
    "출선소요시간(분)": [fixed_avg_tap_time]*int(completed_taps),
    "평균출선속도(t/m)": [fixed_avg_tap_speed]*int(completed_taps),
    "Tap별출선량(ton)": [fixed_avg_tap_output]*int(completed_taps),
    "Tap별슬래그분리(분)": [fixed_avg_tap_time * 0.12]*int(completed_taps)  # 예: 전체 출선시간의 12% 소요 가정
})

st.dataframe(tap_history)

# CSV 다운로드 기능
csv_tap = tap_history.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 Tap별 종료/슬래그기록 CSV", data=csv_tap, file_name="BlastTap_Tap_History.csv", mime='text/csv')

# ------------------ 7부: 누적 조업 리포트 및 요약 ------------------

st.markdown("---")
st.header("📋 누적 조업 리포트 및 종합 요약")

# 주요 요약 값 정리
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "기준일자": base_date,
    "현재시각": current_time.strftime('%H:%M'),
    "예상일일생산량(t/day)": daily_expected_production,
    "현재시각누적생산량(t)": expected_till_now,
    "현재시각누적출선량(t)": total_realtime_output,
    "현재시각 저선량(t)": residual_molten,
    "저선율(%)": residual_rate,
    "AI 기반 Tf예상온도(°C)": Tf_predict,
    "조업상태": status,
    "종료된Tap수": completed_taps,
    "평균 Tap출선량(ton)": fixed_avg_tap_output,
    "평균 Tap출선시간(분)": fixed_avg_tap_time,
    "평균 Tap출선속도(t/m)": fixed_avg_tap_speed,
    "선행출선시간(분)": lead_time,
    "선행출선속도(t/m)": lead_speed,
    "선행출선량(ton, 실측)": lead_output_manual,
    "후행출선시간(분)": follow_time,
    "후행출선속도(t/m)": follow_speed,
    "후행출선량(ton, 실측)": follow_output_manual,
    "일일실시간누적배출량(ton)": total_realtime_output,
    "누적슬래그량(ton)": accumulated_slag
}

# 로그 세션에 추가
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)

# 500건 초과 시 oldest 삭제
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

df_log = pd.DataFrame(st.session_state['log'])
st.dataframe(df_log)

# CSV 다운로드 버튼
csv = df_log.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 누적 리포트 CSV", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

# =================== 안내 ===================
st.markdown("---")
st.markdown("#### 🛠️ BlastTap 10.3 Pro — AI 기반 고로조업 통합 시스템")
st.markdown("- 제작: 신동준 (개발지원: ChatGPT + Streamlit 기반)")
st.markdown("- 업데이트일: 2025-06 최신반영")
st.markdown("- 기능: 일일생산량 예측, 저선관리, 출선추적, 슬래그분리 등 통합 제공")
st.info("💡 모든 조업 정보는 기준일/시간 기반 자동 집계, 실시간 데이터 반영 및 기록 관리.")
st.success("📌 BlastTap 10.3 Pro는 현장 적용/업데이트 버전입니다. 건의/개선점은 GitHub 등으로 제출!")

