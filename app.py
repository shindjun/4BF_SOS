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

# 페이지 초기설정
st.set_page_config(page_title="BlastTap 9.9 Pro — AI 고로조업 지원 통합엔진", layout="wide")
st.title("🔥 BlastTap 9.9 Pro — 실시간 AI 고로조업 지원 통합버전")

# 세션 초기화
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
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# ② 정상조업 기본입력
st.sidebar.header("① 정상조업 기본입력")

# 장입/수지 입력
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그비율 (kg/T-P)", value=305.0)
reduction_efficiency = st.sidebar.number_input("기본 환원율 (기본 1.0)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍/조습/산소/PCI 입력
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_enrichment_rate = st.sidebar.number_input("산소부화율 (%)", value=6.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (ton/hr)", value=90.0)

# 압력/온도 입력
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=4.0)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183)
measured_temp = st.sidebar.number_input("실제 용선온도 (°C)", value=1515.0)

# 생산성 & 체류시간
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
k_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# 송풍원단위 입력 (자동계산도 병행)
blast_unit_manual = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ③ 비상조업 보정입력
st.sidebar.header("② 비상조업 보정입력")

abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (ton/hr)", value=pci_rate)
    abnormal_blast_unit_manual = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=blast_unit_manual)
else:
    abnormal_charging_delay = 0

# 📌 기준일자 및 경과시간
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# 📌 시간분할 경과계산
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60,
                                elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
    normal_elapsed = elapsed_minutes
    abnormal_elapsed = 0
    after_elapsed = 0

# 📌 비상조업 장입지연 보정
abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0)

# 📌 전체 장입시간 보정
adjusted_elapsed_minutes = normal_elapsed + abnormal_adjusted_elapsed + after_elapsed
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 60)

# ④ AI 환원효율 계산 (정상조업 기준)

# 조업효율 영향요소 계산
size_effect = 1.0  # (고정)
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_ratio / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_rate_effect = iron_rate / 9.0
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

# 정상 환원효율 계산
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * iron_rate_effect * measured_temp_effect *
    K_factor * 0.9
)

# 📌 비상조업 환원효율 계산 (비상조업 시만 반영)
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_volume / (60 * abnormal_blast_volume) / 0.21)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
        temp_effect * abnormal_pci_effect * iron_rate_effect * measured_temp_effect *
        K_factor * 0.9
    )
else:
    abnormal_reduction_eff = normal_reduction_eff

# 📌 구간별 누적 Charge 수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_adjusted_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# 📌 Ore → Fe → 생산량으로 변환
normal_ore = ore_per_charge * normal_charges
abnormal_ore = ore_per_charge * abnormal_charges
after_ore = ore_per_charge * after_charges

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

# 📌 이론 누적 생산량 산출 (AI 이론생산량)
production_ton_ai = normal_production + abnormal_production + after_production
production_ton_ai = max(production_ton_ai, 0)

# 📌 체류시간 보정 (실질 용융물 보정 생산량)
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 📌 환원효율 기반 일일생산량 예측 (송풍원단위는 따로계산)
if elapsed_charges > 0:
    daily_production_est_reduction = (ore_per_charge * elapsed_charges * (tfe_percent/100) * normal_reduction_eff) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est_reduction = 0

# ⑤ 송풍원단위 기반 AI 예측 일일생산량 (풍량원단위 방식)
# 산소부화량과 송풍량 기반 총송풍량을 Nm³/day 단위로 환산

# 총 송풍량 = (풍량 × 1440) + (산소부화량 × 24 / 0.21)
total_blast_volume_per_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)

# 송풍원단위 기반 예상 일일생산량 (ton/day)
if blast_unit > 0:
    daily_production_est_blast_unit = total_blast_volume_per_day / blast_unit
else:
    daily_production_est_blast_unit = 0

# 비상조업 시 송풍원단위 보정계산
if abnormal_active:
    abnormal_total_blast_volume_per_day = (abnormal_blast_volume * 1440) + (abnormal_oxygen_volume * 24 / 0.21)
    if abnormal_blast_unit > 0:
        abnormal_daily_production_est_blast_unit = abnormal_total_blast_volume_per_day / abnormal_blast_unit
    else:
        abnormal_daily_production_est_blast_unit = 0
else:
    abnormal_daily_production_est_blast_unit = daily_production_est_blast_unit

# 🔧 실측 TAP 실시간 출선량 반영

# 실측 TAP 생산량 입력 → ③에서 입력된 값 재활용
# production_ton_tap = completed_taps * fixed_avg_tap_output

# 🔧 이중수지 병합 (AI+실측 평균)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 🔧 생산수지 편차 산출 (AI-실측차이)
production_gap = effective_production_ton - production_ton_tap

# 🔧 최종 산출 환원효율 표시 (표시용)
final_reduction_efficiency = normal_reduction_eff

# ⑥ 실측 TAP 기반 출선 실적 입력
st.sidebar.header("③ 실측 출선 실적 입력")

# TAP 출선량 실측 (매일변경 가능)
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균 용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# ✅ 선행/후행 출선 실시간 누적추적 입력

st.sidebar.header("④ 실시간 출선량 입력")

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

# ✅ 누적 용선출선량 합산 (실측 + 실시간 선행·후행 합산)
total_tapped_hot_metal = production_ton_tap + lead_tapped + follow_tapped

# ✅ 누적 슬래그출선량 자동계산
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# ✅ 실시간 잔류 저선량 추적
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# ✅ 저선경보판 표시
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ⑦ AI 출선전략 추천

st.header("🧮 AI 출선전략 & 공취예상")

# ✅ 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# ✅ 출선간격 추천 로직
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "20~25분"
else:
    next_tap_interval = "30분↑ 조정권고"

# ✅ 평균 TAP당 용선/슬래그 자동계산
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# ✅ 공취예상시간 (선행-후행 잔류시간 계산)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1250.0)
lead_remain = max(lead_target - lead_tapped, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# ✅ 실시간 결과 표시
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton → 잔여출선시간: {lead_remain_time:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# ⑧ 실시간 용융물 수지 시각화

st.header("📈 실시간 용융물 수지곡선")

# 시간축 생성 (15분 단위)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 정상 환원효율 기준 누적생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 보정 적용
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화 출력
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

# ⑨ 최종 AI 종합리포트 출력

st.header("📊 BlastTap 9.9 Pro — AI 실시간 종합리포트")

# AI 생산수지 요약 출력
st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"일일 실시간 용선배출량 (TAP 실적): {production_ton_tap:.1f} ton")
st.write(f"AI 이중수지 평균 생산량: {production_ton:.1f} ton")

# 일일 생산량 예측 (두 방식 병행 표시)
st.write(f"AI 예측 일일생산량 (환원효율 기준): {daily_production_est_reduction:.1f} ton/day")
st.write(f"AI 예측 일일생산량 (송풍원단위 기준): {daily_production_est_blast_unit:.1f} ton/day")

# 누적 출선/슬래그 수지
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {total_tapped_slag:.1f} ton")

# 저선량 및 상태
st.write(f"잔류 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# 현장 실측 용선온도
st.write(f"현장 실측 용선온도 (Tf): {measured_temp:.1f} °C")

# ✅ 누적 기록 저장 (최대 100개 유지)
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
    "일일생산량_환원효율": daily_production_est_reduction,
    "일일생산량_송풍원단위": daily_production_est_blast_unit,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# ✅ 누적 리포트 표시 및 다운로드 제공
st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.9_Report.csv", mime='text/csv')
