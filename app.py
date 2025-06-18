import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 🔹 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 🔹 페이지 설정
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# 🔹 세션 로그 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# ================== 1부: 기준일자 / 기준시각 / 현재시각 입력 ==================
st.sidebar.header("① 기준일자 및 현재시각 입력")

# 1) 기준일자
base_date = st.sidebar.date_input("기준일자 선택", value=datetime.date.today())

# 2) 기준시각 입력 (예: "07:00")
base_time_str = st.sidebar.text_input("기준시각 입력 (예: 07:00)", value="07:00")

# 3) 현재시각 입력 (예: "19:44")
current_time_str = st.sidebar.text_input("현재시각 입력 (예: 19:44)", value=datetime.datetime.now().strftime("%H:%M"))

# 4) 시간 파싱 및 예외처리
try:
    base_hour, base_minute = map(int, base_time_str.strip().split(":"))
    base_datetime = datetime.datetime.combine(base_date, datetime.time(base_hour, base_minute))

    current_hour, current_minute = map(int, current_time_str.strip().split(":"))
    current_datetime = datetime.datetime.combine(base_date, datetime.time(current_hour, current_minute))

    # 현재시각이 기준시각보다 앞서면 → 익일로 간주
    if current_datetime < base_datetime:
        current_datetime += datetime.timedelta(days=1)

    # 경과시간(분) 계산
    elapsed_minutes = (current_datetime - base_datetime).total_seconds() / 60
    elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

except:
    st.error("❗ 시각 입력 오류: 07:00 또는 19:44 같은 HH:MM 형식으로 입력해주세요.")
    now = datetime.datetime.now()
    base_datetime = now.replace(hour=7, minute=0, second=0, microsecond=0)
    current_datetime = now
    elapsed_minutes = (current_datetime - base_datetime).total_seconds() / 60
    elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

# 5) 결과 출력
st.markdown(f"✅ **기준일시:** `{base_datetime.strftime('%Y-%m-%d %H:%M')}`")
st.markdown(f"✅ **현재시각:** `{current_datetime.strftime('%Y-%m-%d %H:%M')}`")
st.markdown(f"⏱️ **경과시간:** `{elapsed_minutes:.1f} 분`")

# ================== 2부: 정상조업 입력 ==================
st.sidebar.header("② 정상조업 기본입력")

# 🌾 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 🌾 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("너트코크(N.C) 장입량 (kg)", value=800.0)

# 🔍 O/C 비율 자동계산
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"📌 O/C 비율 (Ore/Coke): **{ore_coke_ratio:.2f}**")

# ⚙️ 철광석 성분
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 🔍 슬래그비율 자동계산 (예: O/C 비율 * 계수)
slag_ratio = ore_coke_ratio * 0.033
st.sidebar.markdown(f"📌 슬래그비율 자동계산 (ton/ton): **{slag_ratio:.2f}**")

# ⚙️ 조업기초 계수
reduction_efficiency = st.sidebar.number_input("기본 환원율 (정상)", value=1.0)

# 🔍 기본 환원율 보정 (슬래그계수 + 온도계수 등 없이 기본값 유지)
st.sidebar.markdown(f"📌 기본 환원율: **{reduction_efficiency:.2f}**")

# 💨 송풍량, 산소, 조습
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 (kg/thm)", value=170)

# 🌡️ 압력/온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 Tf (°C)", value=1515.0)

# 🔸 송풍 원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================
import datetime

st.sidebar.header("② 비상조업 보정입력")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False, key="abnormal_active")

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0), key="abnormal_start_time")
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0), key="abnormal_end_time")

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0, key="abnormal_charging_delay")
    abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정 (분)", value=300, key="abnormal_total_melting_delay")

    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume, key="abnormal_blast_volume")
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume, key="abnormal_oxygen_volume")
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual, key="abnormal_oxygen_enrichment")
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification, key="abnormal_humidification")
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate, key="abnormal_pci_rate")
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit, key="abnormal_wind_unit")

st.sidebar.header("③ 감풍·휴풍 보정입력")
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False, key="reduction_active")

if reduction_active:
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0), key="reduction_start_time")
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0), key="reduction_end_time")

    reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간 (분)", value=0, key="reduction_charging_delay")

    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm³/min)", value=blast_volume, key="reduction_blast_volume")
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm³/hr)", value=oxygen_volume, key="reduction_oxygen_volume")
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual, key="reduction_oxygen_enrichment")
    reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm³)", value=humidification, key="reduction_humidification")
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 (kg/thm)", value=pci_rate, key="reduction_pci_rate")
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위 (Nm³/t)", value=wind_unit, key="reduction_wind_unit")

# ========================== 4부: 환원효율 및 시간분할 생산량 계산 ==========================

# 계수 기반 환원효율
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

# 기본 환원효율 (정상조업 기준)
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * 0.9
)

# 구간별 시간(분)
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

# 비상조업 환원효율
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
    abnormal_temp_effect = temp_effect
    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
        abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * 0.9
    )
