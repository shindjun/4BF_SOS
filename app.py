import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 설정 (운영체제별 자동 적용)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="BlastTap 9.9 Pro — 실시간 AI 고로조업지원 통합버전", layout="wide")
st.title("🔥 BlastTap 9.9 Pro — 실시간 AI 고로조업지원 통합버전")

# 세션 상태 초기화 (리포트 누적기록용)
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 설정 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# ✅ 정상조업 입력부
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1 Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90.0)

# ✅ 산소부화량·부화율 입력 (동시 관리)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)
oxygen_ratio_input = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)
oxygen_ratio_auto = (oxygen_enrichment_manual * 60) / (blast_volume * 60 * 0.21)
st.sidebar.write(f"⛽ 산소부화율 자동계산: {oxygen_ratio_auto:.2f} %")

# ✅ 송풍원단위 입력
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ✅ 체류시간·K보정
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# ✅ 정상 장입 누적 Charge 계산
adjusted_elapsed_minutes = elapsed_minutes
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# ✅ 비상조업 입력부
st.sidebar.header("② 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

# 🔧 정상조업 환원효율 계산
size_effect = 1.0
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_ratio_input / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02

# 정상 환원효율 (이론 + K보정)
normal_reduction_eff = 1.0 * size_effect * melting_effect * gas_effect * oxygen_boost * \
    humidity_effect * pressure_boost * blow_pressure_boost * temp_effect * pci_effect * K_factor * 0.9

# 🔧 비상조업 환원효율 계산
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_ratio = (abnormal_oxygen * 60) / (abnormal_blast_volume * 60 * 0.21)
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_ratio / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = 1.0 * size_effect * melting_effect * abnormal_gas_effect * abnormal_oxygen_boost * \
        abnormal_humidity_effect * pressure_boost * blow_pressure_boost * temp_effect * abnormal_pci_effect * K_factor * 0.9

else:
    abnormal_reduction_eff = normal_reduction_eff

# 🔧 체류시간 보정 적용
ore_per_hour = ore_per_charge * charge_rate
fe_hour = ore_per_hour * (tfe_percent / 100)
normal_hourly_production = fe_hour * normal_reduction_eff

# 실제 체류시간 고려
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = normal_hourly_production * (active_minutes / 60)

# 🔧 AI 이론생산량 (누적 전체)
production_ton_ai = normal_hourly_production * (adjusted_elapsed_minutes / 60)
production_ton_ai = max(production_ton_ai, 0)

# 🔧 실측 TAP 기반 실시간 출선 실적 입력
st.sidebar.header("⑤ 실측 출선 실적 입력")

tap_avg_output = st.sidebar.number_input("TAP당 평균 출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)

# 실측 누적 TAP 용선 출선량
tap_total_output = tap_avg_output * completed_taps

# 🔧 이중수지 평균 생산량 계산
avg_total_production = (effective_production_ton + tap_total_output) / 2
avg_total_production = max(avg_total_production, 0)

# 🔧 실시간 수지 편차 (AI - TAP)
production_gap = effective_production_ton - tap_total_output

# 🔧 실시간 선행·후행 출선 실적 입력
st.sidebar.header("⑥ 실시간 선행·후행 출선 실적")

# 선행 출선 시작 시각 및 속도
lead_start_time = st.sidebar.time_input("선행 출선 시작 시각", value=datetime.time(8, 0))
lead_speed = st.sidebar.number_input("선행 출선 속도 (ton/min)", value=5.0)

# 후행 출선 시작 시각 및 속도
follow_start_time = st.sidebar.time_input("후행 출선 시작 시각", value=datetime.time(9, 0))
follow_speed = st.sidebar.number_input("후행 출선 속도 (ton/min)", value=5.0)

# 경과시간 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# 선행·후행 출선량
lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 누적 용선출선량 = TAP출선 + 선행 + 후행
total_tapped_hot_metal = tap_total_output + lead_tapped + follow_tapped

# 누적 슬래그출선량 자동 계산
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# 잔류 저선량 (이중수지 생산량 기준)
residual_molten = avg_total_production - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 저선율 (%)
residual_rate = (residual_molten / avg_total_production) * 100 if avg_total_production > 0 else 0

# 조업상태 경보판
if residual_molten >= 200:
    status = "🔴 저선 위험"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 주의"
else:
    status = "✅ 정상"

# 🔧 AI 추천 비트경 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 🔧 차기 출선간격 추천 로직
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "20~25분"
else:
    next_tap_interval = "30분 이상 권장"

# 🔧 선행 목표출선량 (가변 입력 가능)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1250.0)
lead_remain = max(lead_target - lead_tapped, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 🔧 공취예상시간 = 선행 잔여시간 - 후행경과시간
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# 🔧 평균 출선량 자동계산 (실측 기반)
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# 🔧 결과 출력
st.header("🧮 AI 출선전략 · 공취예상")

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton → 잔여출선시간: {lead_remain_time:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# 📊 실시간 용융물 수지곡선 시각화

st.header("📈 실시간 용융물 수지곡선")

# 시간축 생성 (15분 단위 시뮬레이션)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 이론 누적 생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 보정 시뮬레이션
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

# 실측 누적제한
gen_series = [min(g, avg_total_production) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="AI 누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 용선출선량 (ton)")
plt.plot(time_labels, residual_series, label="잔류 저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지곡선")
plt.grid()
plt.legend()
st.pyplot(plt)

# 📊 BlastTap 9.9 Pro — AI 실시간 종합 리포트

st.header("📊 BlastTap 9.9 Pro — AI 실시간 종합 리포트")

# 생산수지 리포트 출력
st.write(f"AI 이론생산량 (누적): {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 용선출선량: {tap_total_output:.1f} ton")
st.write(f"AI 이중수지 평균 생산량: {avg_total_production:.1f} ton")
st.write(f"송풍원단위 기반 일일예상생산량: {((blast_volume * 1440) + (oxygen_enrichment_manual * 24 / 0.21)) / wind_unit:.1f} ton/day")

# 출선수지 리포트
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {total_tapped_slag:.1f} ton")
st.write(f"잔류 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# 누적 리포트 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI 이론생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측출선량": tap_total_output,
    "이중수지평균": avg_total_production,
    "누적출선량": total_tapped_hot_metal,
    "누적슬래그": total_tapped_slag,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "조업상태": status
}

# 누적 세션기록
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 누적 리포트 테이블 및 다운로드
st.subheader("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.9_Pro_Report.csv", mime='text/csv')
