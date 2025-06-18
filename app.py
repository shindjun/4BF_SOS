import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 폰트 설정 (한글 안정화)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 초기설정
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# 세션 리포트 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 현재 시각 입력 기반 경과 시간 계산
st.sidebar.header("⏱ 현재 시간 기준 설정")
user_time = st.sidebar.time_input("현재 시간 입력", value=datetime.datetime.now().time())
user_now = datetime.datetime.combine(datetime.date.today(), user_time)

# 기준일자 (07시 교대기준)
if user_now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (user_now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

# ========================== 2부: 정상조업 기본입력 ==========================

st.sidebar.header("① 정상조업 기본입력")

# 장입속도 및 장입량
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke = st.sidebar.number_input("너트코크 장입량 (kg)", value=0.0)

# O/C 비율 입력
ore_coke_ratio = st.sidebar.number_input("O/C 비율", value=5.0)

# 철광석 성분
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 슬래그 비율 (참고용)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 조업지수 및 용해능력
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍 및 산소부화 입력
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

# 조습 및 미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

# 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

# 송풍원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================

# 비상조업 보정 입력
st.sidebar.header("② 비상조업 보정입력")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))

    # 체류시간 보정 이동 (정상조업에서 삭제 후 여기로 이동)
    total_melting_delay = st.sidebar.number_input("체류시간 보정 (분)", value=300)

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

# 감풍·휴풍 보정 입력
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

# 환원효율 영향요인 계산
size_effect = (20 / 20 + 60 / 60) / 2  # 형상영향 상수
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

# K 계수는 비상조업 시에만 적용
K_factor_applied = K_factor if abnormal_active else 1.0

# 정상 환원효율 계산
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor_applied * 0.9
)

# 시간 분할 처리
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

# 비상조업 환원효율
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
    abnormal_temp_effect = temp_effect  # 동일
    abnormal_measured_temp = measured_temp_effect
    abnormal_K = K_factor
    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost *
        blow_pressure_boost * abnormal_temp_effect * abnormal_pci_effect *
        abnormal_measured_temp * abnormal_K * 0.9
    )
else:
    abnormal_reduction_eff = normal_reduction_eff

# 감풍 환원효율
if reduction_active:
    reduction_gas_effect = 1 + (reduction_blast_volume - 4000) / 8000
    reduction_oxygen_boost = 1 + (reduction_oxygen_enrichment / 10)
    reduction_humidity_effect = 1 - (reduction_humidification / 100)
    reduction_pci_effect = 1 + (reduction_pci_rate - 150) / 100 * 0.02
    reduction_temp_effect = temp_effect
    reduction_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * reduction_gas_effect *
        reduction_oxygen_boost * reduction_humidity_effect * pressure_boost *
        blow_pressure_boost * reduction_temp_effect * reduction_pci_effect *
        measured_temp_effect * K_factor_applied * 0.9
    )
else:
    reduction_reduction_eff = normal_reduction_eff

# 시간 가중 누적 장입시간
adjusted_elapsed_minutes = (
    normal_elapsed + abnormal_elapsed + reduction_elapsed + after_elapsed
)

# 누적 charge 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# 각 구간 철광석 투입량 및 환원 Fe 계산
def fe_calc(mins, eff):
    ore = ore_per_charge * charge_rate * (mins / 60)
    fe = ore * (tfe_percent / 100)
    return fe * eff

normal_production = fe_calc(normal_elapsed, normal_reduction_eff)
abnormal_production = fe_calc(abnormal_elapsed, abnormal_reduction_eff)
reduction_production = fe_calc(reduction_elapsed, reduction_reduction_eff)
after_production = fe_calc(after_elapsed, normal_reduction_eff)

# 총 생산량
production_ton_ai = (
    normal_production + abnormal_production + reduction_production + after_production
)

# ========================== 5부: 실측출선 + 저선량 + 슬래그 + 실측 저선량 입력 ==========================
st.sidebar.header("④ 실측출선 데이터 입력")

# TAP 기준 출선량
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=5)
tap_total_output = fixed_avg_tap_output * completed_taps

# 선행/후행 출선 (소요시간 기반 계산)
st.sidebar.header("⑤ 실시간 선행/후행 출선 현황")

lead_duration = st.sidebar.number_input("선행 출선 소요시간 (분)", value=90.0)
follow_duration = st.sidebar.number_input("후행 출선 소요시간 (분)", value=30.0)

lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.5)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.5)

lead_output = lead_duration * lead_speed
follow_output = follow_duration * follow_speed

# 누적 용선출선량 (TAP + 선행 + 후행)
total_tapped_hot_metal = tap_total_output + lead_output + follow_output

# 누적 슬래그출선량 (참고용 자동계산)
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# AI 계산 저선량 (용선 기준, 슬래그 미포함)
residual_molten = total_production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / total_production_ton) * 100 if total_production_ton > 0 else 0

# 실측 저선량 수동입력
measured_residual_molten = st.sidebar.number_input("실측 저선량 (ton)", value=45.0)

