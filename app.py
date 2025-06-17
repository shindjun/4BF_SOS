import streamlit as st
import pandas as pd
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
st.set_page_config(page_title="BlastTap 9.8 Pro — 실시간 고로 AI조업엔진", layout="wide")
st.title("🔥 BlastTap 9.8 Pro — 실시간 고로 AI조업엔진")

# 세션 초기화 (리포트 기록용)
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# -----------------------------------
# ① 정상조업 기본입력
# -----------------------------------
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=6.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
blast_unit_normal = st.sidebar.number_input("송풍원단위 (정상 Nm³/t)", value=1189.0)

# -----------------------------------
# ② 비상조업 보정입력
# -----------------------------------
st.sidebar.header("② 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 (분)", value=0)

    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    blast_unit_abnormal = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=blast_unit_normal)

# -----------------------------------
# 시간 분할 (정상, 비상, 이후)
# -----------------------------------
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

# 장입지연 보정
abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0) if abnormal_active else 0
adjusted_elapsed_minutes = max(normal_elapsed + abnormal_adjusted_elapsed + after_elapsed, 60)

# -----------------------------------
# ③ AI 이론생산량 및 환원효율 계산
# -----------------------------------

# ✅ 정상조업 환원효율 계산
size_effect = (20 / 20 + 60 / 60) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9

# ✅ 비상조업 환원효율 계산
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor * 0.9
else:
    abnormal_reduction_eff = normal_reduction_eff

# -----------------------------------
# 누적 Charge 수 계산
# -----------------------------------
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_adjusted_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# -----------------------------------
# 구간별 Ore 투입량 → Fe → 환원생산량
# -----------------------------------
normal_fe = ore_per_charge * normal_charges * (tfe_percent / 100)
abnormal_fe = ore_per_charge * abnormal_charges * (tfe_percent / 100)
after_fe = ore_per_charge * after_charges * (tfe_percent / 100)

normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

# AI 이론 누적 생산량
production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# -----------------------------------
# 체류시간 보정 생산량
# -----------------------------------
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
    effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes)
else:
    effective_production_ton = 0

# -----------------------------------
# ④ AI 일일예상생산량 (송풍원단위 기반)
# -----------------------------------

# ✅ 정상/비상 시간가중 평균 송풍원단위 적용
if abnormal_active:
    normal_daily_production = (blast_volume * 1440 + oxygen_volume * 24 / 0.21) / blast_unit_normal
    abnormal_daily_production = (abnormal_blast_volume * 1440 + abnormal_oxygen_volume * 24 / 0.21) / blast_unit_abnormal
    total_minutes = normal_elapsed + abnormal_elapsed
    daily_production_est = (normal_daily_production * normal_elapsed + abnormal_daily_production * abnormal_elapsed) / total_minutes if total_minutes > 0 else 0
else:
    daily_production_est = (blast_volume * 1440 + oxygen_volume * 24 / 0.21) / blast_unit_normal

# -----------------------------------
# ⑤ 용선온도 (Tf) 안정화 예측
# -----------------------------------

# 🔧 미분탄 kg/thm → ton/hr 변환
pci_ton_per_hr = pci_rate * daily_production_est / 1000

# 🔧 안정화 최종 공식 (음수 방지형 튜닝)
if blast_volume > 0:
    tf_predict = (hot_blast_temp * 0.836) \
        + (oxygen_volume / (60 * blast_volume) * 4973) \
        - (hot_blast_temp * 3.5) \
        - (pci_ton_per_hr / (60 * blast_volume) * 1.8) \
        + 1559
else:
    tf_predict = 0

# -----------------------------------
# ⑤ 실시간 출선작업 조건 및 실측출선량 병합
# -----------------------------------

st.sidebar.header("③ 실시간 출선 작업조건")

# ✅ 실시간 선행·후행 실측 누적 용선출선량 입력
lead_tapped_real = st.sidebar.number_input("선행 현재까지 용선출선량 (ton)", value=0.0)
follow_tapped_real = st.sidebar.number_input("후행 현재까지 용선출선량 (ton)", value=0.0)

# ✅ 종료된 TAP 출선 실적 입력
st.sidebar.header("④ 실측 TAP 출선 실적")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=0)
daily_hot_metal_tap = fixed_avg_tap_output * completed_taps

# ✅ 최종 누적 용선출선량
total_tapped_hot_metal = daily_hot_metal_tap + lead_tapped_real + follow_tapped_real

# ✅ 슬래그 자동계산 (슬래그 비율 기반)
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# ✅ 실측 이중수지 평균 생산량 (AI + 실측 병합)
production_ton = (effective_production_ton + daily_hot_metal_tap) / 2
production_ton = max(production_ton, 0)

# ✅ 실시간 저선량 추적
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# -----------------------------------
# ⑥ AI 출선전략 추천 엔진
# -----------------------------------

# ✅ 평균 TAP당 용선·슬래그출선량 계산
avg_hot_metal_per_tap = production_ton / max(completed_taps, 1) if completed_taps > 0 else 0
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio if slag_ratio > 0 else 0

# ✅ AI 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# ✅ 차기 출선간격 추천
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 10:
    next_tap_interval = "20~30분"
else:
    next_tap_interval = "출선조정 권장"

# -----------------------------------
# ⑦ 실시간 공취예상시간 예측 (선행/후행 격차)
# -----------------------------------

st.sidebar.header("⑤ 실시간 공취예측")

# 실시간 선행·후행 출선 시각 입력
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1250.0)

# 시간 경과 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)
lead_elapsed_min = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed_min = max((now - follow_start_dt).total_seconds() / 60, 0)

# 선행 잔여출선량
lead_remain = max(lead_target - (lead_speed * lead_elapsed_min), 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 공취 예상시간
gap_minutes = max(lead_remain_time - follow_elapsed_min, 0)

# -----------------------------------
# ⑧ 실시간 종합 리포트 출력
# -----------------------------------

st.header("📊 AI 실시간 수지 리포트")

st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"일일 실시간 용선배출량 (TAP): {daily_hot_metal_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량 (송풍원단위): {daily_production_est:.1f} ton/day")
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동): {total_tapped_slag:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"예상 용선온도 (Tf): {tf_predict:.1f} °C")

st.header("📊 AI 출선전략 추천")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그량: {avg_slag_per_tap:.1f} ton")

st.header("📊 공취예상시간")
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton → 잔여시간: {lead_remain_time:.1f} 분")
st.write(f"후행 출선 경과시간: {follow_elapsed_min:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# -----------------------------------
# ⑨ 실시간 용융물 수지 시각화 엔진
# -----------------------------------

st.header("📈 실시간 용융물 수지곡선 시각화")

# 시간축 생성 (15분 단위 시뮬레이션)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 누적 생산량 (AI 이론계산 → 체류시간 보정 포함)
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 이후부터 용융물 발생 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

# 초과 누적 생산량 제한 (현재 생산량까지 제한)
gen_series = [min(g, production_ton) for g in gen_series]

# 출선량 → 누적 출선량은 현재까지 constant 유지
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선량 → 생산량 - 출선량
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화 그래프 그리기
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
