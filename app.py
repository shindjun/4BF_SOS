import streamlit as st
import pandas as pd
import numpy as np
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

# 페이지 기본설정
st.set_page_config(page_title="BlastTap 9.7 Master — 실시간 AI 고로출선조업지원", layout="wide")
st.title("🔥 BlastTap 9.7 — 실시간 AI 고로조업 시뮬레이터")

# 세션 기록 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# 기준일자 계산 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()

today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(60, min(elapsed_minutes, 1440))

# ① 정상조업 입력부
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("장입시간 (분)", value=11.0)
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

# Charge rate 계산
charge_rate = 60 / charging_time_per_charge

# Pig 생성량 계산
pig_per_charge = (ore_per_charge + coke_per_charge) / (ore_per_charge / coke_per_charge)

# 풍량원단위 계산 (Nm³/t)
# 현재 일일 생산량(12589t)은 샘플기본값 기준
total_oxygen = (blast_volume * 60 + (oxygen_enrichment / 0.21) * 8)
blast_specific_volume = (total_oxygen * 24) / 12589

# 예상 용선온도(Tf) 예측식
Tf = (
    (hot_blast_temp * 0.836)
    + (oxygen_enrichment / (60 * blast_volume) * 4973)
    - (hot_blast_temp * 6.033)
    - ((pci_rate * 1000000) / (60 * blast_volume) * 3.01)
    + 1559
)

# AI 환원효율 보정
size_effect = (20/20 + 60/60) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
iron_rate_effect = iron_rate / 9.0

reduction_eff = (
    size_effect * melting_effect * gas_effect * oxygen_boost * humidity_effect
    * pressure_boost * blow_pressure_boost * temp_effect * pci_effect
    * iron_rate_effect * K_factor * 0.9
)

# AI 이론 생산량 계산
elapsed_charges = charge_rate * (elapsed_minutes / 60)
total_ore = ore_per_charge * elapsed_charges
total_fe = total_ore * (tfe_percent / 100)
production_ton_ai = total_fe * reduction_eff

# 체류시간 보정 적용
if elapsed_minutes > melting_delay:
    active_minutes = elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = (
    production_ton_ai * (active_minutes / elapsed_minutes) if elapsed_minutes > 0 else 0
)

