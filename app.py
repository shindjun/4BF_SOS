import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 🔧 한글 폰트 안정화
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 📌 페이지 초기설정
st.set_page_config(page_title="BlastTap 9.8 Pro — 실시간 고로 AI 조업지원 엔진", layout="wide")
st.title("🔥 BlastTap 9.8 Pro — 실시간 고로 AI 조업지원 통합판")

# 세션 초기화 (리포트 기록용)
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# ==================== 정상조업 입력부 ====================

st.sidebar.header("① 정상조업 기본입력")

# 장입기본
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 슬래그 비율 (자동으로 계산할 예정이지만 기본값 제공)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 기타 기본조업지표
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍계통 입력 (산소부화량 & 부화율 모두 수동 입력 가능)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%) (수동입력)", value=6.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)

humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)

# 송풍원단위 (수동입력)
blast_unit = st.sidebar.number_input("송풍원단위 (Nm3/ton)", value=1189.0)

# 예상 일일생산량 계산 (송풍원단위 기반 자동계산)
expected_daily_production = (blast_volume * 1440 + oxygen_volume * 24 / 0.21) / blast_unit

# ==================== 실시간 출선 입력 ====================

st.sidebar.header("② 현재 실시간 출선량")

# 출선간격 (계획기준)
tap_interval_plan = st.sidebar.number_input("출선간격 (계획) (분)", value=10.0)

# 선행 출선 정보 입력
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=7.0)

# 후행 출선 정보 입력
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=3.0)

# 현재까지 경과시간 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# 누적 출선량 계산 (용선)
lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 슬래그 자동계산 (용선:슬래그 비율 활용)
lead_slag = lead_tapped / slag_ratio
follow_slag = follow_tapped / slag_ratio

# 결과 표시
st.write(f"선행 소요시간: {lead_elapsed:.1f}분 ➔ 용선출선: {lead_tapped:.1f} ton")
st.write(f"후행 소요시간: {follow_elapsed:.1f}분 ➔ 용선출선: {follow_tapped:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {lead_slag + follow_slag:.1f} ton")

# ==================== 비상조업 입력부 ====================

st.sidebar.header("③ 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment)
    abnormal_blast_unit = st.sidebar.number_input("비상 송풍원단위 (Nm3/ton)", value=blast_unit)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)

else:
    abnormal_charging_delay = 0

# ==================== 실측 TAP 생산량 입력부 ====================

st.sidebar.header("④ 실측 출선 실적 입력")

# 평균 TAP당 용선 출선량 (이제 유동입력으로 변경 반영)
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균 출선량 (ton)", value=1250.0, step=10.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6, step=1)
production_ton_tap = completed_taps * fixed_avg_tap_output

# ==================== AI 생산량 수지통합 ====================

# 🔧 정상조업 환원효율 계산
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

# 🔧 체류시간 보정 (실질 용융물 계산)
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

normal_ore = ore_per_charge * charge_rate * (adjusted_elapsed_minutes / 60)
normal_fe = normal_ore * (tfe_percent / 100)
production_ton_ai = normal_fe * normal_reduction_eff
effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 🔧 이중수지 평균
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 🔧 일일예상생산량 (송풍원단위 기반)
if blast_unit > 0:
    daily_production_est_unit = (blast_volume * 1440 + oxygen_volume * 24 / 0.21) / blast_unit
else:
    daily_production_est_unit = 0

# ==================== 실시간 출선진행 및 저선량 수지추적 ====================

# 🔧 실시간 선행/후행 출선 진행상황 입력
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

now = datetime.datetime.now()

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped_now = lead_speed * lead_elapsed
follow_tapped_now = follow_speed * follow_elapsed

# 🔧 누적 용선출선량 (실측 TAP + 실시간 선행/후행 누적 포함)
total_hot_metal = production_ton_tap + lead_tapped_now + follow_tapped_now

# 🔧 누적 슬래그 출선량 자동계산
slag_total = total_hot_metal / slag_ratio

# 🔧 저선량 계산
residual_molten = production_ton - total_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 🔧 저선경보판 상태 판단
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ==================== 공취예상시간 및 AI 잔류출선 예측 ====================

st.header("📊 실시간 공취예상 및 출선AI")

# 🔧 선행 출선 잔여량 및 잔여시간 계산
lead_remain = max(fixed_avg_tap_output - lead_tapped_now, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 🔧 후행 출선 잔여량 및 잔여시간 계산
follow_remain = max(fixed_avg_tap_output - follow_tapped_now, 0)
follow_remain_time = follow_remain / follow_speed if follow_speed > 0 else 0

# 🔧 공취예상시간 계산 (선행 잔여시간 - 후행 경과시간)
gap_minutes = max(lead_remain_time - follow_elapsed, 0)

# 🔧 출선패턴 AI 추천 로직 (동시출선 예상)
if lead_remain_time <= 0:
    simultaneous_tap_predict = "선행 출선 완료"
elif follow_elapsed == 0:
    simultaneous_tap_predict = "아직 후행 미시작"
elif gap_minutes <= 0:
    simultaneous_tap_predict = "동시출선 중 (후행 진입)"
else:
    simultaneous_tap_predict = f"예상 동시출선까지 {gap_minutes:.1f}분 남음"

# 🔧 종합 출선정보 리포트
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton ➔ 잔여시간: {lead_remain_time:.1f}분")
st.write(f"후행 잔여출선량: {follow_remain:.1f} ton ➔ 잔여시간: {follow_remain_time:.1f}분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f}분")
st.write(f"동시출선AI 예측상황: {simultaneous_tap_predict}")

# ==================== 9부: 종합 리포트 및 실시간 수지곡선 ====================

st.header("📊 AI 실시간 통합 수지 리포트")

# 🔧 AI 생산수지 결과 출력
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량 (송풍원단위): {daily_production_est_unit:.1f} ton/day")

# 🔧 누적 용선/슬래그 수지 출력
st.write(f"누적 용선출선량: {total_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동): {slag_total:.1f} ton")

# 🔧 저선 수지 결과
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# 🔧 용선온도 예측결과 출력
st.write(f"예상 용선온도 (Tf): {measured_temp:.1f} °C")  # ※ 현재 실측값 우선반영

# 🔧 실시간 수지 시각화
st.header("📈 실시간 용융물 수지 곡선")

# 시간축 생성 (15분 단위 시뮬레이션)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 누적 생산량 (AI 이론계산 → 체류시간 보정 포함)
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

# 최대생산량 제한
gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_hot_metal] * len(time_labels)
residual_series = [max(g - total_hot_metal, 0) for g in gen_series]

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 용선출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 추적")
plt.legend()
plt.grid()
st.pyplot(plt)
