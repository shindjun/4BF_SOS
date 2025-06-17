import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 📌 폰트설정
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 📌 페이지 설정
st.set_page_config(page_title="BlastTap 9.8 Pro Edition", layout="wide")
st.title("🔥 BlastTap 9.8 Pro — 실시간 고로 AI 조업지원 시스템")

# 📌 세션 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (교대 07시 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# 📌 참고지수
iron_density = 7.0   # 용선 비중 (ton/m³)
slag_density = 2.3   # 슬래그 비중 (ton/m³)

# =================== ① 정상조업 기본입력 ===================
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_gen_kg = st.sidebar.number_input("슬래그 발생량 (kg/thm)", value=280.0)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)

# 산소부화량 수동입력 → 부화율 자동계산
oxygen_volume_hr = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)

if blast_volume > 0:
    oxygen_enrichment = (oxygen_volume_hr / (blast_volume * 60)) * 100
else:
    oxygen_enrichment = 0
st.sidebar.write(f"산소부화율 자동계산결과: {oxygen_enrichment:.2f} %")

humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=90.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1183)
measured_temp = st.sidebar.number_input("현재 용선온도 (℃)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
manual_blast_specific_volume = st.sidebar.number_input("송풍원단위 수동입력 (Nm³/ton)", value=1189.0)

# =================== ② 출선 작업조건 ===================
st.sidebar.header("② 출선 작업조건")

lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
tap_interval_min = st.sidebar.number_input("출선간격 (계획) (분)", value=200.0)

# =================== ③ 현재 실시간 출선량 ===================
st.sidebar.header("③ 현재 실시간 출선량")

lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)

# 선행/후행 소요시간 자동계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# 누적 용선 출선량
lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed
total_hot_metal_tapped = lead_tapped + follow_tapped

# 누적 슬래그출선량 자동계산
total_slag_tapped = (total_hot_metal_tapped / 1000) * (slag_gen_kg / iron_density)

# 출력
st.sidebar.write(f"선행 소요시간: {lead_elapsed:.1f}분 → 용선출선: {lead_tapped:.1f} ton")
st.sidebar.write(f"후행 소요시간: {follow_elapsed:.1f}분 → 용선출선: {follow_tapped:.1f} ton")
st.sidebar.write(f"누적 슬래그출선량 (자동계산): {total_slag_tapped:.1f} ton")

# =================== ④ 비상조업 입력 ===================
st.sidebar.header("④ 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume_hr = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume_hr)
    if abnormal_blast_volume > 0:
        abnormal_oxygen_enrichment = (abnormal_oxygen_volume_hr / (abnormal_blast_volume * 60)) * 100
    else:
        abnormal_oxygen_enrichment = 0
    st.sidebar.write(f"비상 산소부화율 자동계산: {abnormal_oxygen_enrichment:.2f} %")
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_blast_specific_volume = st.sidebar.number_input("비상 송풍원단위 (Nm³/ton)", value=manual_blast_specific_volume)
else:
    abnormal_charging_delay = 0
    abnormal_blast_volume = blast_volume
    abnormal_oxygen_volume_hr = oxygen_volume_hr
    abnormal_oxygen_enrichment = oxygen_enrichment
    abnormal_humidification = humidification
    abnormal_pci_rate = pci_rate
    abnormal_blast_specific_volume = manual_blast_specific_volume

# =================== ②부: 시간분할 · 환원효율 · AI 생산량 ===================

# 📌 경과시간 자동계산
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)  # 하루 최대 1440분 제한

# 📌 Charge당 생산속도
charge_rate = 60 / charging_time_per_charge

# 📌 시간분할 비상조업 구간분리
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

# 📌 비상조업 장입지연 적용
abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0)

# 📌 총 조정된 장입시간
adjusted_elapsed_minutes = normal_elapsed + abnormal_adjusted_elapsed + after_elapsed
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 60)

# 📌 누적 Charge수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_adjusted_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# 📌 생산량 계산 (구간별 Ore → Fe → 환원)
normal_ore = ore_per_charge * normal_charges
abnormal_ore = ore_per_charge * abnormal_charges
after_ore = ore_per_charge * after_charges

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 📌 환원효율 계산 로직

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
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

