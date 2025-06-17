# ========================== 1부: 기본 설정 및 라이브러리 ==========================
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 설정 (OS별)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# Streamlit 페이지 설정
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# 세션 로그 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 설정 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 60)

# ========================== 2부: 정상조업 기본입력 ==========================
st.sidebar.header("① 정상조업 기본입력")

# 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge  # hourly charges

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)

# 철광석 성분
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 슬래그 비율 (표시용)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25, help="참고용. 저선량 계산에는 포함되지 않습니다.")

# 기본 조업지수
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍 및 산소 조건
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

# 보정계수 및 체류시간 설정
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
total_melting_delay = st.sidebar.number_input("체류시간 보정 (분)", value=300)

# 송풍원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================
# --- 비상조업 보정 입력 ---
st.sidebar.header("② 비상조업 보정입력")
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

# --- 감풍·휴풍 보정 입력 ---
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

# ========================== 4부: 환원효율 및 생산량 계산 ==========================

# 정상조업 환원효율 요소 계산
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

# 정상 환원효율 종합 계산
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9
)

# 시간 분할 계산
normal_elapsed = elapsed_minutes
abnormal_elapsed = 0
reduction_elapsed = 0

# 비상 시간 계산
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)
    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60,
                               elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
    after_elapsed = 0

# 감풍 시간 계산
if reduction_active:
    reduction_start_dt = datetime.datetime.combine(base_date, reduction_start_time)
    reduction_end_dt = datetime.datetime.combine(base_date, reduction_end_time)
    normal_elapsed = min((reduction_start_dt - today_start).total_seconds() / 60, normal_elapsed)
    reduction_elapsed = max(min((reduction_end_dt - reduction_start_dt).total_seconds() / 60,
                                elapsed_minutes - (normal_elapsed + abnormal_elapsed)), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed + reduction_elapsed), 0)

# 비상 환원효율 계산
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

# 감풍 환원효율 계산
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

# 시간 가중 전체 조업시간
adjusted_elapsed_minutes = normal_elapsed + abnormal_elapsed + reduction_elapsed + after_elapsed

# 장입 속도 기반 Charge 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# Ore 투입량 및 Fe 환산
def fe_calc(minutes):  
    ore = ore_per_charge * charge_rate * (minutes / 60)
    return ore * (tfe_percent / 100)

normal_fe = fe_calc(normal_elapsed)
abnormal_fe = fe_calc(abnormal_elapsed)
reduction_fe = fe_calc(reduction_elapsed)
after_fe = fe_calc(after_elapsed)

# 생산량 계산
normal_prod = normal_fe * normal_reduction_eff
abnormal_prod = abnormal_fe * abnormal_reduction_eff
reduction_prod = reduction_fe * reduction_reduction_eff
after_prod = after_fe * normal_reduction_eff

# 최종 AI 환원 생산량
production_ton_ai = normal_prod + abnormal_prod + reduction_prod + after_prod

# ========================== 5부: 실측출선 + 저선량 + 슬래그 ==========================

st.sidebar.header("⑤ 실측 출선 데이터 입력")

# TAP 기반 실측 출선량
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균용선출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=5)
tap_total_output = fixed_avg_tap_output * completed_taps

# 선행/후행 실시간 출선현황 입력
st.sidebar.header("⑥ 실시간 선행/후행 출선량 입력")

lead_elapsed_time = st.sidebar.number_input("선행 출선 경과시간 (분)", value=90.0)
follow_elapsed_time = st.sidebar.number_input("후행 출선 경과시간 (분)", value=30.0)
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.5)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.5)

lead_output = lead_elapsed_time * lead_speed
follow_output = follow_elapsed_time * follow_speed

# 누적 출선량 = TAP + 선행 + 후행
total_tapped_hot_metal = tap_total_output + lead_output + follow_output

# 누적 슬래그 출선량 (참고용 자동계산 — 슬래그비율 기반)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# AI 기반 저선량 (용선 기준)
residual_molten = production_ton_ai - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)  # 음수 방지
residual_rate = (residual_molten / production_ton_ai) * 100 if production_ton_ai > 0 else 0

# 실측 저선량 수동입력 (수지보정용)
measured_residual_molten = st.sidebar.number_input("실측 저선량 (ton)", value=45.0)

# AI-실측 저선 오차
residual_gap = residual_molten - measured_residual_molten

