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
st.set_page_config(page_title="BlastTap 9.8 Pro Edition", layout="wide")
st.title("🔥 BlastTap 9.8 Pro — 실시간 고로 AI 조업지원 엔진")

# 📌 세션 기록 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# ===================== 🔧 정상조업 입력부 =====================
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_gen_kg = st.sidebar.number_input("슬래그 발생량 (kg/thm)", value=280.0)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7155.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=170.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.25)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=4.0)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1190)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
manual_blast_specific_volume = st.sidebar.number_input("송풍원단위 수동입력 (Nm³/ton)", value=1187.0)

slag_ratio = round(1000 / slag_gen_kg, 2)
oxygen_volume_hr = blast_volume * (oxygen_enrichment / 100) * 60

# ===================== 🔧 비상조업 입력부 =====================
st.sidebar.header("② 비상조업 보정입력")

abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 투입량 (kg/thm)", value=pci_rate)
    abnormal_blast_specific_volume = st.sidebar.number_input("비상 송풍원단위 (Nm³/ton)", value=manual_blast_specific_volume)

# ===================== 2부: 이중 AI 수지계산 엔진 =====================

# 경과시간 계산 (실제 시간대 기반)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# 비상조업 시간 분리
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

# 장입속도 → Charge rate
charge_rate = 60 / charging_time_per_charge

# 정상조업 환원효율 계산
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

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_rate_effect * K_factor * 0.9

# 비상조업 환원효율 계산
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * abnormal_pci_effect * iron_rate_effect * K_factor * 0.9
else:
    abnormal_reduction_eff = normal_reduction_eff

# 시간분할 누적Charge
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# Ore 투입량
normal_ore = ore_per_charge * normal_charges
abnormal_ore = ore_per_charge * abnormal_charges
after_ore = ore_per_charge * after_charges

# Fe량 투입
normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 생산량 (이론)
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# 체류시간 보정
adjusted_elapsed = normal_elapsed + abnormal_elapsed + after_elapsed
if adjusted_elapsed > melting_delay:
    active_minutes = adjusted_elapsed - melting_delay
    effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed)
else:
    effective_production_ton = 0

# ===================== 3부: AI 생산량 예측 및 송풍원단위 계산 =====================

# 산소부화량 (정상조업 기준 Nm³/hr)
oxygen_volume_hr = blast_volume * (oxygen_enrichment / 100) * 60

# AI 일일생산량 예측 (정상조업 기준)
normal_total_blast = (blast_volume * 1440 + (oxygen_volume_hr * 24 / 0.21))
daily_production_est_normal = normal_total_blast / manual_blast_specific_volume

# 비상조업 구간 일일생산량 예측 (있을 경우)
if abnormal_active:
    abnormal_oxygen_volume_hr = abnormal_blast_volume * (abnormal_oxygen_enrichment / 100) * 60
    abnormal_total_blast = (abnormal_blast_volume * 1440 + (abnormal_oxygen_volume_hr * 24 / 0.21))
    daily_production_est_abnormal = abnormal_total_blast / abnormal_blast_specific_volume
else:
    daily_production_est_abnormal = daily_production_est_normal

# 이중 시간분할 기반 weighted daily production (실제 AI 생산량 추정)
total_elapsed_ratio = adjusted_elapsed / 1440
weighted_daily_production_est = (
    (normal_elapsed / adjusted_elapsed) * daily_production_est_normal
    + (abnormal_elapsed / adjusted_elapsed) * daily_production_est_abnormal
)

# AI 최종 일일생산량 예측 (안정화 보정)
daily_production_est = weighted_daily_production_est

# 🔧 송풍원단위 자동계산 (AI 이론생산량 기준)
auto_blast_specific_volume = (
    (blast_volume * 1440 + (oxygen_volume_hr * 24 / 0.21)) / max(daily_production_est, 1)
)

# ===================== 4부: 저선량 추적 + 슬래그량 + AI출선전략 =====================

# 실측 TAP 기반 출선량 입력 (실측 기반 직접입력 필요)
st.sidebar.header("④ 실측 출선 실적 입력")
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 이중수지 평균 생산량 (AI+실측 병합)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 수지편차 계산
production_gap = effective_production_ton - production_ton_tap

# 누적 출선량 계산
total_tapped = completed_taps * fixed_avg_tap_output
total_tapped = min(total_tapped, production_ton)

# 저선량 (잔류용융물) 추적
residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)

