import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 📌 한글 폰트 안정화
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 📌 페이지 설정
st.set_page_config(page_title="BlastTap 9.8 Pro Edition", layout="wide")
st.title("🔥 BlastTap 9.8 Pro — 실시간 고로 AI 조업지원 엔진")

# 📌 세션 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (교대시간 07시 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# ===================== ① 정상조업 기본입력 =====================
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_gen_kg = st.sidebar.number_input("슬래그 발생량 (kg/thm)", value=280.0)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7155.0)

# 🔧 산소부화량 ↔ 산소부화율 입력분리
oxygen_volume_hr = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36960.0)
oxygen_enrichment = (oxygen_volume_hr / (blast_volume * 60)) * 100
st.sidebar.write(f"🔎 산소부화율 자동계산: {oxygen_enrichment:.2f} %")

humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=170.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.25)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=4.0)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1190)
measured_temp = st.sidebar.number_input("현재 용선온도 (℃)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
manual_blast_specific_volume = st.sidebar.number_input("송풍원단위 수동입력 (Nm³/ton)", value=1187.0)

# ===================== ② 출선작업 조건 입력 =====================
st.sidebar.header("② 출선작업 조건")

tap_interval_min = st.sidebar.number_input("출선간격 (min)", value=200.0)
tap_speed = st.sidebar.number_input("출선속도 (ton/min)", value=8.0)
pig_gen_rate = st.sidebar.number_input("Pig 생성량 (ton/min)", value=6.5)

# ===================== ③ 현재 실시간 출선량 입력 (선·후행) =====================
st.sidebar.header("③ 현재 실시간 출선량")

lead_tapped = st.sidebar.number_input("선행 현재 출선량 (ton)", value=0.0)
follow_tapped = st.sidebar.number_input("후행 현재 출선량 (ton)", value=0.0)

# ===================== ④ 비상조업 입력 =====================
st.sidebar.header("④ 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume_hr = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume_hr)
    abnormal_oxygen_enrichment = (abnormal_oxygen_volume_hr / (abnormal_blast_volume * 60)) * 100
    st.sidebar.write(f"🔎 비상 산소부화율 자동계산: {abnormal_oxygen_enrichment:.2f} %")
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_blast_specific_volume = st.sidebar.number_input("비상 송풍원단위 (Nm³/ton)", value=manual_blast_specific_volume)
else:
    abnormal_charging_delay = 0
    abnormal_blast_volume = blast_volume
    abnormal_oxygen_enrichment = oxygen_enrichment
    abnormal_humidification = humidification
    abnormal_pci_rate = pci_rate
    abnormal_blast_specific_volume = manual_blast_specific_volume

# ===================== 2부: 시간분할 + AI 환원효율 엔진 =====================

# 🔧 경과시간 계산 (07시 기준)
now = datetime.datetime.now()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# 🔧 비상조업 시간 분할
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
    normal_elapsed = elapsed_minutes
    abnormal_elapsed = 0
    after_elapsed = 0

# 🔧 Charge rate (장입속도)
charge_rate = 60 / charging_time_per_charge

# ===================== 정상조업 환원효율 계산 =====================
size_effect = (20 / 20 + 60 / 60) / 2
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

# ===================== 비상조업 환원효율 계산 =====================
abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
    abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * abnormal_pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

# ===================== 시간분할 누적 Charge 계산 =====================
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# Ore 투입량
normal_ore = ore_per_charge * normal_charges
abnormal_ore = ore_per_charge * abnormal_charges
after_ore = ore_per_charge * after_charges

# Fe 투입량
normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 이론 생산량 계산
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# ===================== 체류시간 보정 =====================
adjusted_elapsed = normal_elapsed + abnormal_elapsed + after_elapsed
if adjusted_elapsed > melting_delay:
    active_minutes = adjusted_elapsed - melting_delay
    effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed)
else:
    effective_production_ton = 0

# ===================== 3부: AI 일일생산량 예측 =====================

# 🔧 안정화된 AI 일일생산량 예측 공식
if (normal_charges + abnormal_charges + after_charges) > 0:
    total_charges = normal_charges + abnormal_charges + after_charges
    daily_production_est = (
        ore_per_charge * total_charges * (tfe_percent / 100) * normal_reduction_eff
    ) * (1440 / adjusted_elapsed)
else:
    daily_production_est = 0

# ===================== 3부: 송풍원단위 자동계산 =====================

# 공식 : (풍량 * 1440 + 산소부화량 * 24 / 0.21) / 생산량

if daily_production_est > 0:
    auto_blast_specific_volume = (blast_volume * 1440 + (oxygen_volume_hr * 24 / 0.21)) / daily_production_est
else:
    auto_blast_specific_volume = manual_blast_specific_volume

# ===================== 4부: 슬래그 생성량 계산 =====================

# 슬래그발생량 (ton 단위)
slag_gen_ton = (effective_production_ton / 1000) * (slag_gen_kg / 7)

# 슬래그비율 자동계산 (슬래그/용선 비)
if effective_production_ton > 0:
    slag_ratio = slag_gen_ton / effective_production_ton
else:
    slag_ratio = slag_gen_kg / 7000

# ===================== 4부: 저선량 및 저선율 추적 =====================

# 누적 실측 출선량 (용선만)
completed_tap_amount = lead_tapped + follow_tapped

# 저선량 계산
residual_molten = effective_production_ton - completed_tap_amount
residual_molten = max(residual_molten, 0)

# 저선율 계산
if effective_production_ton > 0:
    residual_rate = (residual_molten / effective_production_ton) * 100
else:
    residual_rate = 0

# ===================== 5부: AI 출선전략 엔진 =====================

# 🔧 비트경 추천 로직 (저선량 기반)
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 🔧 추천 출선간격 로직
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 7:
    next_tap_interval = "10~15분"
elif residual_rate < 9:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 🔧 예상 출선소요시간 계산 (Pig 생성량 기반 알고리즘)
# 출선소요시간 공식:
# 출선소요시간 = 출선간격 * Pig생성량 / 출선속도 / (1 - (Pig생성량 / 출선속도))

if tap_speed > pig_gen_rate:
    estimated_tap_time = (tap_interval_min * pig_gen_rate / tap_speed) / (1 - (pig_gen_rate / tap_speed))
else:
    estimated_tap_time = 0

# ===================== 6부: 실시간 AI 리포트 =====================

st.header("📊 BlastTap 9.8 Pro — 실시간 AI 조업 리포트")

# 🔧 이론 생산량 & 체류시간 보정
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")

# 🔧 환원효율 결과
st.write(f"정상조업 환원효율: {normal_reduction_eff:.4f}")
st.write(f"비상조업 환원효율: {abnormal_reduction_eff:.4f}")

# 🔧 AI 일일생산량 예측
st.write(f"AI 예측 일일생산량: {daily_production_est:.1f} ton/day")

# 🔧 슬래그량 결과
st.write(f"슬래그 발생량: {slag_gen_ton:.1f} ton")
st.write(f"슬래그비율: {slag_ratio*100:.2f} %")

# 🔧 저선량 결과
st.write(f"잔류 저선량: {residual_molten:.1f} ton")
st.write(f"저선율: {residual_rate:.2f} %")

# 🔧 출선전략 AI 결과
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 출선간격: {next_tap_interval}")
st.write(f"예상 출선소요시간: {estimated_tap_time:.1f} 분")

# 🔧 송풍원단위 결과
st.write(f"송풍원단위 (자동계산): {auto_blast_specific_volume:.1f} Nm³/ton")
st.write(f"송풍원단위 (수동입력): {manual_blast_specific_volume:.1f} Nm³/ton")

# ===================== 7부: 누적 리포트 기록 및 CSV 다운로드 =====================

# 🔧 누적 기록 딕셔너리 생성
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI 이론생산량 (ton)": production_ton_ai,
    "보정 생산량 (ton)": effective_production_ton,
    "AI 일일생산량 (ton/day)": daily_production_est,
    "정상 환원효율": normal_reduction_eff,
    "비상 환원효율": abnormal_reduction_eff,
    "슬래그량 (ton)": slag_gen_ton,
    "슬래그비율 (%)": slag_ratio * 100,
    "잔류 저선량 (ton)": residual_molten,
    "저선율 (%)": residual_rate,
    "추천 비트경": tap_diameter,
    "추천 출선간격": next_tap_interval,
    "예상 출선소요시간 (분)": estimated_tap_time,
    "송풍원단위 (자동)": auto_blast_specific_volume,
    "송풍원단위 (수동)": manual_blast_specific_volume
}

# 🔧 세션에 누적 기록 저장
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 🔧 누적 데이터프레임으로 변환
df = pd.DataFrame(st.session_state['log'])
st.header("📋 누적 AI 리포트")
st.dataframe(df)

# 🔧 CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.8_Report.csv", mime='text/csv')
