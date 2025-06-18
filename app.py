import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

폰트 설정 (한글 안정화)

if platform.system() == "Windows":
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

페이지 설정

st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

세션 로그 초기화

if 'log' not in st.session_state:
st.session_state['log'] = []

기준일자 설정 (07시 교대 기준)

now = datetime.datetime.now()
if now.hour < 7:
base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

경과 시간 계산 (07시 기준)

elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

========================== 2부: 정상조업 입력부 ==========================

st.sidebar.header("① 정상조업 기본입력")

장입속도

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

장입량

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)

O/C 계산값 출력

if coke_per_charge > 0:
ore_coke_ratio = ore_per_charge / coke_per_charge
else:
ore_coke_ratio = 0
st.sidebar.markdown(f"O/C 비율: {ore_coke_ratio:.2f}")

철광석 성분 및 슬래그비율

tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

조업지수 및 용해능력

reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

송풍·산소

blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

조습·미분탄

humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

압력 및 온도

top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

송풍 원단위 (Nm³/t)

wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================

비상조업 보정 입력

st.sidebar.header("② 비상조업 보정입력")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))

abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)  
abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정 (분)", value=300)  

abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)  
abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)  
abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)  
abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)  
abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)  
abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

감풍·휴풍 보정 입력

st.sidebar.header("③ 감풍·휴풍 보정입력")
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)

if reduction_active:
reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0))
reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0))

reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간 (분)", value=0)  

reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm³/min)", value=blast_volume)  
reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm³/hr)", value=oxygen_volume)  
reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual)  
reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm³)", value=humidification)  
reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 (kg/thm)", value=pci_rate)  
reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위 (Nm³/t)", value=wind_unit)

========================== 4부: 환원효율 계산 및 시간분할 생산량 계산 ==========================

환원효율 관련 계수 계산

size_effect = (20 / 20 + 60 / 60) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

기본 환원효율 (정상조업 기준)

normal_reduction_eff = (
reduction_efficiency * size_effect * melting_effect * gas_effect *
oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9
)

시간 분할: 정상-비상-감풍 구간 구분

normal_elapsed = elapsed_minutes
abnormal_elapsed = 0
reduction_elapsed = 0

if abnormal_active:
abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)
normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60,
elapsed_minutes - normal_elapsed), 0)
after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
after_elapsed = max(elapsed_minutes - normal_elapsed, 0)

if reduction_active:
reduction_start_dt = datetime.datetime.combine(base_date, reduction_start_time)
reduction_end_dt = datetime.datetime.combine(base_date, reduction_end_time)
normal_elapsed = min((reduction_start_dt - today_start).total_seconds() / 60, normal_elapsed)
reduction_elapsed = max(min((reduction_end_dt - reduction_start_dt).total_seconds() / 60,
elapsed_minutes - (normal_elapsed + abnormal_elapsed)), 0)
after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed + reduction_elapsed), 0)

비상조업 환원효율

if abnormal_active:
abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
abnormal_temp_effect = temp_effect  # 풍온 동일 적용
abnormal_reduction_eff = (
reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor * 0.9
)
else:
abnormal_reduction_eff = normal_reduction_eff

감풍조업 환원효율

if reduction_active:
reduction_gas_effect = 1 + (reduction_blast_volume - 4000) / 8000
reduction_oxygen_boost = 1 + (reduction_oxygen_enrichment / 10)
reduction_humidity_effect = 1 - (reduction_humidification / 100)
reduction_pci_effect = 1 + (reduction_pci_rate - 150) / 100 * 0.02
reduction_temp_effect = temp_effect
reduction_reduction_eff = (
reduction_efficiency * size_effect * melting_effect * reduction_gas_effect *
reduction_oxygen_boost * reduction_humidity_effect * pressure_boost * blow_pressure_boost *
reduction_temp_effect * reduction_pci_effect * measured_temp_effect * K_factor * 0.9
)
else:
reduction_reduction_eff = normal_reduction_eff

체류시간 적용: 비상조업 체크 시만 적용

if abnormal_active:
adjusted_elapsed_minutes = max(elapsed_minutes - abnormal_total_melting_delay, 0)
else:
adjusted_elapsed_minutes = elapsed_minutes

Charge 수 계산

elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

Ore 및 Fe 환산

normal_ore = ore_per_charge * charge_rate * (normal_elapsed / 60)
abnormal_ore = ore_per_charge * charge_rate * (abnormal_elapsed / 60)
reduction_ore = ore_per_charge * charge_rate * (reduction_elapsed / 60)
after_ore = ore_per_charge * charge_rate * (after_elapsed / 60)

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
reduction_fe = reduction_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

생산량 계산 (AI 기반)

normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
reduction_production = reduction_fe * reduction_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = (
normal_production + abnormal_production + reduction_production + after_production
)

============================ 5부: 실측 출선 및 저선량 계산 ============================

실측 출선값 (종료된 Tap)

closed_tap_weight = st.sidebar.number_input("종료된 Tap 출선량 (ton)", value=0.0)

