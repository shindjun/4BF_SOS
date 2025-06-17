# ========================== 1부: 초기 설정 ==========================
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(
    page_title="BlastTap 10.3 Pro — AI 조업엔진",
    layout="wide"
)

# 앱 제목
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# 세션 로그 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 계산 (07시 기준 교대 시간 설정)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

# 기준 시각 = 오늘 07:00
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# 경과 시간 계산 (단위: 분)
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)  # 최소 60분 ~ 최대 1440분 범위 제한

# ========================== 2부: 정상조업 입력부 ==========================
st.sidebar.header("① 정상조업 기본입력")

# 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)

# O/C 비율 (자동 계산)
ore_coke_ratio = ore_per_charge / coke_per_charge if coke_per_charge else 0
st.sidebar.markdown(f"🔍 O/C 비율: **{ore_coke_ratio:.2f}**")

# 철광석 성분
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 슬래그 비율은 참고용 표시
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 기본 조업지수
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍 및 산소 입력
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36961.0)

# 산소부화율 수동입력 및 자동계산 병행
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)
# 자동 산소부화율 계산 (표시만)
auto_oxygen_enrichment = (oxygen_volume / (60 * blast_volume) * 100) if blast_volume > 0 else 0
st.sidebar.markdown(f"🔎 자동 산소부화율 계산: **{auto_oxygen_enrichment:.2f}%**")

# 조습 및 미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

# 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)

# 실측 온도
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

# 보정계수 및 체류시간
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
total_melting_delay = st.sidebar.number_input("체류시간 보정 (분)", value=300)

# 송풍원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================
st.sidebar.header("② 비상조업 보정입력")

# 비상조업 체크박스
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

# 감풍·휴풍 보정
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

# ========================== 4부: 시간분할 환원효율 및 생산량 계산 ==========================

# 정상조업 기준 환원효율 계산
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

normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9
)

# 시간분할: 정상/비상/감풍
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
    after_elapsed = 0

if reduction_active:
    reduction_start_dt = datetime.datetime.combine(base_date, reduction_start_time)
    reduction_end_dt = datetime.datetime.combine(base_date, reduction_end_time)
    normal_elapsed = min((reduction_start_dt - today_start).total_seconds() / 60, normal_elapsed)
    reduction_elapsed = max(min((reduction_end_dt - reduction_start_dt).total_seconds() / 60,
                                elapsed_minutes - (normal_elapsed + abnormal_elapsed)), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed + reduction_elapsed), 0)

# 비상조업 환원효율 계산
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
    abnormal_temp_effect = temp_effect

    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
        abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor * 0.9
    )
else:
    abnormal_reduction_eff = normal_reduction_eff

# 감풍·휴풍 환원효율 계산
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

# 시간가중 장입시간 반영
adjusted_elapsed_minutes = normal_elapsed + abnormal_elapsed + reduction_elapsed + after_elapsed
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# Fe 환산 장입량
normal_ore = ore_per_charge * charge_rate * (normal_elapsed / 60)
abnormal_ore = ore_per_charge * charge_rate * (abnormal_elapsed / 60)
reduction_ore = ore_per_charge * charge_rate * (reduction_elapsed / 60)
after_ore = ore_per_charge * charge_rate * (after_elapsed / 60)

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
reduction_fe = reduction_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 생산량 계산 (ton)
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
reduction_production = reduction_fe * reduction_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = normal_production + abnormal_production + reduction_production + after_production

# 체류시간 보정
if adjusted_elapsed_minutes > total_melting_delay:
    active_minutes = adjusted_elapsed_minutes - total_melting_delay
    effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes)
else:
    effective_production_ton = 0

# 누적 환원 Fe 기준 생산량
total_production_ton = effective_production_ton

# ========================== 5부: 실측출선 + 저선량 + 슬래그 + 실측 저선량 입력 ==========================

st.sidebar.header("④ 실측출선 데이터 입력")

# TAP당 평균 출선량 및 종료 TAP 수 입력
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=5)
tap_total_output = fixed_avg_tap_output * completed_taps

# 선행/후행 출선 진행 입력
st.sidebar.header("⑤ 실시간 선행/후행 출선 현황")

lead_elapsed_time = st.sidebar.number_input("선행 경과시간 (분)", value=90.0)
follow_elapsed_time = st.sidebar.number_input("후행 경과시간 (분)", value=30.0)
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.5)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.5)

# 실시간 선행/후행 출선량 계산
lead_output = lead_elapsed_time * lead_speed
follow_output = follow_elapsed_time * follow_speed

# 누적 용선출선량 계산: TAP + 선행 + 후행
total_tapped_hot_metal = tap_total_output + lead_output + follow_output

# 누적 슬래그배출량 자동계산 (참고용) — 슬래그 비율은 따로 수지에는 반영하지 않음
total_tapped_slag = total_tapped_hot_metal / slag_ratio if slag_ratio > 0 else 0

# AI 이론 생산량 대비 저선량 계산 (ton)
residual_molten = total_production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / total_production_ton) * 100 if total_production_ton > 0 else 0

# 실측 저선량 수동입력
measured_residual_molten = st.sidebar.number_input("실측 저선량 (ton)", value=45.0)

