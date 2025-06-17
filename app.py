import streamlit as st
import pandas as pd
import numpy as np
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

# 📌 페이지 기본설정
st.set_page_config(page_title="BlastTap 9.7 Pro — 실전형 고로 AI조업엔진", layout="wide")
st.title("🔥 BlastTap 9.7 Pro — 실시간 AI 고로조업지원 확장버전")

# 📌 세션 기록 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 📌 기준일자 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(60, min(elapsed_minutes, 1440))

# ===================== 🔧 정상조업 입력부 =====================
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=170.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.25)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=4.0)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.0)
hot_blast_temp = st.sidebar.number_input("풍온 (℃)", value=1190)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)

# ===================== 🔧 비상조업 입력부 =====================
st.sidebar.header("② 비상조업 보정입력")

abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
else:
    abnormal_start_time = abnormal_end_time = None
    abnormal_charging_delay = 0
    abnormal_blast_volume = blast_volume
    abnormal_oxygen = oxygen_enrichment
    abnormal_humidification = humidification
    abnormal_pci_rate = pci_rate

# ===================== 🔧 선행/후행 출선 동시제어 입력부 =====================
st.sidebar.header("③ 동시출선 실측 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 목표출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)

lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)

# 🔧 장입속도 및 Charge 수 계산
charge_rate = 60 / charging_time_per_charge

# 🔧 전체 경과시간 분할 (정상/비상/이후)
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

# 🔧 비상조업 장입지연 보정
abnormal_adjusted_elapsed = max(abnormal_elapsed - abnormal_charging_delay, 0)

# 🔧 누적장입시간 최종합산
adjusted_elapsed_minutes = normal_elapsed + abnormal_adjusted_elapsed + after_elapsed
adjusted_elapsed_minutes = max(adjusted_elapsed_minutes, 60)

# 🔧 Charge 수 분할계산
normal_charges = charge_rate * (normal_elapsed / 60)
abnormal_charges = charge_rate * (abnormal_adjusted_elapsed / 60)
after_charges = charge_rate * (after_elapsed / 60)

# 🔧 Pig 생성량 재계산
pig_per_charge = (ore_per_charge + coke_per_charge) / (ore_per_charge / coke_per_charge)

# 🔧 정상 환원효율 계산
size_effect = (20 / 20 + 60 / 60) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_rate_effect = iron_rate / 9.0

normal_reduction_eff = (
    size_effect * melting_effect * gas_effect * oxygen_boost * humidity_effect
    * pressure_boost * blow_pressure_boost * temp_effect * pci_effect
    * iron_rate_effect * K_factor * 0.9
)

# 🔧 비상 환원효율 계산
abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
abnormal_oxygen_boost = 1 + (abnormal_oxygen / 10)
abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02

abnormal_reduction_eff = (
    size_effect * melting_effect * abnormal_gas_effect * abnormal_oxygen_boost
    * abnormal_humidity_effect * pressure_boost * blow_pressure_boost
    * temp_effect * abnormal_pci_effect * iron_rate_effect * K_factor * 0.9
)

# 🔧 구간별 수지계산
normal_fe = ore_per_charge * normal_charges * (tfe_percent / 100)
abnormal_fe = ore_per_charge * abnormal_charges * (tfe_percent / 100)
after_fe = ore_per_charge * after_charges * (tfe_percent / 100)

normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
after_production = after_fe * normal_reduction_eff

# 🔧 AI 이론생산량
production_ton_ai = normal_production + abnormal_production + after_production

# 🔧 체류시간 보정
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = (
    production_ton_ai * (active_minutes / adjusted_elapsed_minutes)
    if adjusted_elapsed_minutes > 0 else 0
)

# 🔧 실측 TAP 기반 누적출선량 계산
production_ton_tap = completed_taps * fixed_avg_tap_output

# 🔧 이중수지 평균 생산량 병합
production_ton = (effective_production_ton + production_ton_tap) / 2
production_gap = effective_production_ton - production_ton_tap

# 🔧 선행/후행 출선 실시간 누적출선량 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

# 🔧 누적 출선량 (TAP완료 + 선행 + 후행)
completed_tap_amount = production_ton_tap
total_tapped = completed_tap_amount + lead_tapped + follow_tapped
total_tapped = min(total_tapped, production_ton)  # 과다보정 방지

# 🔧 저선량 계산
residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)

# 🔧 저선율
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 🔧 잔여출선량 (선행기준)
T_target = fixed_avg_tap_output
T_remain = max(T_target - lead_tapped, 0)

# 🔧 평균 출선속도 보정혼합 (AI 블렌딩)
avg_tap_duration = 140  # 기본 평균 출선시간
V_avg = T_target / avg_tap_duration
alpha = 0.7
V_blend = alpha * lead_speed + (1 - alpha) * V_avg
t_remain = T_remain / V_blend if V_blend > 0 else 0

# 🔧 선행 전체 예상출선 소요시간
lead_expected_duration = T_target / lead_speed if lead_speed > 0 else 0
lead_expected_amount = T_target

# 🔧 공취위험 스코어 계산
design_pool_ton = 150  # 안정적 저선 Pool 기준값 (설정 가능)

