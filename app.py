import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 안정화
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(page_title="BlastTap 9.9 Pro — 실시간 AI 고로조업지원 통합엔진", layout="wide")
st.title("🔥 BlastTap 9.9 Pro Edition — 실시간 AI 고로조업지원 통합엔진")

# 세션 로그 초기화
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
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# 📌 2부 — 정상조업 입력부

st.sidebar.header("① 정상조업 입력")

# 기본 장입 속도 및 생산량 조건
charging_time_per_charge = st.sidebar.number_input("1 Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원효율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# AI 용선온도 관련 입력 (실측온도 반영)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515)

# 송풍 및 조습 관련
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
oxygen_enrichment_rate = st.sidebar.number_input("산소부화율 (%)", value=6.0)
oxygen_enrichment = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)

# 기타 AI 보정 인자
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# 신규 추가: 송풍원단위 입력
blast_unit = st.sidebar.number_input("송풍원단위 (Nm3/ton)", value=1189.0)

# 📌 3부 — 비상조업 입력 및 시간분할처리

st.sidebar.header("② 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작 시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료 시각", value=datetime.time(13, 0))

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_enrichment)
    abnormal_oxygen_rate = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_rate)
    abnormal_blast_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/ton)", value=blast_unit)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 취입량 (kg/thm)", value=pci_rate)
else:
    abnormal_charging_delay = 0
    abnormal_blast_volume = blast_volume
    abnormal_oxygen = oxygen_enrichment
    abnormal_oxygen_rate = oxygen_enrichment_rate
    abnormal_blast_unit = blast_unit
    abnormal_pci_rate = pci_rate

# 📌 시간분할 계산
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

abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0)
adjusted_elapsed_minutes = normal_elapsed + abnormal_adjusted_elapsed + after_elapsed
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 60)

# 📌 4부 — AI 이론생산량 + 체류보정 + 송풍원단위 예측

# ✅ 정상 환원효율 계산
size_effect = 1.0
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_rate / 10)
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

# ✅ 비상 환원효율 계산 (비상조업 적용시)
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_rate / 10)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * abnormal_pci_effect * iron_rate_effect * measured_temp_effect * K_factor * 0.9
else:
    abnormal_reduction_eff = normal_reduction_eff

# ✅ Charge 수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_adjusted_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# ✅ Fe 투입량 및 AI 이론생산량 계산
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

# ✅ 체류시간 보정 생산량
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# ✅ 송풍원단위 기반 일일 생산량 자동 계산 (AI 예측 핵심)
daily_production_by_blast_unit = ((blast_volume * 1440) + (oxygen_enrichment * 24 / 0.21)) / blast_unit

# 📌 5부 — 실측 출선 실적 · 실시간 출선량 · 저선 추적 통합

# ✅ 5-1 실측 TAP 기반 출선 실적 입력
st.sidebar.header("⑤ 실측 출선 실적 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균 용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# ✅ 5-2 실시간 출선속도 기반 실시간 누적 출선량 계산
st.sidebar.header("③ 현재 실시간 출선량")

lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=7.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=3.0)

lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))

lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# ✅ 5-3 선행/후행 현재까지 출선량 표시
lead_tapped = max(lead_tapped, 0)
follow_tapped = max(follow_tapped, 0)

st.write(f"선행 소요시간: {lead_elapsed:.1f}분 → 용선출선: {lead_tapped:.1f} ton")
st.write(f"후행 소요시간: {follow_elapsed:.1f}분 → 용선출선: {follow_tapped:.1f} ton")

# ✅ 5-4 누적 용선 출선량 최종 통합 (실시간 + TAP)
total_tapped_hot_metal = production_ton_tap + lead_tapped + follow_tapped

# ✅ 5-5 슬래그 자동계산 (누적)
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# ✅ 5-6 이중수지 평균 생산량
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# ✅ 5-7 저선량(잔류 용융물) 계산
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# ✅ 5-8 저선 경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상운전"

# 📌 6부 — AI 출선전략 추천 · 비트경 · 출선간격

st.header("🧮 AI 출선전략 추천")

# ✅ 평균 TAP당 용선/슬래그 자동계산
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# ✅ 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# ✅ AI 출선간격 추천 로직 (실제 조업 패턴 근거)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "20~25분"
else:
    next_tap_interval = "30분↑ 조정권고"

# ✅ AI 결과 표시
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")

# 📌 7부 — 공취예상시간 & 실시간 잔류출선량 추적

st.header("📊 공취예상시간 & 실시간 잔류출선량")

# ✅ 선행 잔여출선 계산
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
lead_tapped = lead_elapsed * lead_speed
lead_remain_hot_metal = max(lead_target - lead_tapped, 0)
lead_remain_time = lead_remain_hot_metal / lead_speed if lead_speed > 0 else 0

# ✅ 후행 출선 경과시간
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)
follow_tapped = follow_elapsed * follow_speed

# ✅ 공취발생 예측
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# ✅ 누적 출선량 재계산
completed_tap_amount = completed_taps * fixed_avg_tap_output
total_tapped_hot_metal = completed_tap_amount + lead_tapped + follow_tapped

# ✅ 잔류 저선량 재계산
residual_molten = max(production_ton - total_tapped_hot_metal, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# ✅ 슬래그 자동 누적반영
total_slag_amount = total_tapped_hot_metal / slag_ratio

# ✅ 실시간 결과 표시
st.write(f"선행 현재 누적출선량: {lead_tapped:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain_hot_metal:.1f} ton → 잔여시간: {lead_remain_time:.1f} 분")
st.write(f"후행 출선 경과시간: {follow_elapsed:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {total_slag_amount:.1f} ton")
st.write(f"실시간 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")

# 📌 8부 — 실시간 용융물 수지추적 시각화

st.header("📈 실시간 용융물 수지 시각화")

# ✅ 시간축 (15분 단위 생성)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# ✅ 이론 누적 생산량 시뮬레이션 (체류시간 보정 포함)
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# ✅ 시각화 그래프 출력
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 용선출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 추적")
plt.grid()
plt.legend()
st.pyplot(plt)

# 📌 9부 — 최종 AI 종합 리포트 출력 및 누적 리포트 기록

st.header("📊 BlastTap 9.9 Pro — AI 실시간 종합 리포트")

# ✅ AI 생산수지 요약 출력
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량 (일일 실시간 용선배출량): {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량 (송풍원단위): {daily_production_by_blast_unit:.1f} ton/day")

# ✅ 누적 출선 및 슬래그 수지
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동): {total_tapped_slag:.1f} ton")

# ✅ 저선량 및 상태
st.write(f"잔류 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# ✅ 용선온도 표시 (실측값 기준 유지)
st.write(f"현장 실측 용선온도 (Tf): {measured_temp:.1f} °C")

# ✅ 누적 리포트 기록 저장 (100개 제한)
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI 이론생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측출선량": production_ton_tap,
    "이중수지평균": production_ton,
    "누적출선량": total_tapped_hot_metal,
    "누적슬래그량": total_tapped_slag,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "예상일일생산량": daily_production_by_blast_unit,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# ✅ 누적 리포트 표시 및 다운로드
st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.9_Report.csv", mime='text/csv')
