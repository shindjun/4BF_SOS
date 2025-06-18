import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# ----------- 1부: 환경설정 및 기준일시/기준시각 입력 -------------
# 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 및 타이틀
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# 세션 로그 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# ========================== 기준일자/시각 입력 ==========================
st.sidebar.header("🗓️ 기준일자/기준일시 입력")

# 기준일자 (예: 2025-06-18)
base_date = st.sidebar.date_input("기준일자", value=datetime.date.today())

# 기준 시작시각 (예: 07:00)
default_time = datetime.time(7, 0)
start_time = st.sidebar.time_input("기준 시작시각", value=default_time)

# 기준 종료시각 (예: 07:00 다음날)
end_time = st.sidebar.time_input("기준 종료시각", value=default_time)

# 오늘의 기준시각대
today_start = datetime.datetime.combine(base_date, start_time)
# 기준종료시각이 당일 7시와 같으면, 종료는 다음날 7시로 간주
if end_time == start_time:
    today_end = today_start + datetime.timedelta(days=1)
else:
    today_end = datetime.datetime.combine(base_date, end_time)
# 현재시각 직접입력 (예: 19:44)
now_time = st.sidebar.time_input("현재 시각 입력", value=datetime.datetime.now().time())
# 사용자가 입력한 현재시각 기준으로 now_datetime 설정
now = datetime.datetime.combine(base_date, now_time)
if now < today_start:
    now = now + datetime.timedelta(days=1)  # 0~7시 입력시 익일로 보정

# 경과분 자동 계산 (07:00 ~ 현재 입력시각)
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

st.info(f"기준일시: {today_start.strftime('%Y-%m-%d %H:%M')} ~ {today_end.strftime('%Y-%m-%d %H:%M')}")
st.info(f"현재시각: {now.strftime('%Y-%m-%d %H:%M')} (경과분: {int(elapsed_minutes)}분)")

# ========================== 2부: 정상조업 입력부 ==========================
st.sidebar.header("① 정상조업 기본입력")

# 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)

# O/C 비율 (자동계산)
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"**O/C 비율:** {ore_coke_ratio:.2f}")

# 철광석 성분 및 슬래그비율
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 조업지수 및 용해능력
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)

# 송풍·산소
blast_volume = st.sidebar.number_input("송풍량 (Nm3/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm3/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

# 조습·미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm3)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

# 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

# 송풍 원단위 (Nm3/t)
wind_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================

# 비상조업 보정 입력
st.sidebar.header("② 비상조업 보정입력")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정 (분)", value=300)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm3/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm3/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm3)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm3/t)", value=wind_unit)

# 감풍·휴풍 보정 입력
st.sidebar.header("③ 감풍·휴풍 보정입력")
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)

if reduction_active:
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0))
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0))
    reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간 (분)", value=0)
    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm3/min)", value=blast_volume)
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm3/hr)", value=oxygen_volume)
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual)
    reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm3)", value=humidification)
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 (kg/thm)", value=pci_rate)
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위 (Nm3/t)", value=wind_unit)

# ========================== 4부: 환원효율 계산 및 시간분할 생산량 계산 ==========================

# 환원효율 관련 계수 계산
size_effect = (20 / 20 + 60 / 60) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05  # ← 정상적으로 입력된 melting_capacity 사용
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

# 시간 분할: 정상-비상-감풍 구간 구분
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
    abnormal_temp_effect = temp_effect  # 풍온 동일 적용
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

# 체류시간 적용: 비상조업 체크 시만 적용
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

# ========================== 5부: 실측 출선 및 저선·슬래그량 계산 ==========================

# [출선 입력] (사이드바에서 입력)
closed_tap_count = st.sidebar.number_input("종료된 TAP 수", min_value=0, value=0)
avg_tap_time = st.sidebar.number_input("평균 TAP당 출선소요시간 (분)", min_value=1, value=250)
avg_tap_speed = st.sidebar.number_input("평균 TAP당 출선속도 (ton/min)", min_value=1.0, value=4.5)

# 종료된 Tap 출선량(ton)
closed_tap_output = st.sidebar.number_input("종료된 Tap 출선량 (ton)", min_value=0.0, value=0.0)

# 선행·후행 출선시간 및 속도
lead_elapsed_time = st.sidebar.number_input("선행출선경과시간 (분)", min_value=0, value=0)
lead_speed = st.sidebar.number_input("선행출선속도 (ton/min)", min_value=0.0, value=avg_tap_speed)
lead_output_ai = lead_elapsed_time * lead_speed
lead_output_real = st.sidebar.number_input("선행출선량(실측값, ton)", min_value=0.0, value=lead_output_ai)

follow_elapsed_time = st.sidebar.number_input("후행출선경과시간 (분)", min_value=0, value=0)
follow_speed = st.sidebar.number_input("후행출선속도 (ton/min)", min_value=0.0, value=avg_tap_speed)
follow_output_ai = follow_elapsed_time * follow_speed
follow_output_real = st.sidebar.number_input("후행출선량(실측값, ton)", min_value=0.0, value=follow_output_ai)

