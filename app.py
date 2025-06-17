# 📦 필수 라이브러리 호출
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 📌 한글 폰트 안정화 (운영체제별 자동)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 📌 Streamlit 페이지 기본설정
st.set_page_config(page_title="BlastTap 10.2 Pro — AI 고로 실시간 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.2 Pro — 실시간 장입·출선·저선 AI 통합엔진")

# 📌 세션 로그 초기화 (100개 기록 유지)
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 및 경과시간 (07시 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60

# 📌 경과시간 최소/최대 제한 (안정성)
elapsed_minutes = max(elapsed_minutes, 60)
elapsed_minutes = min(elapsed_minutes, 1440)

# ========================== 2부: 정상조업 기본입력 ==========================

st.sidebar.header("① 정상조업 기본입력")

# 장입조건
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 조업조건 (송풍/산소/조습)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7155.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 (%) (수동입력)", value=6.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)

# 풍압·노정압·풍온
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183.0)

# 환원보조 입력
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# 송풍원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# 체류시간 지연 AI 자동보정 (10.2 핵심)
alpha_delay = 10   # iron_rate 변화에 따른 체류시간 보정계수 (분/ton)
base_melting_delay = 330  # 기본 체류지연시간 (분)
melting_delay = base_melting_delay - alpha_delay * (iron_rate - 9.0)
melting_delay = max(240, min(melting_delay, 400))  # 안정 구간 제한

st.sidebar.write(f"AI 자동보정 체류지연시간: {melting_delay:.1f} 분")

# ========================== 3부: 비상조업 + 감풍·휴풍 입력 ==========================

st.sidebar.header("② 비상조업 보정입력")

# 🔧 비상조업 체크박스
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

# 🔧 감풍·휴풍 보정 체크박스
st.sidebar.header("③ 감풍·휴풍 보정입력")
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)

if reduction_active:
    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm³/min)", value=blast_volume)
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm³/hr)", value=oxygen_volume)
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual)
    reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm³)", value=humidification)
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 (kg/thm)", value=pci_rate)
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위 (Nm³/t)", value=wind_unit)

# ========================== 4부: 시간분할 AI 환원효율 계산 ==========================

# 🔧 정상 환원효율 계산
size_effect = 1  # 단순화 유지 (Size 평균효과 반영)
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_rate_effect = iron_rate / 9.0

normal_reduction_eff = reduction_efficiency * size_effect * melting_effect * gas_effect * \
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost * temp_effect * \
    pci_effect * iron_rate_effect * K_factor * 0.9

# 🔧 비상조업 보정효율
if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

    abnormal_reduction_eff = reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect * \
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * abnormal_pci_effect * iron_rate_effect * K_factor * 0.9
else:
    abnormal_reduction_eff = normal_reduction_eff

# 🔧 감풍·휴풍 보정효율
if reduction_active:
    reduction_gas_effect = 1 + (reduction_blast_volume - 4000) / 8000
    reduction_oxygen_boost = 1 + (reduction_oxygen_enrichment / 10)
    reduction_humidity_effect = 1 - (reduction_humidification / 100)
    reduction_pci_effect = 1 + (reduction_pci_rate - 150) / 100 * 0.02

    reduction_reduction_eff = reduction_efficiency * size_effect * melting_effect * reduction_gas_effect * \
        reduction_oxygen_boost * reduction_humidity_effect * pressure_boost * blow_pressure_boost * \
        temp_effect * reduction_pci_effect * iron_rate_effect * K_factor * 0.9
else:
    reduction_reduction_eff = normal_reduction_eff

# 🔧 시간분할 적용 (정상/비상/감풍 시간 분리계산)
# 지금은 단일 정상시간 적용 (이후 확장에서 분할 가능)

adjusted_elapsed_minutes = elapsed_minutes
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 60)

# 🔧 누적 Charge 수
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# 🔧 생산량 계산
ore_total = ore_per_charge * elapsed_charges
fe_total = ore_total * (tfe_percent / 100)
production_ton_ai = fe_total * normal_reduction_eff
production_ton_ai = max(production_ton_ai, 0)

# 🔧 체류시간 보정 생산량
if adjusted_elapsed_minutes > melting_delay:
    effective_minutes = adjusted_elapsed_minutes - melting_delay
else:
    effective_minutes = 0

effective_production_ton = production_ton_ai * (effective_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# ========================== 5부: 실측 출선, 저선량, 슬래그 계산 ==========================

st.sidebar.header("④ 실측 출선 실적 입력")

# TAP당 실측 입력
fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균 출선량 (ton)", value=1250.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=5)
tap_total_output = fixed_avg_tap_output * completed_taps

# 실시간 선행/후행 출선 데이터 입력
st.sidebar.header("⑤ 실시간 출선 현황 입력")

lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 30))

lead_elapsed_time = st.sidebar.number_input("선행 경과시간 (분)", value=90.0)
follow_elapsed_time = st.sidebar.number_input("후행 경과시간 (분)", value=30.0)

lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.5)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.5)

lead_output = lead_elapsed_time * lead_speed
follow_output = follow_elapsed_time * follow_speed

# 누적 용선 출선량 = TAP용선 + 실시간 선행 + 실시간 후행
total_tapped_hot_metal = tap_total_output + lead_output + follow_output