else:
    abnormal_reduction_eff = normal_reduction_eff

# 감풍조업 환원효율
if reduction_active:
    reduction_gas_effect = 1 + (reduction_blast_volume - 4000) / 8000
    reduction_oxygen_boost = 1 + (reduction_oxygen_enrichment / 10)
    reduction_humidity_effect = 1 - (reduction_humidification / 100)
    reduction_pci_effect = 1 + (reduction_pci_rate - 150) / 100 * 0.02
    reduction_temp_effect = temp_effect
    reduction_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * reduction_gas_effect *
        reduction_oxygen_boost * reduction_humidity_effect * pressure_boost * blow_pressure_boost *
        reduction_temp_effect * reduction_pci_effect * measured_temp_effect * 0.9
    )
else:
    reduction_reduction_eff = normal_reduction_eff

# 체류시간(비상조업시만 적용)
if abnormal_active:
    adjusted_elapsed_minutes = max(elapsed_minutes - abnormal_total_melting_delay, 0)
else:
    adjusted_elapsed_minutes = elapsed_minutes

# Charge 수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# Ore 및 Fe 환산
normal_ore = ore_per_charge * charge_rate * (normal_elapsed / 60)
abnormal_ore = ore_per_charge * charge_rate * (abnormal_elapsed / 60)
reduction_ore = ore_per_charge * charge_rate * (reduction_elapsed / 60)
after_ore = ore_per_charge * charge_rate * (after_elapsed / 60)

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
reduction_fe = reduction_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 생산량 계산 (AI 기반)
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
reduction_production = reduction_fe * reduction_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = (
    normal_production + abnormal_production + reduction_production + after_production
)

# ========================== 5부: 출선/실측 저선량/일일예상생산량 등 계산 ==========================

# --- 출선관리 입력부 (사이드바) ---
st.sidebar.header("④ 출선관리 입력")
closed_tap_count = st.sidebar.number_input("종료된 Tap 수", value=0, step=1)
avg_tap_time = st.sidebar.number_input("평균 TAP당 출선소요시간(분)", value=240.0)
avg_tap_speed = st.sidebar.number_input("평균 TAP당 출선속도(t/min)", value=4.5)

# 선행/후행 출선 실시간 경과
lead_elapsed_time = st.sidebar.number_input("선행출선시간(분)", value=0.0)
lead_output_speed = st.sidebar.number_input("선행출선속도(t/min)", value=avg_tap_speed)
lead_output_manual = st.sidebar.number_input("선행출선량(실측입력, ton)", value=0.0)
lead_output_ai = lead_elapsed_time * lead_output_speed

follow_elapsed_time = st.sidebar.number_input("후행출선시간(분)", value=0.0)
follow_output_speed = st.sidebar.number_input("후행출선속도(t/min)", value=avg_tap_speed)
follow_output_manual = st.sidebar.number_input("후행출선량(실측입력, ton)", value=0.0)
follow_output_ai = follow_elapsed_time * follow_output_speed

# 종료된 Tap 출선량 합계 (평균 속도 x 시간)
tap_total_output = closed_tap_count * avg_tap_time * avg_tap_speed / avg_tap_time if closed_tap_count > 0 else 0  # 혹은 평균용선량 입력가능

# 일일 실시간 출선량(직접입력)
realtime_tap_weight = st.sidebar.number_input("일일 실시간 출선량(ton)", value=0.0)

# 누적 출선량(실측+선행+후행+실시간)
total_tapped_hot_metal = tap_total_output + lead_output_manual + follow_output_manual + realtime_tap_weight

# --- 일일예상생산량 및 현재시각기준 누적예상생산량 ---
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_expected_production = wind_air_day / wind_unit
elapsed_ratio = elapsed_minutes / 1440  # 하루 1440분 기준
expected_till_now = daily_expected_production * elapsed_ratio

# --- 현재시각 기준 저선량 (핵심 공식) ---
# = 현재시각 누적생산량 - (Tap출선량합계+선행출선량+후행출선량+실시간출선)
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# --- 누적 슬래그 자동계산 (슬래그 비율 적용) ---
slag_ratio_applied = slag_ratio if slag_ratio > 0 else 0.33
accumulated_slag = total_tapped_hot_metal * slag_ratio_applied

# --- 참고: AI 기반 용선온도(Tf) 예측 공식 (참고지수) ---
pci_ton_hr = pci_rate * daily_expected_production / 1000
try:
    Tf_predict = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1000000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except:
    Tf_predict = 0
Tf_predict = max(Tf_predict, 1200)

# --- 저선 경보판 ---
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

# ========================== 6부: 주요 결과출력/AI추천/출선전략 ==========================

st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

# 생산량 요약
st.subheader("📈 일일 생산량 기준 예측")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재시각({input_now.strftime('%H:%M')})까지 누적 예상 생산량: {expected_till_now:.1f} ton")