# 일일 실시간 출선량(기타 보충입력)
realtime_tap_output = st.sidebar.number_input("일일 실시간 용선 출선량 (ton)", min_value=0.0, value=0.0)

# [누적 출선량]
# 총 누적 출선량 = 종료된 + 선행 + 후행 + 실시간
total_tapped_hot_metal = closed_tap_output + lead_output_real + follow_output_real + realtime_tap_output

# [예상 누적 생산량] (현재시각 기반)
elapsed_ratio = elapsed_minutes / 1440  # 하루 1440분 기준
daily_expected_production = (blast_volume * 1440 + oxygen_volume * 24 / 0.21) / wind_unit
expected_till_now = daily_expected_production * elapsed_ratio

# [저선량]
# 현재시각 기준 저선량 = 현재시각 누적 예상 생산량 - 현재시각 누적 출선량
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# [슬래그 자동계산] (누적 용선출선량 × 슬래그비율)
accumulated_slag = total_tapped_hot_metal / slag_ratio if slag_ratio > 0 else 0

# [저선 경보]
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

# ========================== 6부: 결과 출력 및 추천·진단 ==========================

# 결과 요약 표시
st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

st.subheader("📈 일일 생산량 기준 예측")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재시각 누적 예상생산량: {expected_till_now:.1f} ton")

st.subheader("💧 누적 출선량")
st.write(f"종료된 Tap 출선량: {closed_tap_output:.1f} ton")
st.write(f"선행 출선량(실측): {lead_output_real:.1f} ton (AI예측: {lead_output_ai:.1f} ton)")
st.write(f"후행 출선량(실측): {follow_output_real:.1f} ton (AI예측: {follow_output_ai:.1f} ton)")
st.write(f"일일 실시간 출선량: {realtime_tap_output:.1f} ton")
st.write(f"총 누적 출선량: {total_tapped_hot_metal:.1f} ton")

st.subheader("🔥 저선 및 슬래그량 추정")
st.write(f"현재시각 기준 저선량: {residual_molten:.1f} ton")
st.write(f"누적 슬래그 출선량 (자동계산): {accumulated_slag:.1f} ton")
st.write(f"조업상태: {status}")

# ========================== 7부: 출선관리 추천/진단 (비트경, 차기출선, 공취시간) ==========================

# 추천 비트경 (예시 로직, 조정가능)
if residual_molten < 100:
    tap_diameter = 43
elif residual_molten < 150:
    tap_diameter = 45
else:
    tap_diameter = 48

# 선행 Tap 종료 후, 차기 출선간격 예측
if avg_tap_speed > 0:
    next_tap_interval = lead_output_real / avg_tap_speed
else:
    next_tap_interval = 0

# AI 공취 예상 잔여시간: (예시, 더 정교한 예측 로직 가능)
if lead_speed > 0:
    lead_expected_close_time = lead_output_real / lead_speed
    ai_gap_minutes = max(lead_expected_close_time - lead_elapsed_time, 0)
else:
    ai_gap_minutes = 0

st.subheader("⚙️ 출선전략/추천")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"선행 예상 폐쇄시간: {lead_expected_close_time:.1f} 분")
st.write(f"AI 공취예상 잔여시간: {ai_gap_minutes:.1f} 분")
st.write(f"차기 출선간격(예상): {next_tap_interval:.1f} 분")

# ========================== 8부: AI 기반 Tf예상온도 산출 (참고지수) ==========================
# 예시용 AI 예측 Tf 계산식 (산출 공식은 조정 가능)
try:
    pci_ton_hr = pci_rate * daily_expected_production / 1000
    Tf_predict = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1000000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except Exception:
    Tf_predict = 0
Tf_predict = max(Tf_predict, 1200)  # 하한선 적용

st.subheader("🌡️ AI 기반 Tf예상온도 (참고)")
st.write(f"AI 기반 Tf예상온도: {Tf_predict:.1f} °C")

# ========================== 9부: 실시간 시각화 ==========================
st.subheader("📊 실시간 용융물 수지 시각화")

time_labels = list(range(0, int(elapsed_minutes) + 1, 15))
gen_series = [daily_expected_production * (t / 1440) for t in time_labels]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# ========================== 10부: 누적 리포트 기록 ==========================
st.subheader("📋 누적 조업 리포트 기록")
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "예상일일생산량(t/day)": daily_expected_production,
    "현재누적생산량(t)": expected_till_now,
    "누적출선량(t)": total_tapped_hot_metal,
    "현재저선량(t)": residual_molten,
    "누적슬래그량(t)": accumulated_slag,
    "조업상태": status,
    "선행출선(ton)": lead_output_real,
    "후행출선(ton)": follow_output_real,
    "종료된Tap출선(ton)": closed_tap_output,
    "실시간출선(ton)": realtime_tap_output,
    "추천비트경": tap_diameter,
    "선행폐쇄예상시간(분)": lead_expected_close_time,
    "AI공취예상잔여시간(분)": ai_gap_minutes,
    "Tf예상온도": Tf_predict,
    "경과시간(min)": elapsed_minutes,
}
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

st.markdown("---")
st.info("💡 조업 정보는 07시 기준 초기화, 실시간 출선 및 저선·추천·시각화 자동 제공.")

