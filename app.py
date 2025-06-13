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

# 🔧 페이지 설정
st.set_page_config(page_title="BlastTap 9.0 — AI 실시간 고로조업 최적화", layout="wide")
st.title("🔥 BlastTap 9.0 — AI 실시간 고로조업 최적화")

# 🔧 세션 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 🔧 기준일자 설정 (07시 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = min(max(elapsed_minutes, 0), 1440)

# =================== [입력 파트] ===================

# ⚙ 장입지연 입력
st.sidebar.header("① 장입지연 입력")
charging_delay = st.sidebar.number_input("장입지연 누적시간 (분)", value=0)
adjusted_elapsed_minutes = max(elapsed_minutes - charging_delay, 0)

# ⚙ 장입수지 입력
st.sidebar.header("② 장입수지 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원효율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
furnace_volume = st.sidebar.number_input("고로 유효내용적 (m³)", value=4497)

# ⚙ 조업지수 입력
st.sidebar.header("③ 조업지수 입력")
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7960.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.2)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1194)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# ⚙ 장입속도 입력
st.sidebar.header("④ 장입속도 입력")
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# ⚙ 체류시간 입력 (신규)
st.sidebar.header("⑤ 체류시간 보정")
melting_delay = st.sidebar.number_input("용융 Pool 체류시간 (분)", value=240)

# ⚙ 비상조업 보정 스위치
st.sidebar.header("⑥ 비상조업 보정")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비정상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비정상 종료시각", value=datetime.time(13, 0))
    abnormal_blast_volume = st.sidebar.number_input("비정상 송풍량 (Nm³/min)", value=6000.0)
    abnormal_oxygen = st.sidebar.number_input("비정상 산소부화율 (%)", value=1.5)

# =================== [2부: 이론 생산량 계산 엔진] ===================

# 🔧 정상조업 환원효율 계산
size_effect = (20 / 20 + 60 / 60) / 2  # 입도 고정 가정
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

# 🔧 비상조업 보정 적용 (선택적)
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, adjusted_elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, adjusted_elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(adjusted_elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)

    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen / 10)

    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9

    normal_production = normal_elapsed * iron_rate * normal_reduction_eff / 60
    abnormal_production = abnormal_elapsed * iron_rate * abnormal_reduction_eff / 60
    after_production = after_elapsed * iron_rate * normal_reduction_eff / 60
    production_ton_ai = normal_production + abnormal_production + after_production

else:
    # 정상조업 전체적용
    production_ton_ai = adjusted_elapsed_minutes * iron_rate * normal_reduction_eff / 60

production_ton_ai = max(production_ton_ai, 0)

# 🔧 체류시간 보정 적용 (용융 딜레이 적용)
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

# 딜레이 적용된 유효 생산량
effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 🔧 현재 실시간 일일생산량 예측 계산
if adjusted_elapsed_minutes > 0:
    estimated_daily_production = production_ton_ai / adjusted_elapsed_minutes * 1440
else:
    estimated_daily_production = 0

# =================== [3부: 출선량 추적 및 저선량 계산] ===================

# 🔧 실측 TAP 기반 누적 출선량 입력
st.sidebar.header("⑦ 출선 실측 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 🔧 이중수지 평균 생산량 (AI+TAP)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 🔧 수지편차 계산
production_gap = effective_production_ton - production_ton_tap

# 🔧 출선 실시간 누적계산
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)

# 출선 경과시간 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 🔧 누적 출선량 총합
completed_tap_amount = completed_taps * fixed_avg_tap_output
total_tapped = completed_tap_amount + lead_tapped + follow_tapped
total_tapped = min(total_tapped, production_ton)

# 🔧 저선량 계산 (잔류 용융물)
residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)

# 🔧 저선율 계산
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 🔧 공취 예상시간 계산
lead_close_time = lead_start_dt + datetime.timedelta(minutes=(lead_target / lead_speed))
gap_minutes = max((lead_close_time - follow_start_dt).total_seconds() / 60, 0)

# 🔧 조업상태 경보판단
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# =================== [4부: AI 출선전략 추천] ===================

# 🔧 평균 Tap당 출선/슬래그량 재계산
avg_hot_metal_per_tap = production_ton / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# 🔧 AI 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 🔧 AI 출선간격 추천 로직
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 7:
    next_tap_interval = "10~15분"
elif residual_rate < 9:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 🔧 AI 실시간 일일생산량 예측 (조업전체기준)
if adjusted_elapsed_minutes > 0:
    estimated_daily_production = production_ton / adjusted_elapsed_minutes * 1440
else:
    estimated_daily_production = 0

# 🔧 AI 운영 리포트 출력
st.header("📊 AI 실시간 수지분석 리포트")

st.write(f"AI 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"예상 일일생산량: {estimated_daily_production:.1f} ton/day")
st.write(f"누적 출선량: {total_tapped:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"수지편차 (AI-TAP): {production_gap:.1f} ton")
st.write(f"공취 예상시간: {gap_minutes:.1f} 분")
st.write(f"선행폐쇄 예상시각: {lead_close_time.strftime('%H:%M')}")
st.write(f"조업상태: {status}")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"평균 출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 슬래그량: {avg_slag_per_tap:.1f} ton")

# =================== [5부: 실시간 시각화 및 누적 리포트] ===================

# 🔧 실시간 용융물 수지추적 시각화

st.header("📊 실시간 용융물 수지추적 그래프")

# 그래프용 시간축 생성
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 정상 환원효율 기준 누적 생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 반영 시뮬레이션 보정
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
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

# 🔧 누적 리포트 로그 기록
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "이중수지": production_ton,
    "출선량": total_tapped,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 🔧 누적 리포트 및 CSV 다운로드
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.0_Report.csv", mime='text/csv')