# 저선율 계산
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 저선경보판 AI
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# 슬래그량 계산 (자동계산 슬래그비율 활용)
avg_hot_metal_per_tap = production_ton / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# 비트경 추천 AI
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 출선간격 추천 AI
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
else:
    next_tap_interval = "즉시 출선"

# ===================== 5부: 출선소요시간 + 용선온도 + 풍압판정 + 공취위험 AI =====================

# 출선소요시간 (Pig 생성 기반 AI 공식)
if pig_gen_rate >= tap_speed:
    estimated_tap_time = 0
else:
    estimated_tap_time = (tap_interval_min * pig_gen_rate / tap_speed) / (1 - (pig_gen_rate / tap_speed))

# 용선온도(Tf) 예측 (PC ton/hr 환산 필요)
PC_ton_hr = pci_rate * daily_production_est / 1000

predicted_tf = (
    (hot_blast_temp * 0.836)
    + ((oxygen_volume_hr / (60 * blast_volume)) * 4973)
    - (hot_blast_temp * 6.033)
    - ((PC_ton_hr * 1000000) / (60 * blast_volume) * 3.01)
    + 1559
)

# 풍압 AI 경보판
if blast_pressure >= 4.2:
    pressure_status = "🔴 한계풍압 위험"
elif blast_pressure >= 4.0:
    pressure_status = "🟠 강화단계"
else:
    pressure_status = "✅ 안정범위"

# 공취 AI 위험스코어 (간이)
risk_score = (residual_molten / 200) + (blast_pressure / 4.2) + (iron_rate / 10)
if risk_score >= 3.0:
    risk_status = "🔴 공취위험"
elif risk_score >= 2.0:
    risk_status = "🟠 공취주의"
else:
    risk_status = "✅ 안정"

# ===================== 6부: 최종 리포트 출력 및 누적 기록 =====================

st.header("📊 BlastTap 9.8 Pro — 실시간 AI 조업 리포트")

# 생산량 결과
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"AI+실측 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량: {daily_production_est:.1f} ton/day")

# 저선/슬래그 결과
st.write(f"잔류 저선량: {residual_molten:.1f} ton")
st.write(f"저선율: {residual_rate:.2f} %")
st.write(f"슬래그비율 (자동): {slag_ratio:.2f}")
st.write(f"슬래그량: {avg_slag_per_tap:.1f} ton")

# 출선전략 추천
st.write(f"수지편차 (AI-TAP): {production_gap:.1f} ton")
st.write(f"조업상태: {status}")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 출선간격: {next_tap_interval}")

# Pig출선시간
st.write(f"예상 출선소요시간: {estimated_tap_time:.1f} 분")

# 용선온도예측
st.write(f"예상 용선온도 Tf: {predicted_tf:.1f} ℃")

# 송풍원단위 결과
st.write(f"송풍원단위 (자동): {auto_blast_specific_volume:.1f} Nm³/ton")
st.write(f"송풍원단위 (수동): {manual_blast_specific_volume:.1f} Nm³/ton")

# AI 공취·풍압 경보
st.write(f"풍압경보: {pressure_status}")
st.write(f"공취위험판정: {risk_status} (스코어: {risk_score:.2f})")

# ===================== 누적기록 저장 =====================
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI이론생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "AI+실측평균": production_ton,
    "일일예상생산량": daily_production_est,
    "잔류저선": residual_molten,
    "저선율": residual_rate,
    "슬래그비율": slag_ratio,
    "슬래그량": avg_slag_per_tap,
    "비트경": tap_diameter,
    "출선간격": next_tap_interval,
    "출선소요시간": estimated_tap_time,
    "용선온도": predicted_tf,
    "송풍원단위(자동)": auto_blast_specific_volume,
    "송풍원단위(수동)": manual_blast_specific_volume,
    "풍압": blast_pressure,
    "풍압경보": pressure_status,
    "공취스코어": risk_score,
    "공취판정": risk_status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# ===================== 누적기록 표출 =====================
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# ===================== CSV 다운로드 =====================
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.8_Pro_Report.csv", mime='text/csv')

# ===================== 간단 시각화 =====================
st.header("📊 생산량 추적 그래프")

plt.figure(figsize=(10, 5))
plt.plot(df['시각'], df['AI이론생산량'], label='AI 이론생산량')
plt.plot(df['시각'], df['AI+실측평균'], label='AI+실측평균')
plt.xticks(rotation=45)
plt.xlabel("시간")
plt.ylabel("생산량 (ton)")
plt.legend()
plt.grid()
st.pyplot(plt)

