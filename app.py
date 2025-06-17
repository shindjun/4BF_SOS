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

# 📌 페이지 초기설정
st.set_page_config(page_title="BlastTap 9.8 Pro — 실시간 AI 고로조업지원", layout="wide")
st.title("🔥 BlastTap 9.8 Pro Master — 실시간 AI 고로조업지원 통합엔진")

# 📌 세션 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (교대 기준 07시)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# ================= 정상조업 기본입력 =================

st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
oxygen_amount = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=6.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183)
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1515.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)

# 📌 송풍원단위 입력 및 자동계산
manual_wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/ton)", value=1189.0)

# ================= ②부: AI 환원효율 + 이론생산량 =================

# 📌 기본 참고지수
iron_density = 7.0
slag_density = 2.3

# 📌 시간분할 정상/비상조업 경과시간 나누기 (간략: 비상조업 제외 버전)
normal_elapsed = elapsed_minutes

# 📌 누적 Charge 수
elapsed_charges = charge_rate * (normal_elapsed / 60)
normal_ore = ore_per_charge * elapsed_charges
normal_fe = normal_ore * (tfe_percent / 100)

# 📌 정상조업 환원효율 상세 계산

size_effect = 1.0  # 고정 (20~60mm 기준)
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

# 📌 이론생산량 (환원효율 적용)
production_ton_ai = normal_fe * normal_reduction_eff

# 📌 체류시간 보정
if normal_elapsed > melting_delay:
    active_minutes = normal_elapsed - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / normal_elapsed) if normal_elapsed > 0 else 0

# 📌 기존 방식 일일예상생산량 (AI 계산 기반)
if elapsed_charges > 0:
    daily_production_est_ai = (ore_per_charge * elapsed_charges * (tfe_percent/100) * normal_reduction_eff) * (1440 / normal_elapsed)
else:
    daily_production_est_ai = 0

# 📌 새로운 방식: 송풍원단위 기반 AI 생산량 계산식
# 생산량 (ton/day) = (풍량×1440 + (산소×24/0.21)) / 송풍원단위
total_gas_volume = blast_volume * 1440 + (oxygen_amount * 24 / 0.21)
daily_production_est_gas = total_gas_volume / manual_wind_unit

# ================= ③부: 실측출선 병합 + 저선 추적 =================

st.sidebar.header("③ 출선 실시간 정보")

# 📌 선행/후행 출선 시작시각 입력
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))

lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

# 📌 현재까지의 출선 경과시간 자동계산
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# 📌 선행/후행 출선속도 입력 (ton/min)
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)

# 📌 선행/후행 실시간 출선량 자동계산
lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 📌 실측 TAP 기준 출선 실적
st.sidebar.header("④ 실측 TAP 실적")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 📌 전체 누적 용선 출선량 계산
total_tapped_hot_metal = completed_taps * fixed_avg_tap_output + lead_tapped + follow_tapped

# 📌 누적 슬래그 출선량 자동계산 (슬래그 비중 반영)
total_tapped_slag = (total_tapped_hot_metal / slag_ratio)

# 📌 이중수지 병합 생산량
production_ton = (effective_production_ton + production_ton_tap) / 2

# 📌 수지편차 계산
production_gap = effective_production_ton - production_ton_tap

# 📌 저선량 추적 (잔류용융물량)
residual_molten = production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 📌 저선율 계산
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 📌 저선경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상운전"

# 📌 결과 출력 (간이 요약)
st.header("📊 생산량 · 저선 추적 요약")

st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"AI 예측 일일생산량 (환원효율): {daily_production_est_ai:.1f} ton/day")
st.write(f"AI 예측 일일생산량 (송풍원단위): {daily_production_est_gas:.1f} ton/day")
st.write(f"누적 용선출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동): {total_tapped_slag:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업상태: {status}")

# ================= ④부: AI 출선전략 추천 엔진 =================

st.header("📊 AI 출선전략 추천")

# 📌 평균 TAP당 출선량 및 슬래그량 (실측기준)
if completed_taps > 0:
    avg_hot_metal_per_tap = production_ton / completed_taps
    avg_slag_per_tap = total_tapped_slag / completed_taps
else:
    avg_hot_metal_per_tap = 0
    avg_slag_per_tap = 0

# 📌 AI 비트경 추천 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 📌 AI 출선간격 추천 로직 (잔류저선율 기반)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 7:
    next_tap_interval = "10~15분"
elif residual_rate < 9:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 출선 필요 (0~5분)"

# 📌 AI 전략 리포트 출력
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")
st.write(f"평균 TAP당 용선출선량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"평균 TAP당 슬래그출선량: {avg_slag_per_tap:.1f} ton")

# ================= ⑤부: 실시간 공취예상시간 추적 엔진 =================

st.header("📊 공취예상시간 & 실시간 잔류출선량")

# 📌 선행 목표 출선량 입력
lead_target_output = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)

# 📌 현재 선행 잔류출선량 계산
lead_remain_ton = max(lead_target_output - lead_tapped, 0)

# 📌 선행 잔류출선시간 (분)
lead_remain_time = lead_remain_ton / lead_speed if lead_speed > 0 else 0

# 📌 공취예상시간 (선행 잔류 - 후행 경과시간 차이)
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# 📌 실시간 공취 리포트 출력
st.write(f"선행 현재 누적출선량: {lead_tapped:.1f} ton")
st.write(f"선행 잔여출선량: {lead_remain_ton:.1f} ton")
st.write(f"선행 잔여출선 예상시간: {lead_remain_time:.1f} 분")
st.write(f"후행 출선 경과시간: {follow_elapsed:.1f} 분")
st.write(f"공취 발생 예상시간: {gap_minutes:.1f} 분")

# ================= ⑥부: 실시간 수지 시각화 + 누적기록 =================

st.header("📊 실시간 용융물 수지 시각화")

# 📌 시간축 생성 (15분 단위)
time_labels = [i for i in range(0, int(normal_elapsed)+1, 15)]

# 📌 정상환원효율 기준 누적생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * normal_reduction_eff
    for t in time_labels
]

# 📌 체류시간 보정 적용
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 📌 시각화 그래프 출력
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="잔류 저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 추적")
plt.ylim(0, production_ton * 1.2)
plt.xlim(0, max(normal_elapsed, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# 📌 누적 리포트 기록
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
    "예상일일생산량_AI": daily_production_est_ai,
    "예상일일생산량_송풍": daily_production_est_gas,
    "공취예상시간": gap_minutes,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 📌 누적 테이블 출력
st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# 📌 CSV 다운로드
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.8_Pro_Report.csv", mime='text/csv')
