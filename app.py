import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 폰트 안정화
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지설정
st.set_page_config(page_title="BlastTap 9.2 Stable", layout="wide")
st.title("🔥 BlastTap 9.2 — Stable Deployment Version")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 설정 (07:00 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60

# 경과시간 보호 (최소 60분)
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# 정상조업 입력
st.sidebar.header("① Normal Operation Input")
charging_delay = st.sidebar.number_input("Charging Delay (min)", value=0)
adjusted_elapsed_minutes = max(elapsed_minutes - charging_delay, 60)

ore_per_charge = st.sidebar.number_input("Ore per Charge (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke per Charge (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("Slag Ratio", value=2.25)
reduction_efficiency = st.sidebar.number_input("Reduction Efficiency", value=1.0)
melting_capacity = st.sidebar.number_input("Melting Capacity (°CKN)", value=2800)

blast_volume = st.sidebar.number_input("Blast Volume (Nm³/min)", value=7960.0)
oxygen_enrichment = st.sidebar.number_input("Oxygen Enrichment (%)", value=3.0)
humidification = st.sidebar.number_input("Humidity (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("PCI Rate (kg/thm)", value=170)
top_pressure = st.sidebar.number_input("Top Pressure (kg/cm²)", value=2.2)
blast_pressure = st.sidebar.number_input("Blast Pressure (kg/cm²)", value=3.9)
iron_rate = st.sidebar.number_input("Iron Rate (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("Hot Blast Temp (°C)", value=1194)
measured_temp = st.sidebar.number_input("Measured Temp (°C)", value=1515.0)
K_factor = st.sidebar.number_input("K Factor", value=1.0)

charging_time_per_charge = st.sidebar.number_input("Charging Time per Charge (min)", value=11.0)
charge_rate = 60 / charging_time_per_charge
melting_delay = st.sidebar.number_input("Melting Delay (min)", value=240)

# 비상조업 입력
st.sidebar.header("② Emergency Mode Input")
abnormal_active = st.sidebar.checkbox("Activate Emergency Mode", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("Emergency Start Time", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("Emergency End Time", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("Emergency Charging Delay (min)", value=charging_delay)
    abnormal_blast_volume = st.sidebar.number_input("Emergency Blast Volume (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("Emergency Oxygen (%)", value=oxygen_enrichment)
    abnormal_humidification = st.sidebar.number_input("Emergency Humidity (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("Emergency PCI (kg/thm)", value=pci_rate)

# ================== [2부: AI 생산량 계산 엔진] ===================

# 정상조업 환원효율 계산
size_effect = 1  # 입도 고정
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

# 비상조업 환원효율 계산
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * abnormal_pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9
else:
    abnormal_reduction_eff = normal_reduction_eff

# 시간분할 계산
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, adjusted_elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, adjusted_elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(adjusted_elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
    normal_elapsed = adjusted_elapsed_minutes
    abnormal_elapsed = 0
    after_elapsed = 0

# 누적 Charge 수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# 구간별 생산량 계산
normal_ore = ore_per_charge * normal_charges
abnormal_ore = ore_per_charge * abnormal_charges
after_ore = ore_per_charge * after_charges

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# 체류시간 보정
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 누적 Charge 기반 일일생산량 추정 (최종 핵심 안정식)
if elapsed_charges > 0:
    daily_production_est = (ore_per_charge * elapsed_charges * (tfe_percent/100) * normal_reduction_eff) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est = 0

# ================== [3부: 실측 출선량 병합 및 저선량 추적] ===================

# 실측 TAP 기반 출선량 입력
st.sidebar.header("③ Tapping Actual Input")

fixed_avg_tap_output = st.sidebar.number_input("Avg Output per TAP (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("Completed TAP Count (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 이중수지 평균 생산량 (AI + 실측 병합)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 수지편차 계산
production_gap = effective_production_ton - production_ton_tap

# 실시간 출선 진행상황 입력
lead_start_time = st.sidebar.time_input("Lead Tapping Start Time", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("Follow Tapping Start Time", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("Lead Tapping Speed (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("Follow Tapping Speed (ton/min)", value=5.0)
lead_target = st.sidebar.number_input("Lead Tapping Target (ton)", value=1100.0)

# 시간기준 출선 경과계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 누적 출선량 계산
completed_tap_amount = completed_taps * fixed_avg_tap_output
total_tapped = completed_tap_amount + lead_tapped + follow_tapped
total_tapped = min(total_tapped, production_ton)

# 저선량 (잔류용융물) 추적
residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)

# 저선율 계산
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 공취 예상시간 계산
lead_close_time = lead_start_dt + datetime.timedelta(minutes=(lead_target / lead_speed))
gap_minutes = max((lead_close_time - follow_start_dt).total_seconds() / 60, 0)

# 저선경보판
if residual_molten >= 200:
    status = "🔴 High Residual (Critical)"
elif residual_molten >= 150:
    status = "🟠 Residual High"
elif residual_molten >= 100:
    status = "🟡 Monitor Residual"
else:
    status = "✅ Stable"

# ================== [4부: AI 출선전략 추천 엔진] ===================

# 평균 Tap당 출선/슬래그량 계산
avg_hot_metal_per_tap = production_ton / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# AI 비트경 추천
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# AI 출선간격 추천
if residual_rate < 5:
    next_tap_interval = "15~20 min"
elif residual_rate < 7:
    next_tap_interval = "10~15 min"
elif residual_rate < 9:
    next_tap_interval = "5~10 min"
else:
    next_tap_interval = "Immediate (0~5 min)"

# AI 리포트 출력
st.header("📊 AI Production Balance Report")

st.write(f"AI Calculated Production (raw): {production_ton_ai:.1f} ton")
st.write(f"Effective Production (after melting delay): {effective_production_ton:.1f} ton")
st.write(f"Actual Tapping Production: {production_ton_tap:.1f} ton")
st.write(f"Final Blended Production: {production_ton:.1f} ton")
st.write(f"Estimated Daily Production: {daily_production_est:.1f} ton/day")
st.write(f"Total Tapped: {total_tapped:.1f} ton")
st.write(f"Residual Molten: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"Production Gap (AI - Tapping): {production_gap:.1f} ton")
st.write(f"Expected Closing Gap Time: {gap_minutes:.1f} min")
st.write(f"Lead Close Target Time: {lead_close_time.strftime('%H:%M')}")
st.write(f"Operation Status: {status}")
st.write(f"Recommended Tap Diameter: Ø{tap_diameter}")
st.write(f"Next Tap Interval Recommendation: {next_tap_interval}")
st.write(f"Avg Tapping per TAP: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"Avg Slag per TAP: {avg_slag_per_tap:.1f} ton")

# ================== [5부: 실시간 시각화 및 누적 리포트] ===================

# 실시간 수지 시각화
st.header("📊 Real-time Production Balance Chart")

# 시간축 생성 (15분 간격)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 정상환원효율 기준 누적생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped] * len(time_labels)
residual_series = [max(g - total_tapped, 0) for g in gen_series]

plt.figure(figsize=(8, 5))
plt.plot(time_labels, gen_series, label="Prod (ton)")
plt.plot(time_labels, tap_series, label="Tapping (ton)")
plt.plot(time_labels, residual_series, label="Residual (ton)")
plt.xlabel("Elapsed Time (min)")
plt.ylabel("ton")
plt.title("Molten Balance Tracker")
plt.ylim(0, production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# 누적 리포트 기록
record = {
    "Time": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI Production (raw)": production_ton_ai,
    "Effective Production": effective_production_ton,
    "Tapping Production": production_ton_tap,
    "Final Production": production_ton,
    "Total Tapped": total_tapped,
    "Residual Molten": residual_molten,
    "Residual Rate": residual_rate,
    "Daily Estimate": daily_production_est,
    "Status": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 누적 리포트 테이블 및 CSV 다운로드
st.header("📋 Operation Log")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 Download CSV", data=csv, file_name="BlastTap9.2_Report.csv", mime='text/csv')