# AI-실측 수지편차
residual_gap = residual_molten - measured_residual_molten

# 상태 메시지 출력
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ========================== 6부: AI 출선전략 + 공취예상시간 + 출선소요시간 ==========================

st.header("🧠 AI 기반 출선 전략 및 시간예측")

# TAP당 평균 출선량 계산 (참고용)
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio if slag_ratio > 0 else 0

# AI 추천 비트경 (잔류 용선량 기준)
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# AI 추천 차기 출선간격 (저선율 기반)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 공취예상시간 계산
lead_target = fixed_avg_tap_output  # 목표 출선량
lead_remain = max(lead_target - lead_output, 0)  # 잔여 출선량
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 공취(후행→선행 충돌시간) 간격
pure_gap = lead_remain_time - follow_elapsed_time
gap_minutes = max(pure_gap, 0)

# 선행 1Tap 예상 출선소요시간
expected_tap_time = lead_target / lead_speed if lead_speed > 0 else 0

# ========================== 7부: 용선온도 예측 + 일일예상생산량 계산 ==========================

st.header("🔥 용선온도 예측 및 일일예상생산량")

# 송풍원단위 기반 일일 생산량 (AI 이론식)
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_production_by_wind = wind_air_day / wind_unit if wind_unit > 0 else 0

# 환원효율 기반 보조 일일 생산량
if elapsed_charges > 0:
    daily_production_est = (
        ore_per_charge * elapsed_charges * (tfe_percent / 100) * normal_reduction_eff
    ) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est = 0

# 미분탄 ton/hr 환산 (용선온도에 반영)
pci_ton_hr = pci_rate * daily_production_by_wind / 1000

# 안정화된 용선온도 예측 공식
try:
    Tf_predict = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1000000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except:
    Tf_predict = 0  # 계산 예외보호

# 용선온도 하한선 보정
Tf_predict = max(Tf_predict, 1200)

# ========================== 8부: AI 실시간 리포트 출력 ==========================

st.header("📊 BlastTap 10.3 Pro — AI 실시간 조업 리포트")

# 생산량 요약
st.subheader("🔧 생산량 및 환원 효율 요약")
st.write(f"AI 이론생산량 (누적): {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"누적 선철생산량 (총환원량 기준): {total_production_ton:.1f} ton")
st.write(f"일일예상생산량 (송풍원단위 기반): {daily_production_by_wind:.1f} ton/day")
st.write(f"일일예상생산량 (환원효율 기반 참고): {daily_production_est:.1f} ton/day")

# 출선량 및 슬래그
st.subheader("🚚 출선 현황")
st.write(f"TAP 기준 실측 출선량: {tap_total_output:.1f} ton")
st.write(f"선행 실시간 출선량: {lead_output:.1f} ton")
st.write(f"후행 실시간 출선량: {follow_output:.1f} ton")
st.write(f"누적 용선출선량 (총계): {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산 참고용): {total_tapped_slag:.1f} ton")

# 저선량 및 수지오차
st.subheader("🔥 저선 수지 분석")
st.write(f"현재 저선량 (AI 계산): {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"실측 저선량 입력값: {measured_residual_molten:.1f} ton")
st.write(f"AI-실측 저선 수지편차: {residual_gap:.1f} ton")
st.write(f"조업상태: {status}")

# 용선온도 예측
st.subheader("🌡️ 용선온도 예측")
st.write(f"AI 예측 용선온도 (Tf 보정): {Tf_predict:.1f} °C")

# 출선 전략
st.subheader("🧠 출선 전략 및 공취 분석")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"선행 잔여 출선시간: {lead_remain_time:.1f} 분")
st.write(f"AI 공취예상시간: {gap_minutes:.1f} 분")
st.write(f"예상 1Tap 출선소요시간: {expected_tap_time:.1f} 분")

# ========================== 9부: 실시간 시각화 + 누적 리포트 기록 ==========================

st.header("📊 실시간 용융물 수지 시각화")

# 시간축 생성 (15분 단위 시계열)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

# 누적 생산량 시뮬레이션 시계열
gen_series = []
for t in time_labels:
    ore_t = ore_per_charge * (charge_rate * (t / 60))
    fe_t = ore_t * (tfe_percent / 100)
    prod_t = fe_t * normal_reduction_eff

    if t > total_melting_delay:
        prod_t *= ((t - total_melting_delay) / t)
    else:
        prod_t = 0

    prod_t = min(prod_t, total_production_ton)
    gen_series.append(prod_t)

# 누적 출선량 시계열
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선량 시계열
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화
plt.figure(figsize=(10, 6))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")

plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 추적")
plt.ylim(0, total_production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.grid()
plt.legend()

st.pyplot(plt)

# ========================== 리포트 누적 기록 ==========================
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "누적출선량": total_tapped_hot_metal,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "송풍원단위생산량": daily_production_by_wind,
    "공취예상시간": gap_minutes,
    "Tf예상온도": Tf_predict,
    "AI-실측저선수지차": residual_gap,
    "조업상태": status
}

st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 리포트 테이블 및 다운로드
st.header("📋 누적 조업 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Pro_Report.csv", mime='text/csv')