# ② 실측 출선 실적 입력
st.sidebar.header("② 실측 출선 실적 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 이중수지 평균 생산량 병합
production_ton = (effective_production_ton + production_ton_tap) / 2
production_gap = effective_production_ton - production_ton_tap

# ③ 잔여출선 AI 예측
st.sidebar.header("③ 잔여 출선 예측 AI")

avg_tap_duration = st.sidebar.number_input("평균 출선소요시간 (분)", value=140)
current_lead_speed = st.sidebar.number_input("현재 선행출선속도 (ton/min)", value=5.0)
tap_start_time = st.sidebar.time_input("선행출선 시작시각", value=datetime.time(8, 0))

tap_start_dt = datetime.datetime.combine(base_date, tap_start_time)
t_elapsed = max((now - tap_start_dt).total_seconds() / 60, 0)
T_tapped = current_lead_speed * t_elapsed

T_target = fixed_avg_tap_output
T_remain = max(T_target - T_tapped, 0)

# 잔여시간 예측 (현재출선속도 + 평균출선시간 보정 혼합모델)
V_avg = T_target / avg_tap_duration
alpha = 0.7
V_blend = alpha * current_lead_speed + (1 - alpha) * V_avg
t_remain = T_remain / V_blend if V_blend > 0 else 0

# 선행 예상 출선소요시간 및 예상출선량
lead_expected_duration = T_target / current_lead_speed if current_lead_speed > 0 else 0
lead_expected_amount = T_target

# ④ 공취위험예측 AI
design_pool_ton = 150  # 저선 안정 Pool 기준값
residual_molten = max(production_ton - (production_ton_tap + T_tapped), 0)

# 공취위험스코어 계산식 (4중 요소 가중치)
risk_score = (
    30 * (1 - residual_molten / design_pool_ton)
    + 20 * (t_elapsed / 150)
    + 20 * (blast_pressure / 4.2)
    + 10 * (current_lead_speed / 5)
)

# 공취위험 상태판별
if risk_score >= 80:
    risk_status = "🔴 공취위험 고도화"
elif risk_score >= 60:
    risk_status = "🟠 공취경계구간"
else:
    risk_status = "✅ 안정출선"

# 풍압상승 감지 → 자동 풍량·산소 보정 제안
if blast_pressure >= 4.0:
    blast_volume_adj = blast_volume * 0.985
    oxygen_enrichment_adj = oxygen_enrichment * 0.975
else:
    blast_volume_adj = blast_volume
    oxygen_enrichment_adj = oxygen_enrichment

# 색상경고판넬 — 저선 위험판
if residual_molten >= 200:
    molten_status = "🔴 저선 위험"
elif residual_molten >= 150:
    molten_status = "🟠 저선 과다"
elif residual_molten >= 100:
    molten_status = "🟡 관리권고"
else:
    molten_status = "✅ 정상"

# 색상경고판넬 — 풍압 경고판
if blast_pressure >= 4.2:
    pressure_status = "🔴 풍압한계"
elif blast_pressure >= 4.0:
    pressure_status = "🟠 풍압강화"
else:
    pressure_status = "✅ 정상"

# ⑤ 추천 비트경 (저선량 + 위험스코어 기반)
if residual_molten < 100 and risk_score < 50:
    tap_diameter = 43
elif residual_molten < 150 and risk_score < 70:
    tap_diameter = 45
else:
    tap_diameter = 48

# 차기 출선간격 추천
if residual_molten < 100:
    next_tap_interval = "15~20분"
elif residual_molten < 150:
    next_tap_interval = "10~15분"
elif residual_molten < 200:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 출선 권장"

# 동시출선 예상잔여시간 (선행출선 종료전까지)
lead_speed_reference = 5.0  # 기준속도 5 ton/min
lead_remain = max(T_target - T_tapped, 0)
lead_remain_time = lead_remain / lead_speed_reference if lead_speed_reference > 0 else 0

# ⑥ 실시간 AI 조업 리포트
st.header("📊 AI 실시간 조업 리포트")

st.write(f"AI 이론생산량: {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")

st.write(f"잔여출선량: {T_remain:.1f} ton")
st.write(f"잔여출선 소요시간: {t_remain:.1f} 분")
st.write(f"선행 예상출선소요시간: {lead_expected_duration:.1f} 분")
st.write(f"선행 예상출선량: {lead_expected_amount:.1f} ton")

st.write(f"잔류저선량: {residual_molten:.1f} ton → {molten_status}")
st.write(f"현재 풍압: {blast_pressure:.2f} kg/cm² → {pressure_status}")
st.write(f"공취위험스코어: {risk_score:.1f} → {risk_status}")

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"동시출선 예상 잔여시간: {lead_remain_time:.1f} 분")

st.write(f"예상 용선온도 (Tf): {Tf:.1f} ℃")
st.write(f"풍량원단위: {blast_specific_volume:.1f} Nm³/t")
st.write(f"Pig 생성량: {pig_per_charge:.2f} ton/ch")

# ⑦ 저선량-풍압 곡선패널 시각화
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

# 📋 누적 리포트 기록 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "이중수지평균": production_ton,
    "잔여출선량": T_remain,
    "잔여출선시간": t_remain,
    "선행출선시간": lead_expected_duration,
    "선행출선량": lead_expected_amount,
    "저선량": residual_molten,
    "공취스코어": risk_score,
    "풍압": blast_pressure,
    "비트경": tap_diameter,
    "출선간격": next_tap_interval,
    "공취상태": risk_status
}

st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# 누적 리포트 출력
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.7_Report.csv", mime='text/csv')