# AI-실측 저선량 차이
residual_gap = residual_molten - measured_residual_molten

# 조업상태 경고
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ========================== 6부: AI 출선전략 + 공취예상시간 + 출선소요시간 ==========================

st.header("📈 출선 전략 및 공취 예상")

# 평균 출선량 (TAP 기준 참고용)
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# AI 추천 비트경 로직 (저선량 기준)
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# AI 추천 차기 출선 간격 (저선율 기반)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 공취 예상 시간 계산
lead_target = fixed_avg_tap_output
lead_remain = max(lead_target - lead_output, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 후행 출선시작 기준으로 남은 시간
pure_gap = lead_remain_time - follow_elapsed_time
gap_minutes = max(pure_gap, 0)

# 예상 1Tap 출선 소요시간
expected_tap_time = lead_target / lead_speed if lead_speed > 0 else 0

# 선행 폐쇄 후 차기 출선 간격 입력 (참고용)
user_defined_tap_gap = st.sidebar.number_input("선행 폐쇄 후 차기 출선간격 (분)", value=15.0)

# ========================== 7부: 예상 일일 생산량 계산 (송풍 및 환원효율 기반) ==========================

st.header("📊 일일 예상 생산량 요약")

# 송풍 및 산소 부화 기준 생산공기 총량
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)

# 송풍원단위 기반 생산량 (ton/day)
try:
    daily_production_by_wind = wind_air_day / wind_unit
except ZeroDivisionError:
    daily_production_by_wind = 0

# 환원효율 기반 생산량 (ton/day)
if adjusted_elapsed_minutes > 0:
    daily_production_est = (ore_per_charge * elapsed_charges * (tfe_percent / 100) * normal_reduction_eff) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est = 0

# 현재시각 기준 누적 생산량 (송풍 기반)
try:
    expected_cumulative_production = daily_production_by_wind * (adjusted_elapsed_minutes / 1440)
except:
    expected_cumulative_production = 0

# 결과 출력
st.write(f"예상 일일생산량 (송풍기준): {daily_production_by_wind:.1f} ton/day")
st.write(f"예상 일일생산량 (환원효율 기반): {daily_production_est:.1f} ton/day")
st.write(f"예상 누적생산량 (현재시각 기준): {expected_cumulative_production:.1f} ton")

# ========================== 8부: AI 실시간 조업 리포트 출력 ==========================

st.header("📋 BlastTap 10.3 Pro — AI 실시간 조업 리포트")

# 생산량 요약
st.subheader("✅ 생산량 요약")
st.write(f"예상 누적생산량 (현재시각 기준): {expected_cumulative_production:.1f} ton")
st.write(f"종료된 Tap 기준 출선량: {tap_total_output:.1f} ton")
st.write(f"선행 출선량: {lead_output:.1f} ton")
st.write(f"후행 출선량: {follow_output:.1f} ton")
st.write(f"누적 출선량 (합계): {total_tapped_hot_metal:.1f} ton")

# 저선량 계산
residual_molten = expected_cumulative_production - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / expected_cumulative_production) * 100 if expected_cumulative_production > 0 else 0

# 실측 저선량 입력 대비 오차
residual_gap = residual_molten - measured_residual_molten

# 저선 경보 상태
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# 저선 정보 출력
st.subheader("🧯 저선 수지 추정")
st.write(f"AI 저선량 (예측): {residual_molten:.1f} ton")
st.write(f"실측 저선량 입력값: {measured_residual_molten:.1f} ton")
st.write(f"AI-실측 저선 수지 차이: {residual_gap:.1f} ton")
st.write(f"현재 조업 상태: {status}")

# ========================== 9부: 실시간 시각화 + 누적 리포트 기록 ==========================

st.header("📊 실시간 용융물 수지 시각화")

# 시간축 생성 (15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량 시뮬레이션 (예측)
simulated_production = []
for t in time_labels:
    ore_sim = ore_per_charge * charge_rate * (t / 60)
    fe_sim = ore_sim * (tfe_percent / 100)
    prod_sim = fe_sim * normal_reduction_eff
    simulated_production.append(prod_sim)

# 동일한 시간 기준 누적 출선 및 저선 시계열 생성
tapped_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(p - total_tapped_hot_metal, 0) for p in simulated_production]

# 시각화 플롯
plt.figure(figsize=(10, 6))
plt.plot(time_labels, simulated_production, label="누적 생산량 (ton)")
plt.plot(time_labels, tapped_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="예상 저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지 시뮬레이션")
plt.grid()
plt.legend()
st.pyplot(plt)

# ========================== 리포트 누적 저장 및 다운로드 ==========================
st.header("📑 누적 조업 리포트 기록")

record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "예상누적생산량": expected_cumulative_production,
    "누적출선량": total_tapped_hot_metal,
    "AI저선량": residual_molten,
    "실측저선": measured_residual_molten,
    "AI-실측오차": residual_gap,
    "저선율(%)": residual_rate,
    "조업상태": status
}

# 로그 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []

st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 데이터프레임 생성 및 다운로드
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_Report_Log.csv", mime='text/csv')