# 조업상태 경고 등급
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ========================== 6부: AI 출선전략 + 공취예상시간 + 출선소요시간 ==========================

# 평균 출선량 계산 (TAP 기준)
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)  # 평균 용선
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio  # 평균 슬래그 (참고용)

# AI 추천 비트경: 저선량 기준
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# AI 추천 차기 출선간격 (저선율 기준)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 선행 기준 공취예상시간 계산
lead_target = fixed_avg_tap_output
lead_remain = max(lead_target - lead_output, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 후행 출선과 비교해 Gap 계산
pure_gap = lead_remain_time - follow_elapsed_time
gap_minutes = max(pure_gap, 0)

# 선행 기준 1 Tap 출선 예상 소요시간
expected_tap_time = lead_target / lead_speed if lead_speed > 0 else 0

# ========================== 7부: 용선온도 예측 + 송풍원단위 기반 생산량 계산 ==========================

# 송풍원단위 기반 예상 일일생산량
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_production_by_wind = wind_air_day / wind_unit

# 미분탄 ton/hr 환산 (용선온도 보정용 계산용도)
pci_ton_hr = pci_rate * daily_production_by_wind / 1000

# 용선온도 예측 공식 (보정 및 안정화 적용)
try:
    Tf_predict = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1_000_000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except:
    Tf_predict = 0  # 예외방지

# 최소 하한값 설정 (예외 및 음수 방지)
Tf_predict = max(Tf_predict, 1200)

# ========================== 8부: AI 실시간 리포트 출력 ==========================
st.header("📊 BlastTap 10.3 Pro — AI 실시간 조업 리포트")

# 생산량 요약 (체류보정 제거된 버전 기준)
st.write(f"AI 이론생산량 (누적): {production_ton_ai:.1f} ton")
st.write(f"누적 선철생산량 (총환원량): {total_production_ton:.1f} ton")
st.write(f"일일예상생산량 (송풍원단위 기반): {daily_production_by_wind:.1f} ton/day")

# 실측 출선 및 저선량
st.write(f"TAP 기준 실측 출선량: {tap_total_output:.1f} ton")
st.write(f"선행 실시간 출선량: {lead_output:.1f} ton")
st.write(f"후행 실시간 출선량: {follow_output:.1f} ton")
st.write(f"누적 용선출선량 (총계): {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산 참고): {total_tapped_slag:.1f} ton")
st.write(f"현재 저선량 (AI 계산): {residual_molten:.1f} ton ({residual_rate:.2f}%)")

# 실측 저선량 수동 보정
st.write(f"실측 저선량 입력값: {measured_residual_molten:.1f} ton")
st.write(f"AI-실측 저선 수지편차: {residual_gap:.1f} ton")
st.write(f"조업상태: {status}")

# AI 출선전략
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"선행 잔여 출선시간: {lead_remain_time:.1f} 분")
st.write(f"AI 공취예상시간: {gap_minutes:.1f} 분")
st.write(f"예상 1Tap 출선소요시간: {expected_tap_time:.1f} 분")

# 용선온도 예측
st.write(f"AI 예측 용선온도 (Tf 보정): {Tf_predict:.1f} °C")

# ========================== 9부: 실시간 용융물 수지 시각화 ==========================
st.header("📊 실시간 용융물 수지 시각화")

# 시간축 생성 (15분 간격 시계열)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 누적 생산량 시뮬레이션
gen_series = []
for t in time_labels:
    ore_t = ore_per_charge * (charge_rate * (t / 60))
    fe_t = ore_t * (tfe_percent / 100)
    prod_t = fe_t * normal_reduction_eff  # 체류보정 제거
    prod_t = min(prod_t, total_production_ton)
    gen_series.append(prod_t)

tap_series = [total_tapped_hot_metal] * len(time_labels)
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
plt.legend()
plt.grid()
st.pyplot(plt)

# ====================== 누적 리포트 기록 저장 ======================
st.header("📋 누적 조업 리포트 기록")

record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "누적출선량": total_tapped_hot_metal,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "송풍원단위생산량": daily_production_by_wind,
    "공취예상시간": gap_minutes,
    "Tf예상온도": Tf_predict,
    "AI-실측저선수지차": residual_gap,
    "조업상태": status
}

# 세션 누적 저장
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 테이블 출력 및 CSV 다운로드
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Pro_Report.csv", mime='text/csv')