선행·후행 출선량

lead_tap_weight = st.sidebar.number_input("선행 Tap 출선량 (ton)", value=0.0)
follow_tap_weight = st.sidebar.number_input("후행 Tap 출선량 (ton)", value=0.0)

일일 실시간 출선량

realtime_tap_weight = st.sidebar.number_input("일일 실시간 용선 출선량 (ton)", value=0.0)

총 누적 출선량 = 실측 + 선행 + 후행

total_tapped_hot_metal = closed_tap_weight + lead_tap_weight + follow_tap_weight + realtime_tap_weight

🔸 예상 누적 생산량 (현재 시각 기반)

elapsed_ratio = elapsed_minutes / 1440  # 하루 1440분 기준
daily_expected_production = wind_air_day / wind_unit
expected_till_now = daily_expected_production * elapsed_ratio

🔸 저선량 계산 = 누적 생산량 - 누적 출선량

residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

🔸 슬래그 자동계산: 누적 용선 출선량 × 고정 슬래그비율 (예: 0.33)

slag_ratio = 0.33
accumulated_slag = total_tapped_hot_metal * slag_ratio

============================ 6부: 주요 결과 요약 및 리포트 ============================

st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

🌐 예상 누적 생산량 (현재 시각 기준)

st.subheader("📈 일일 생산량 기준 예측")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재 시각까지 누적 예상 생산량: {expected_till_now:.1f} ton")

🔩 실측 출선량

st.subheader("💧 누적 출선량")
st.write(f"종료된 Tap 출선량: {closed_tap_weight:.1f} ton")
st.write(f"선행 Tap 출선량: {lead_tap_weight:.1f} ton")
st.write(f"후행 Tap 출선량: {follow_tap_weight:.1f} ton")
st.write(f"일일 실시간 출선량: {realtime_tap_weight:.1f} ton")
st.write(f"총 누적 출선량: {total_tapped_hot_metal:.1f} ton")

🔥 저선량 및 슬래그 자동 계산

st.subheader("🔥 저선량 및 슬래그량 추정")
st.write(f"현재 시각 기준 저선량 (예측): {residual_molten:.1f} ton")
st.write(f"누적 슬래그량 (자동계산): {accumulated_slag:.1f} ton")

🔴 저선 경보판

if residual_molten >= 200:
status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
status = "🟡 저선 관리 권고"
else:
status = "✅ 정상 운영"

st.subheader("⚠️ 조업 상태 진단")
st.write(f"조업 상태: {status}")

============================ 7부: 실시간 시각화 ============================

st.subheader("📊 실시간 용융물 수지 시각화")

시계열 시간축 (예: 15분 단위)

time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

누적 생산량 시뮬레이션 시계열

gen_series = []
for t in time_labels:
prod = daily_expected_production * (t / 1440)
gen_series.append(prod)

누적 출선량 시계열

tap_series = [total_tapped_hot_metal] * len(time_labels)

저선 시계열 (예상 생산 - 출선)

residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

시각화

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")

plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.legend()
plt.grid(True)

st.pyplot(plt)

============================ 8부: 누적 리포트 기록 ============================

st.subheader("📋 누적 조업 리포트 기록")

리포트 항목 기록용 dict

record = {
"기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
"일일예상생산량(t/day)": daily_expected_production,
"예상누적생산량(t)": production_ton_ai,
"누적출선량(t)": total_tapped_hot_metal,
"현재저선량(t)": residual_molten,
"저선율(%)": residual_rate,
"조업상태": status,
"선행출선량(t)": lead_output,
"후행출선량(t)": follow_output,
"종료된Tap출선량(t)": tap_total_output,
"현재경과시간(min)": elapsed_minutes
}

세션에 저장

if 'log' not in st.session_state:
st.session_state['log'] = []
st.session_state['log'].append(record)

500건 초과 시 oldest 삭제

if len(st.session_state['log']) > 500:
st.session_state['log'].pop(0)

테이블 표시

df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

CSV 다운로드 버튼

csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

============================ 9부: 마무리 안내 및 제작 정보 ============================

st.markdown("---")
st.markdown("#### 🛠️ BlastTap 10.3 Pro — AI 기반 고로조업 통합 시스템")
st.markdown("- 제작: 신동준 (개발지원: ChatGPT + Streamlit 기반)")
st.markdown("- 업데이트일: 2025-06 기준 최종반영")
st.markdown("- 기능: 일일생산량 예측, 실시간 저선관리, 출선전략, CSV 기록 저장 등 통합 제공")
st.markdown("- 버그 또는 개선 요청: GitHub 또는 내부 관리 시스템에 등록")

st.info("💡 모든 조업 정보는 07시 기준으로 일일 초기화되며, 실시간 출선소요 기반으로 누적 생산량이 자동 보정됩니다.")
st.success("📌 BlastTap 10.3 Pro는 현재 베타 운영 중이며, 조업 안정성과 자동화 연동 고도화를 목표로 지속 개선됩니다.")


