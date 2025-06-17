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
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=170.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.25)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=4.0)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1190)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)

# 슬래그비율 자동계산
slag_ratio = round(1000 / slag_gen_kg, 2)

# ====================== 저선 체적기반 입력부 ======================
st.sidebar.header("② 저선 체적기반 입력")

hearth_area = st.sidebar.number_input("노저 단면적 (m²)", value=90.0)
porosity = st.sidebar.number_input("노저 공극률", value=0.3)
slag_volume_ratio = st.sidebar.number_input("슬래그 볼륨비율 (%)", value=30.0)

# ====================== Pig 기반 출선시간 입력부 ======================
st.sidebar.header("③ Pig 기반 출선시간 예측")

pig_gen_rate = st.sidebar.number_input("Pig 생성량 (ton/min)", value=6.5)
tap_interval_min = st.sidebar.number_input("출선간격 (분)", value=140)
tap_speed = st.sidebar.number_input("출선속도 (ton/min)", value=5.0)

# ====================== 실시간 장입진도 입력부 ======================
st.sidebar.header("④ 실시간 장입진도 입력")

total_charges_plan = st.sidebar.number_input("계획 Charge 수 (EA)", value=125)
current_charges = st.sidebar.number_input("현재 진행된 Charge 수 (EA)", value=65)

# 🔧 누적 장입시간 계산
elapsed_minutes = current_charges * charging_time_per_charge
total_planned_minutes = total_charges_plan * charging_time_per_charge
remaining_minutes = total_planned_minutes - elapsed_minutes

# ====================== 송풍원단위 이중입력부 ======================
st.sidebar.header("⑤ 송풍원단위 입력")

manual_blast_specific_volume = st.sidebar.number_input("송풍원단위 수동입력 (Nm³/ton)", value=1200.0)

# ====================== 2부: AI 수지계산 본엔진 ======================

# 시간당 장입속도 (Charge/hour)
charge_rate = 60 / charging_time_per_charge

# 누적 Charge 수
elapsed_charges = charge_rate * (elapsed_minutes / 60)

# 누적 Ore 투입량 (ton)
total_ore = ore_per_charge * elapsed_charges

# 환산 Fe 투입량
total_fe = total_ore * (tfe_percent / 100)

# AI 이론 환원효율 보정 (AI 복합보정효율 간소화)
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

ai_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_rate_effect * K_factor * 0.9

# AI 이론생산량 (누적 ton)
production_ton_ai = total_fe * ai_reduction_eff
production_ton_ai = max(production_ton_ai, 0)

# 체류시간 보정 생산량
if elapsed_minutes > melting_delay:
    active_minutes = elapsed_minutes - melting_delay
    effective_production_ton = production_ton_ai * (active_minutes / elapsed_minutes)
else:
    effective_production_ton = 0

# AI 일일예상 생산량 (ton/day)
if elapsed_charges > 0:
    daily_production_est = (ore_per_charge * elapsed_charges * (tfe_percent/100) * ai_reduction_eff) * (1440 / elapsed_minutes)
else:
    daily_production_est = 0

# 송풍원단위 자동계산 (ton/day 기반 자동 보정)
oxygen_volume = blast_volume * (oxygen_enrichment / 100)
oxygen_corrected = oxygen_volume * 60  # Nm³/hr

auto_blast_specific_volume = (
    (blast_volume * 1440 + (oxygen_corrected * 24 / 0.21)) / max(daily_production_est, 1)
)

# ====================== 3부: 저선량 추적 및 출선전략 ======================

