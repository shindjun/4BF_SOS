import streamlit as st
import datetime

# 기본 설정
st.set_page_config(page_title="BlastTap 9.9 Pro — 실시간 AI 고로조업지원 엔진", layout="wide")
st.title("🔥 BlastTap 9.9 Pro — 실시간 AI 고로조업지원 통합버전")

now = datetime.datetime.now()
base_date = datetime.date.today() if now.hour >= 7 else datetime.date.today() - datetime.timedelta(days=1)
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = max((now - today_start).total_seconds() / 60, 60)

# ① 정상조업 입력
st.sidebar.header("① 정상조업 기본 입력")

charging_time_per_charge = st.sidebar.number_input("장입시간 (분/Charge)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

reduction_efficiency = st.sidebar.number_input("환원율 계수", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 (kg/thm)", value=90.0)

top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1183)
measured_temp = st.sidebar.number_input("실측 용선온도 (℃)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
blowing_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

# ② 비상조업 입력
st.sidebar.header("② 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_blowing_unit = st.sidebar.number_input("비상 송풍원단위 (Nm3/t)", value=blowing_unit)

# 2부 — AI 생산량 이론 계산

# 정상조업 환원효율 계산
size_effect = 1.0
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_enrichment = (oxygen_volume * 60) / (blast_volume * 60) / 10 * 100  # 자동 산소부화율 계산 (보조 출력용)
oxygen_boost = 1 + ((oxygen_volume * 60) / (blast_volume * 60) / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
    temp_effect * pci_effect * iron_temp_effect * K_factor * 0.9

# 시간보정 경과시간 분리
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
    abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0)
else:
    normal_elapsed = elapsed_minutes
    abnormal_adjusted_elapsed = 0
    after_elapsed = 0

adjusted_elapsed_minutes = max(normal_elapsed + abnormal_adjusted_elapsed + after_elapsed, 60)

# 누적 장입 Charge 수량
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_ore = ore_per_charge * elapsed_charges
normal_fe = normal_ore * (tfe_percent / 100)
production_ton_ai = normal_fe * normal_reduction_eff

# 체류시간 보정 생산량
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes)

# AI 예측 일일 생산량 (송풍원단위 방식)
daily_production_est = ((blast_volume * 1440) + (oxygen_volume * 24 / 0.21)) / blowing_unit

# 3부 — 실시간 출선 실적 및 이중수지 병합 계산

# ① 실시간 출선 실적 입력부
st.sidebar.subheader("③ 실시간 출선 실적 입력")

# TAP당 평균 용선출선량 (ton) — 실시간 가변 입력 가능
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균 용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)

# 실측 TAP 생산량
production_ton_tap = completed_taps * fixed_avg_tap_output

# ② 이중수지 평균 생산량 (AI+실측 병합)
production_ton = (effective_production_ton + production_ton_tap) / 2

# ③ 수지 편차
production_gap = effective_production_ton - production_ton_tap

# ④ 실시간 선행·후행 출선 입력
st.sidebar.subheader("④ 선행·후행 실시간 출선 입력")

# 선행 출선 시작시각 & 속도
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)

# 후행 출선 시작시각 & 속도
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)

# 실시간 경과시간 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# 실시간 출선량 누적계산
lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 총 누적 출선량 (실측 + 선행 + 후행)
total_tapped_hot_metal = production_ton_tap + lead_tapped + follow_tapped

# 슬래그 누적 자동계산
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# 잔류 저선량 추적
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 저선 상태 판단
if residual_molten >= 200:
    status = "🔴 저선 위험"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 주의"
else:
    status = "✅ 정상"

# ⑤ AI 출선전략 및 공취예상시간

st.header("🧮 AI 출선전략 · 공취예상")

# 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 차기 출선간격 추천
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "20~25분"
else:
    next_tap_interval = "30분 이상 조정권고"

# 선행 목표출선량 (가변 입력 가능)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1250.0)
lead_remain = max(lead_target - lead_tapped, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 공취예상시간 계산 (선행 잔여시간 - 후행경과시간)
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# TAP당 평균출선량 자동계산 (실제 데이터 기반)
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# 결과 출력
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton → 잔여출선시간: {lead_remain_time:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# ⑥ 실시간 용융물 수지곡선 시각화

import matplotlib.pyplot as plt
import platform

# 한글 폰트 설정 (윈도우/리눅스 대응)
if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

st.header("📈 실시간 용융물 수지곡선")

# 시간축 생성 (15분 단위 시뮬레이션)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 정상환원효율 기준 생산곡선
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 보정
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화 플롯
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 용선출선량 (ton)")
plt.plot(time_labels, residual_series, label="잔류 저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지곡선")
plt.grid()
plt.legend()
st.pyplot(plt)

# ⑦ AI 종합 리포트 출력

st.header("📊 BlastTap 9.9 Pro — AI 실시간 종합 리포트")

# AI 생산수지 출력
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실시간 TAP 용선출선량: {production_ton_tap:.1f} ton")
st.write(f"AI 이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 일일예상생산량 (송풍원단위 기반): {daily_production_est:.1f} ton/day")

# 출선수지
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {total_tapped_slag:.1f} ton")

# 저선수지
st.write(f"잔류 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# 실측 용선온도
st.write(f"실제 용선온도: {measured_temp:.1f} °C")

# 누적 기록 관리
if 'log' not in st.session_state:
    st.session_state['log'] = []

record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI 이론생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측출선량": production_ton_tap,
    "이중수지평균": production_ton,
    "누적출선량": total_tapped_hot_metal,
    "누적슬래그": total_tapped_slag,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "예상일일생산량": daily_production_est,
    "조업상태": status
}

st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 누적 리포트 표시 및 다운로드 제공
st.subheader("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.9_Pro_Report.csv", mime='text/csv')