# 슬래그 자동계산 (슬래그비율 기준)
total_tapped_slag = total_tapped_hot_metal / slag_ratio

# 누적 선철생산량 기준 저선량 추적
# 누적 생산량 (장입 누적 환원 기준 생산량)
total_production_ton = production_ton_ai

# 저선량 = 생산량 - 출선량
residual_molten = total_production_ton - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / total_production_ton) * 100 if total_production_ton > 0 else 0

# 저선 상태 경보
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# ========================== 6부: AI 출선전략 및 공취예상시간 ==========================

# 🔧 평균 출선량 및 슬래그량
avg_hot_metal_per_tap = total_tapped_hot_metal / max(completed_taps, 1)
avg_slag_per_tap = avg_hot_metal_per_tap / slag_ratio

# 🔧 AI 추천 비트경 로직
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 🔧 AI 추천 차기 출선간격 로직 (저선율 기반)
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 🔧 공취예상시간 계산
# 선행 기준으로 현재 잔여출선량 계산
lead_target = fixed_avg_tap_output  # 한 tap당 계획 출선량 기준
lead_remain = max(lead_target - lead_output, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 후행 기준 공취 gap 시간 계산
pure_gap = lead_remain_time - follow_elapsed_time
gap_minutes = max(pure_gap, 0)

# 🔧 예상 출선소요시간 계산 (AI출선계획)
# 참고: 실질적인 1 Tap 소요시간 예측모델
expected_tap_time = lead_target / lead_speed

# 예상 공취 시각 자동출력
expected_closing_time = lead_remain_time + follow_elapsed_time

# ========================== 7부: 용선온도 예측 및 송풍원단위 생산량 ==========================

# 🔧 용선온도(Tf) 예측 AI (PC 단위: kg/thm → ton/hr로 환산)
pci_ton_hr = pci_rate / 1000 * daily_production_est if 'daily_production_est' in locals() else 0

# 실제 계산 (이론 공식)
try:
    Tf_predict = (hot_blast_temp * 0.836) \
        + ((oxygen_volume / (60 * blast_volume)) * 4973) \
        - (hot_blast_temp * 6.033) \
        - ((pci_ton_hr * 1000000) / (60 * blast_volume) * 3.01) \
        + 1559
except:
    Tf_predict = 0  # 초기 계산 에러방지

# 🔧 송풍원단위 기반 AI 일일생산량
# 공식: (풍량×1440 + (산소×24/0.21)) / 송풍원단위

wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_production_by_wind = wind_air_day / wind_unit

# 🔧 보정 후 체류생산 기준 일일생산량 (환원효율 기반 기존 계산식)
if elapsed_charges > 0:
    daily_production_est = (ore_per_charge * elapsed_charges * (tfe_percent/100) * normal_reduction_eff) * (1440 / adjusted_elapsed_minutes)
else:
    daily_production_est = 0

# ========================== 8부: AI 실시간 결과 리포트 ==========================

st.header("📊 BlastTap 10.2 Pro 실시간 조업 리포트")

# AI 생산량 요약
st.write(f"AI 이론생산량 (누적): {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"누적 선철생산량: {total_production_ton:.1f} ton")
st.write(f"일일예상생산량 (환원효율 기반): {daily_production_est:.1f} ton/day")
st.write(f"일일예상생산량 (송풍원단위 기반): {daily_production_by_wind:.1f} ton/day")

# 실측 출선 및 저선
st.write(f"실측 용선출선량 (TAP 누적): {tap_total_output:.1f} ton")
st.write(f"선행 출선량 (실시간): {lead_output:.1f} ton")
st.write(f"후행 출선량 (실시간): {follow_output:.1f} ton")
st.write(f"누적 용선출선량 (총계): {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그출선량 (자동계산): {total_tapped_slag:.1f} ton")
st.write(f"현재 저선량: {residual_molten:.1f} ton  ({residual_rate:.2f}%)")
st.write(f"저선상태: {status}")

# AI 출선전략
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"선행 잔여 출선시간: {lead_remain_time:.1f} 분")
st.write(f"AI 공취예상시간: {gap_minutes:.1f} 분")
st.write(f"AI 예상 1Tap 출선소요시간: {expected_tap_time:.1f} 분")

# 용선온도 예측결과
st.write(f"예상 용선온도 (Tf): {Tf_predict:.1f} °C")

# ========================== 9부: 실시간 시각화 및 누적 리포트 기록 ==========================

# 🔧 실시간 용융물 수지 시각화
st.header("📊 실시간 용융물 수지추적")

# 시간축 생성
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 정상환원효율 기준 누적생산량 시뮬레이션
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * normal_reduction_eff
    for t in time_labels
]

# 체류시간 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, total_production_ton) for g in gen_series]
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

plt.figure(figsize=(10, 6))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지추적")
plt.ylim(0, total_production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# 🔧 누적 리포트 기록 및 CSV 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측출선량": total_tapped_hot_metal,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "예상일일생산량": daily_production_est,
    "송풍AI생산량": daily_production_by_wind,
    "공취예상시간": gap_minutes,
    "Tf예상온도": Tf_predict,
    "상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 200:
    st.session_state['log'].pop(0)

# 🔧 누적 조업 리포트 출력
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap10.2_Report.csv", mime='text/csv')
