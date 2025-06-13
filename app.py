import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib

# 폰트 안정화 (Nanum Gothic → Malgun Gothic fallback)
import platform
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(page_title="BlastTap 8.0 AI 복합조업 자동보정판", layout="wide")
st.title("🔥 BlastTap 8.0 — AI 복합조업 자동보정판")

# 세션 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 설정 (07시 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(elapsed_minutes, 0)
elapsed_minutes = min(elapsed_minutes, 1440)

# ====================== 입력 시작 ======================

# 지연시간 입력
st.sidebar.header("⚠ 장입지연 및 설비지연 입력")
charging_delay = st.sidebar.number_input("장입지연 누적시간 (분)", value=0)
adjusted_elapsed_minutes = elapsed_minutes - charging_delay
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 0)

# 정상조업 입력
st.sidebar.header("① 정상조업 조건 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=164.9)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.8)
ore_coke_ratio = st.sidebar.number_input("Ore/Coke 비율 (-)", value=4.89)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("환원율 (기본)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
furnace_volume = st.sidebar.number_input("고로 유효내용적 (m³)", value=4497)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7960.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
oxygen_blow = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36941.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.2)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1194)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# 정상 장입속도
st.sidebar.header("② 정상 장입속도")
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 비정상조업 입력
st.sidebar.header("③ 비정상조업 조건 입력")
abnormal_start_time = st.sidebar.time_input("비정상 시작시각", value=datetime.time(10, 0))
abnormal_end_time = st.sidebar.time_input("비정상 종료시각", value=datetime.time(13, 0))
abnormal_blast_volume = st.sidebar.number_input("비정상 송풍량 (Nm³/min)", value=6000.0)
abnormal_oxygen = st.sidebar.number_input("비정상 산소부화율 (%)", value=1.5)

# ======= 정상조업 환원효율 계산 =======

# 정상 수지효율 보정
size_effect = (20 / 20 + 60 / 60) / 2  # ore_size=20, coke_size=60 (생략)
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_rate_effect = iron_rate / 9.0
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

# ======= 비정상조업 환원효율 계산 =======

# 비정상구간 수지효율 보정 (풍량, 산소만 수정)
abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
abnormal_oxygen_boost = 1 + (abnormal_oxygen / 10)

abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
    abnormal_oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

# ======= 경과시간 구간 분리 =======

abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, adjusted_elapsed_minutes)
abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, adjusted_elapsed_minutes - normal_elapsed), 0)
after_elapsed = max(adjusted_elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)

# ======= 이론생산량 산출 =======

normal_production = normal_elapsed * iron_rate * normal_reduction_eff / 60
abnormal_production = abnormal_elapsed * iron_rate * abnormal_reduction_eff / 60
after_production = after_elapsed * iron_rate * normal_reduction_eff / 60

production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# ======= 실측 TAP 기반 누적 생산량 =======

st.sidebar.header("④ 실측 출선 데이터 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# ======= 이중수지 평균 산출 =======

production_ton = (production_ton_ai + production_ton_tap) / 2

# ======= 수지편차 분석 =======

production_gap = production_ton_ai - production_ton_tap

# ======= 누적 출선량 계산 =======

lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.8)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.8)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)

# 출선 경과시간
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 누적 출선량
completed_tap_amount = completed_taps * fixed_avg_tap_output
total_tapped = completed_tap_amount + lead_tapped + follow_tapped
total_tapped = min(total_tapped, production_ton)

# ======= 저선량 계산 =======

residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# ======= 공취 예상 =======

lead_close_time = lead_start_dt + datetime.timedelta(minutes=(lead_target / lead_speed))
gap_minutes = max((lead_close_time - follow_start_dt).total_seconds() / 60, 0)

# ======= 조업상태 경보 =======

if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ======= 실시간 결과 출력 =======

st.header("📊 AI 수지분석 결과 (복합조업 보정)")

st.write(f"AI 장입수지 기반 생산량: {production_ton_ai:.1f} ton")
st.write(f"TAP 실측 기반 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"누적 출선량: {total_tapped:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton")
st.write(f"저선율: {residual_rate:.2f}%")
st.write(f"수지편차 (AI-TAP): {production_gap:.1f} ton")
st.write(f"조업상태: {status}")
st.write(f"공취 예상시간: {gap_minutes:.1f} 분")
st.write(f"선행폐쇄 예상시각: {lead_close_time.strftime('%H:%M')}")

# ======= 시각화 그래프 =======

st.header("📊 실시간 용융물 수지추적")

time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * normal_reduction_eff
    for t in time_labels
]
gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped] * len(time_labels)
residual_series = [max(g - total_tapped, 0) for g in gen_series]

plt.figure(figsize=(8, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지추적")
plt.ylim(0, production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# ======= 누적 리포트 로그 기록 =======

record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "실측생산량": production_ton_tap,
    "이중수지": production_ton,
    "출선량": total_tapped,
    "저선량": residual_molten,
    "수지편차": production_gap,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# ======= 누적 리포트 및 다운로드 =======

st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트_8_0.csv", mime='text/csv')