# 실측 TAP 기반 출선량 입력 (실시간 수동입력 가능: AI+실측 병합용)
st.sidebar.header("⑥ 실측 TAP 출선실적 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 이중수지 평균 생산량 (AI+실측 병합)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 수지편차 계산 (AI-TAP 수지차이)
production_gap = effective_production_ton - production_ton_tap

# 누적 출선량 (완료된 TAP 기준)
completed_tap_amount = completed_taps * fixed_avg_tap_output

# 잔류용융물 (저선량)
residual_molten = production_ton - completed_tap_amount
residual_molten = max(residual_molten, 0)

# 저선율 (%)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 저선경보판 AI 판정
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# 비트경 추천 로직 (저선량 기반 AI판단)
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 출선간격 추천 로직 (저선율 기반 AI판단)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 7:
    next_tap_interval = "10~15분"
elif residual_rate < 9:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# ====================== 동시출선 예상시간 계산부 ======================

st.sidebar.header("⑦ 동시출선 전략입력")

lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
lead_tapped = st.sidebar.number_input("선행 이미출선량 (ton)", value=0.0)

follow_target = st.sidebar.number_input("후행 목표출선량 (ton)", value=1100.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)

# 선행 잔여출선시간
lead_remain_time = (lead_target - lead_tapped) / lead_speed if lead_speed > 0 else 0

# 후행 전체출선시간
follow_total_time = follow_target / follow_speed if follow_speed > 0 else 0

# 동시출선 예상시간 (실전적용형 공식)
simultaneous_cast_time = min(lead_remain_time, follow_total_time)

# ====================== 4부: 출선소요시간예측, 용선온도예측, 공취위험 ======================

# 🔧 출선소요시간 AI 예측 (Pig 생성식 기반)
if pig_gen_rate >= tap_speed:
    estimated_tap_time = 0
else:
    estimated_tap_time = tap_interval_min * pig_gen_rate / tap_speed / (1 - (pig_gen_rate / tap_speed))

# 🔧 용선온도(Tf) 예측 (실전적용 AI공식, PC 기준은 ton/hr 로 변환해야함)
PC_ton_hr = pci_rate * daily_production_est / 1000  # 대략적 ton/hr 환산

predicted_tf = (
    (hot_blast_temp * 0.836)
    + (oxygen_volume * 60 / (60 * blast_volume) * 4973)
    - (hot_blast_temp * 6.033)
    - ((PC_ton_hr * 1000000) / (60 * blast_volume) * 3.01)
    + 1559
)

# 🔧 풍압경고판 AI
if blast_pressure >= 4.2:
    pressure_status = "🔴 위험 한계풍압"
elif blast_pressure >= 4.0:
    pressure_status = "🟠 강화단계 풍압"
else:
    pressure_status = "✅ 정상범위"

# 🔧 공취위험 스코어 AI (간이판정 예제)
risk_score = (residual_molten / 200) + (blast_pressure / 4.2) + (iron_rate / 10)
if risk_score >= 3.0:
    risk_status = "🔴 공취위험"
elif risk_score >= 2.0:
    risk_status = "🟠 공취주의"
else:
    risk_status = "✅ 안정"

# ====================== 5부: AI 종합 리포트 출력 ======================

st.header("📊 BlastTap 9.8 Pro — 실시간 AI 조업 리포트")

# 생산량 관련 출력
st.write(f"AI 이론생산량 (ton): {production_ton_ai:.1f}")
st.write(f"체류시간 보정 생산량 (ton): {effective_production_ton:.1f}")
st.write(f"실측 TAP 생산량 (ton): {production_ton_tap:.1f}")
st.write(f"AI+실측 평균 생산량 (ton): {production_ton:.1f}")
st.write(f"AI 예측 일일생산량 (ton/day): {daily_production_est:.1f}")

# 저선 및 수지편차 출력
st.write(f"잔류 저선량 (ton): {residual_molten:.1f}")
st.write(f"저선율 (%): {residual_rate:.2f}%")
st.write(f"수지편차 (AI-TAP): {production_gap:.1f} ton")
st.write(f"조업상태: {status}")

# 슬래그 및 비율 출력
st.write(f"슬래그비율 (자동계산): {slag_ratio:.2f} (용선:슬래그)")
avg_slag_per_tap = fixed_avg_tap_output / slag_ratio
st.write(f"평균 슬래그량 (ton): {avg_slag_per_tap:.1f}")

# 비트경 추천
st.write(f"AI 추천 비트경: Ø{tap_diameter}")
st.write(f"AI 추천 출선간격: {next_tap_interval}")

# 동시출선 예상시간 출력
st.write(f"동시출선 예상시간 (분): {simultaneous_cast_time:.1f}")

# 출선소요시간예측 (Pig 기반)
st.write(f"예상 출선소요시간 (분): {estimated_tap_time:.1f}")

# 용선온도예측 출력
st.write(f"예상 용선온도 Tf (℃): {predicted_tf:.1f}")

# 송풍원단위 출력 (자동 및 수동비교)
st.write(f"송풍원단위 (자동계산): {auto_blast_specific_volume:.1f} Nm³/ton")
st.write(f"송풍원단위 (수동입력): {manual_blast_specific_volume:.1f} Nm³/ton")

# 풍압경고
st.write(f"현재 풍압: {blast_pressure} kg/cm² — {pressure_status}")

# 공취위험 AI판정
st.write(f"공취위험판정: {risk_status} (스코어: {risk_score:.2f})")

# ====================== 6부: 누적기록 + 시각화 + CSV저장 ======================

# 🔧 누적 리포트 기록 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI 이론생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "AI+실측평균": production_ton,
    "잔류저선": residual_molten,
    "저선율": residual_rate,
    "수지편차": production_gap,
    "예상일일생산량": daily_production_est,
    "슬래그비율": slag_ratio,
    "슬래그량": avg_slag_per_tap,
    "비트경": tap_diameter,
    "출선간격추천": next_tap_interval,
    "동시출선예상시간": simultaneous_cast_time,
    "출선소요시간": estimated_tap_time,
    "용선온도(Tf)": predicted_tf,
    "송풍원단위(자동)": auto_blast_specific_volume,
    "송풍원단위(수동)": manual_blast_specific_volume,
    "풍압": blast_pressure,
    "풍압상태": pressure_status,
    "공취위험스코어": risk_score,
    "공취위험상태": risk_status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 🔧 누적 리포트 표출
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# 🔧 CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.8_Report.csv", mime='text/csv')

# 🔧 간단한 생산량 시각화 예제 (선택적 시각화)
st.header("📊 생산량 시각화 추적")

plt.figure(figsize=(10, 5))
plt.plot(df['시각'], df['AI 이론생산량'], label='AI이론생산량')
plt.plot(df['시각'], df['실측생산량'], label='실측생산량')
plt.plot(df['시각'], df['AI+실측평균'], label='평균생산량')
plt.xticks(rotation=45)
plt.xlabel("시간")
plt.ylabel("ton")
plt.legend()
plt.grid()
st.pyplot(plt)