# 누적 출선량 요약
st.subheader("💧 누적 출선량")
st.write(f"종료된 Tap 출선량 합계: {tap_total_output:.1f} ton")
st.write(f"선행 출선량(실측): {lead_output_manual:.1f} ton (AI예측: {lead_output_ai:.1f} ton)")
st.write(f"후행 출선량(실측): {follow_output_manual:.1f} ton (AI예측: {follow_output_ai:.1f} ton)")
st.write(f"실시간 출선량: {realtime_tap_weight:.1f} ton")
st.write(f"총 누적 출선량: {total_tapped_hot_metal:.1f} ton")

# 저선량·슬래그·AI Tf예상온도
st.subheader("🔥 저선/슬래그/AI 예측온도")
st.write(f"현재시각 기준 저선량(ton): {residual_molten:.1f}")
st.write(f"누적 슬래그량(자동계산): {accumulated_slag:.1f} ton")
st.write(f"AI 기반 Tf예상온도(참고): {Tf_predict:.1f} ℃")

# 실측 저선량 입력
measured_residual_molten = st.sidebar.number_input("실측 저선량(ton, 선택)", value=0.0)
st.write(f"실측 저선량(입력): {measured_residual_molten:.1f} ton")

# 저선 경보 출력
st.subheader("⚠️ 조업상태 진단")
st.write(f"조업상태: {status}")

# --- 출선추천 전략 ---
st.subheader("🚦 출선 전략 및 추천값")

# AI 비트경/차기 출선간격 추천 로직
if residual_molten < 100:
    tap_diameter = 43
    next_tap_interval = "15~20분"
elif residual_molten < 150:
    tap_diameter = 45
    next_tap_interval = "10~15분"
elif residual_molten < 200:
    tap_diameter = 48
    next_tap_interval = "5~10분"
else:
    tap_diameter = 50
    next_tap_interval = "즉시(0~5분)"

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"추천 차기 출선간격: {next_tap_interval}")

# --- 선행 예상 폐쇄시간, AI 공취예상 잔여시간 ---
# (선행/후행 출선관리 → 잔여시간 계산, 소요시간 = 출선량/출선속도)
if lead_output_speed > 0:
    lead_expected_close_time = lead_output_manual / lead_output_speed
else:
    lead_expected_close_time = 0
if follow_output_speed > 0:
    follow_expected_close_time = follow_output_manual / follow_output_speed
else:
    follow_expected_close_time = 0

# AI 공취예상 잔여시간: 잔여 출선량(선행 목표) / 선행출선속도
lead_target = avg_tap_time * avg_tap_speed / avg_tap_time if avg_tap_speed > 0 else 0
lead_remain = max(lead_target - lead_output_manual, 0)
if lead_output_speed > 0:
    ai_gap_minutes = lead_remain / lead_output_speed
else:
    ai_gap_minutes = 0

st.write(f"선행 예상 폐쇄시간(분): {lead_expected_close_time:.1f}")
st.write(f"AI 공취예상 잔여시간(분): {ai_gap_minutes:.1f}")

# ========================== 7부: 실시간 용융물 수지 시각화 ==========================

st.subheader("📊 실시간 용융물 수지 시각화")

# 시계열 시간축 (예: 15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량 시계열 (송풍기반 예상생산량 * 시점 비율)
gen_series = []
for t in time_labels:
    prod = daily_expected_production * (t / 1440)
    gen_series.append(prod)

# 누적 출선량 시계열 (실측+AI, 현재시각까지)
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선 시계열 (예상 누적생산량 - 누적 출선량)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 그래프
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)", linewidth=2)
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)", linestyle='--')
plt.plot(time_labels, residual_series, label="저선량 (ton)", linestyle=':')
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 용융물 수지 시각화")
plt.legend()
plt.grid(True)

st.pyplot(plt)

# ========================== 8부: 누적 조업 리포트 기록 ==========================

st.subheader("📋 누적 조업 리포트 기록")

# 주요 기록 항목 딕셔너리 생성
record = {
    "기준일자": base_date.strftime('%Y-%m-%d'),
    "기준시작시각": today_start.strftime('%Y-%m-%d %H:%M'),
    "기준입력일시": user_start.strftime('%Y-%m-%d %H:%M'),
    "입력현재시각": user_now.strftime('%Y-%m-%d %H:%M'),
    "일일예상생산량(t/day)": daily_expected_production,
    "현재시각누적생산량(t)": expected_till_now,
    "누적출선량(t)": total_tapped_hot_metal,
    "현재시각저선량(t)": residual_molten,
    "슬래그량(t)": accumulated_slag,
    "선행출선량(t)": lead_tap_weight,
    "후행출선량(t)": follow_tap_weight,
    "종료Tap수": closed_tap_count,
    "Tap당평균출선(ton)": avg_tap_weight,
    "평균TAP출선소요(분)": avg_tap_time,
    "평균TAP출선속도(t/min)": avg_tap_speed,
    "현재경과시간(min)": elapsed_minutes,
    "조업상태": status,
    "AI기반_Tf예상온도(℃)": Tf_predict,
}

# 세션에 누적 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)

# 500건 초과 시 oldest 삭제
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 데이터프레임 표시
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')