# 공취위험 스코어 = 저선량, 경과시간, 풍압, 출선속도 가중모델
risk_score = (
    30 * (1 - residual_molten / design_pool_ton)
    + 20 * (lead_elapsed / 150)
    + 20 * (blast_pressure / 4.2)
    + 10 * (lead_speed / 5)
)

# 🔧 공취상태 판정
if risk_score >= 80:
    risk_status = "🔴 공취위험 고도화"
elif risk_score >= 60:
    risk_status = "🟠 공취경계구간"
else:
    risk_status = "✅ 안정출선"

# 🔧 풍압상승 자동 조정 로직
if blast_pressure >= 4.0:
    blast_volume_adj = blast_volume * 0.985
    oxygen_enrichment_adj = oxygen_enrichment * 0.975
else:
    blast_volume_adj = blast_volume
    oxygen_enrichment_adj = oxygen_enrichment

# 🔧 색상경고판넬 (저선 위험 경고)
if residual_molten >= 200:
    molten_status = "🔴 저선 위험"
elif residual_molten >= 150:
    molten_status = "🟠 저선 과다"
elif residual_molten >= 100:
    molten_status = "🟡 저선 관리권고"
else:
    molten_status = "✅ 정상"

# 🔧 색상경고판넬 (풍압 위험 경고)
if blast_pressure >= 4.2:
    pressure_status = "🔴 풍압한계"
elif blast_pressure >= 4.0:
    pressure_status = "🟠 풍압강화"
else:
    pressure_status = "✅ 정상"

# 🔧 추천 비트경 결정
if residual_molten < 100 and risk_score < 50:
    tap_diameter = 43
elif residual_molten < 150 and risk_score < 70:
    tap_diameter = 45
else:
    tap_diameter = 48

# 🔧 차기 출선간격 추천
if residual_molten < 100:
    next_tap_interval = "15~20분"
elif residual_molten < 150:
    next_tap_interval = "10~15분"
elif residual_molten < 200:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 출선 권장"

# 🔧 동시출선 예상 잔여시간 (선행 기준 5 ton/min 가정)
lead_speed_reference = 5.0  # 기준속도 5톤/분
lead_remain = max(T_target - lead_tapped, 0)
lead_remain_time = lead_remain / lead_speed_reference if lead_speed_reference > 0 else 0

# 🔧 실시간 AI 조업 리포트 출력
st.header("📊 AI 실시간 조업 리포트")

st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")

st.write(f"누적 출선량 (TAP+선행+후행): {total_tapped:.1f} ton")
st.write(f"저선량 (잔류용융물): {residual_molten:.1f} ton → {molten_status}")
st.write(f"저선율: {residual_rate:.2f} %")

st.write(f"선행 현재 출선경과시간: {lead_elapsed:.1f} 분")
st.write(f"선행 잔여출선량: {T_remain:.1f} ton")
st.write(f"선행 잔여출선시간: {t_remain:.1f} 분")
st.write(f"선행 전체예상출선시간: {lead_expected_duration:.1f} 분")
st.write(f"선행 예상출선량: {lead_expected_amount:.1f} ton")

st.write(f"현재 풍압: {blast_pressure:.2f} kg/cm² → {pressure_status}")
st.write(f"공취위험 스코어: {risk_score:.1f} → {risk_status}")

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"동시출선 잔여시간(선행 기준): {lead_remain_time:.1f} 분")

# 추가 참고지수
st.write(f"Pig 생성량: {pig_per_charge:.2f} ton/ch")

# 🔧 저선량 - 풍압 안정곡선 시각화 (AI 진단 패널)
residual_range = np.arange(50, 250, 5)
pressure_curve = []

for rm in residual_range:
    if rm > 150:
        boost = 1 + 0.02 * (rm - 150) / 50
    elif rm < 80:
        boost = 1 + 0.05 * (80 - rm) / 40
    else:
        boost = 1.0
    pressure_curve.append(blast_pressure * boost)

plt.figure(figsize=(7, 5))
plt.plot(residual_range, pressure_curve, label="AI 예측 곡선")
plt.scatter(residual_molten, blast_pressure, color='red', label="현재 위치", zorder=5)
plt.axhline(4.0, color='orange', linestyle='--', label='풍압 강화경계')
plt.axhline(4.2, color='red', linestyle='--', label='한계풍압 4.2')
plt.xlabel("저선량 (ton)")
plt.ylabel("풍압 (kg/cm²)")
plt.title("저선량-풍압 AI 안정곡선")
plt.legend()
plt.grid()
st.pyplot(plt)

# 🔧 누적 리포트 기록 (조업이력 기록판)
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI이론생산": production_ton_ai,
    "체류보정": effective_production_ton,
    "실측생산": production_ton_tap,
    "이중수지평균": production_ton,
    "저선량": residual_molten,
    "잔여출선량": T_remain,
    "잔여출선시간": t_remain,
    "공취스코어": risk_score,
    "풍압": blast_pressure,
    "비트경": tap_diameter,
    "출선간격": next_tap_interval,
    "공취상태": risk_status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 🔧 누적 데이터 출력
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# 🔧 CSV 다운로드 기능
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.7_Pro_Report.csv", mime='text/csv')