# 비상조업 환원효율 계산
abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
    abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * abnormal_pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

# 📌 AI 이론 생산량 계산
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# 📌 체류시간 보정 (용융물 활성량 계산)
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 📌 AI 예측 일일생산량
if elapsed_charges > 0:
    daily_production_est = (ore_per_charge * elapsed_charges * (tfe_percent/100) * normal_reduction_eff) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est = 0

# =================== ③부: 실측출선 병합 · 저선량 추적 ===================

# 📌 실측 Tap 기반 출선실적 입력 (TAP 평균 생산량 → 간략화 유지)
st.sidebar.header("⑤ 실측 출선 실적 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 📌 이중수지 병합: (AI 계산 + 실측 출선량 평균)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 📌 수지편차 계산 (AI - 실측)
production_gap = effective_production_ton - production_ton_tap

# 📌 실시간 누적 출선량 (용선 기준)
total_tapped_hot_metal = total_hot_metal_tapped  # 선행+후행 누적출선량 합계

# 📌 누적 슬래그 출선량 (이미 자동계산됨)
total_tapped_slag = total_slag_tapped

# 📌 저선량(잔류 용융물량) 추적: 용선 기준
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 📌 저선율 계산
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 📌 저선 상태 경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상운전"

# 📌 간이 확인 출력 (리포트에서 확장)
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량: {daily_production_est:.1f} ton/day")
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량: {total_tapped_slag:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"수지편차 (AI - TAP): {production_gap:.1f} ton")
st.write(f"조업상태: {status}")

# =================== ④부: AI 출선전략 추천 엔진 ===================

# 📌 평균 Tap당 출선/슬래그량 계산 (실측 기준)
if completed_taps > 0:
    avg_hot_metal_per_tap = production_ton / completed_taps
else:
    avg_hot_metal_per_tap = 0

# 📌 평균 슬래그량 계산 (슬래그자동계산기준)
if completed_taps > 0:
    avg_slag_per_tap = total_tapped_slag / completed_taps
else:
    avg_slag_per_tap = 0

# 📌 AI 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 📌 AI 출선간격 추천 로직
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 7:
    next_tap_interval = "10~15분"
elif residual_rate < 9:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 출선 필요 (0~5분)"

# 📌 AI 리포트 출력
st.header("📊 AI 실시간 출선전략 리포트")

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")

# =================== ⑤부: 공취예상시간 + 잔여출선 추적 ===================

# 📌 선행 출선 잔여량 계산 (목표기준 설정)
lead_target_output = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)

# 현재 선행 출선 잔여량 (ton)
lead_remain_ton = max(lead_target_output - lead_tapped, 0)

# 남은 출선시간 (분)
lead_remain_time = lead_remain_ton / lead_speed if lead_speed > 0 else 0

# 📌 실시간 공취예상시간 계산 (선행 잔여출선 → 후행 경과 대비)
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# 📌 실시간 리포트 출력 (공취예상 포함)
st.header("📊 실시간 공취예상 & 잔류출선 리포트")

st.write(f"선행 현재 누적출선량: {lead_tapped:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain_ton:.1f} ton")
st.write(f"선행 잔여출선 예상시간: {lead_remain_time:.1f} 분")
st.write(f"후행 경과시간: {follow_elapsed:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# =================== ⑥부: 시각화 및 누적 리포트 기록 ===================

# 📌 실시간 용융물 수지 추적 시각화
st.header("📊 실시간 용융물 수지 추적")

# 시간축 생성
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 정상환원효율 기준 누적생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 보정 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 추적")
plt.ylim(0, production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# 📌 누적 리포트 기록 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "이중수지평균": production_ton,
    "출선량(용선)": total_tapped_hot_metal,
    "출선량(슬래그)": total_tapped_slag,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "예상일일생산량": daily_production_est,
    "공취예상시간": gap_minutes,
    "조업상태": status
}

st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 📌 누적 리포트 테이블 표시
st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# 📌 CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap9.8_Pro_Report.csv", mime='text/csv')
