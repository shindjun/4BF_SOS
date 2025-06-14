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
st.set_page_config(page_title="BlastTap 9.6 Master++", layout="wide")
st.title("🔥 BlastTap 9.6 Master++ — AI 고로조업 실전엔진")

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

# ------------------ 🟢 1부: 입력항목 ------------------

st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 OB (ton/ch)", value=165.0)
oc_ratio = st.sidebar.number_input("O/C 비율", value=5.0)
cr_ratio = st.sidebar.number_input("C.R (kg/thm)", value=370.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
reduction_efficiency = st.sidebar.number_input("환원효율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7960.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36941.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate_ton_hr = st.sidebar.number_input("미분탄 투입량 (ton/hr)", value=25.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.2)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
iron_rate = st.sidebar.number_input("선철 생성속도 (ton/min)", value=9.14)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1194)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)

# CB 및 1Ch당 생산량 계산
charge_bulk = ore_per_charge / oc_ratio
charge_yield = charge_bulk / (cr_ratio / 1000)
charge_rate = 60 / charging_time_per_charge

# 👉 CB, 1Ch당 생산량 출력 (중간 점검)
st.write(f"총 장입량 CB : {charge_bulk:.2f} ton/ch")
st.write(f"1Ch당 생산량 : {charge_yield:.2f} ton/ch")

# 비상조업 입력
st.sidebar.header("② 비상조업 입력")
abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)
    abnormal_pci_rate_ton_hr = st.sidebar.number_input("비상 미분탄 (ton/hr)", value=pci_rate_ton_hr)

# ------------------ 🟢 2부: AI 확장수지 계산 ------------------

# 체류시간 분리
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

# 비상조업 장입지연 보정
if abnormal_active:
    abnormal_adjusted_elapsed = abnormal_elapsed - abnormal_charging_delay
    abnormal_adjusted_elapsed = max(abnormal_adjusted_elapsed, 0)
else:
    abnormal_adjusted_elapsed = 0

# 누적 Charge 수 계산
adjusted_elapsed_minutes = normal_elapsed + abnormal_adjusted_elapsed + after_elapsed
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# 생산량 계산 (정상구간)
normal_ore = ore_per_charge * (charge_rate * (normal_elapsed / 60))
abnormal_ore = ore_per_charge * (charge_rate * (abnormal_adjusted_elapsed / 60))
after_ore = ore_per_charge * (charge_rate * (after_elapsed / 60))

# Fe 함량 계산
normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 용선 생산량 계산 (단순 환원효율 적용)
normal_production = normal_fe * reduction_efficiency
abnormal_production = abnormal_fe * reduction_efficiency
after_production = after_fe * reduction_efficiency

# 총 AI 이론 생산량
production_ton_ai = normal_production + abnormal_production + after_production

# 체류시간 보정
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes) if adjusted_elapsed_minutes > 0 else 0

# 일일생산량 예측
if elapsed_charges > 0:
    expected_daily_production = (ore_per_charge * elapsed_charges * (tfe_percent / 100) * reduction_efficiency) * (1440 / adjusted_elapsed_minutes)
else:
    expected_daily_production = 0

# 분당 용선생산량 및 슬래그포함
hm_per_min = expected_daily_production / (24 * 60)
slag_volume = st.sidebar.number_input("슬래그볼륨 (kg/T-P)", value=300.0)
hm_with_slag_per_min = hm_per_min * (1 + (slag_volume / 1000) * (2 / 7))

# ✅ 🔧 Tf 최종 공식 (ton/hr 기준 적용)
pci_kg_per_min = pci_rate_ton_hr * 1000 / 60
Tf_predict = (hot_blast_temp * 0.836) \
    + (oxygen_volume / (60 * blast_volume) * 4973) \
    - (hot_blast_temp * 6.033) \
    - ((pci_rate_ton_hr * 1_000_000) / (60 * blast_volume) * 3.01) \
    + 1559

# ✅ 🔧 풍량원단위 자동계산
if expected_daily_production > 0:
    blast_unit = ((blast_volume * 1440) + (oxygen_volume * 24 / 0.21)) / expected_daily_production
else:
    blast_unit = 0

# ✅ 결과 중간 출력 (디버깅용)
st.subheader("🔧 AI 확장 수지 계산결과")
st.write(f"AI 예측 일일생산량: {expected_daily_production:.1f} ton/day")
st.write(f"분당 용선생산량: {hm_per_min:.3f} ton/min")
st.write(f"슬래그 포함 분당생산량: {hm_with_slag_per_min:.3f} ton/min")
st.write(f"예상 용선온도 (Tf): {Tf_predict:.1f} °C")
st.write(f"풍량원단위: {blast_unit:.1f} Nm³/ton")

# ------------------ 🟢 3부: 저선량 추적 및 저선고도계산 ------------------

# 🔧 실측 TAP 기반 출선량 입력
st.sidebar.header("③ 실측 출선 실적 입력")

fixed_avg_tap_output = st.sidebar.number_input("TAP당 평균출선량 (ton)", value=1100.0)
completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
production_ton_tap = completed_taps * fixed_avg_tap_output

# 🔧 이중수지 평균 생산량 (AI+실측 병합)
production_ton = (effective_production_ton + production_ton_tap) / 2
production_ton = max(production_ton, 0)

# 🔧 수지편차 계산
production_gap = effective_production_ton - production_ton_tap

# 🔧 누적 출선량 계산
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1100.0)

lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
follow_tapped = follow_speed * follow_elapsed

completed_tap_amount = completed_taps * fixed_avg_tap_output
total_tapped = completed_tap_amount + lead_tapped + follow_tapped
total_tapped = min(total_tapped, production_ton)

# 🔧 저선량 (잔류용융물) 추적
residual_molten = production_ton - total_tapped
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / production_ton) * 100 if production_ton > 0 else 0

# 🔧 저선 고도계산 (출선구대비높이 계산)
st.sidebar.header("④ 저선고도 계산 입력")
hearth_area = st.sidebar.number_input("노저 단면적 (m²)", value=80.0)
porosity = st.sidebar.number_input("공극률", value=0.3)
hm_density = 7.0  # 용선비중 ton/m³
slag_density = 2.3  # 슬래그비중 ton/m³

# 슬래그량 추정
avg_slag_per_tap = (fixed_avg_tap_output / slag_ratio)
total_slag = completed_taps * avg_slag_per_tap

# 용융물 체적 계산
hm_volume = residual_molten / hm_density
slag_volume_m3 = total_slag / slag_density
total_molten_volume = hm_volume + slag_volume_m3

if residual_molten > 0:
    height_ratio = total_molten_volume / (porosity * residual_molten)
else:
    height_ratio = 0

# 🔧 저선경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리권고"
else:
    status = "✅ 정상운전"

# 🔧 결과 출력
st.subheader("🔧 저선량 추적결과")
st.write(f"실측 TAP 생산량: {production_ton_tap:.1f} ton")
st.write(f"AI 이론 생산량: {effective_production_ton:.1f} ton")
st.write(f"이중수지 평균 생산량: {production_ton:.1f} ton")
st.write(f"누적 출선량: {total_tapped:.1f} ton")
st.write(f"저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"저선고도 (출선구대비높이): {height_ratio:.2f}")
st.write(f"조업상태: {status}")

# ------------------ 🟢 4부: 공취예상시간 + 출선소요시간 TapTime AI ------------------

st.sidebar.header("⑤ 공취예상시간 및 소요시간 예측")

# 🔧 선행 출선잔량 추적
lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

lead_tapped = lead_speed * lead_elapsed
lead_remain = max(lead_target - lead_tapped, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 🔧 실시간 공취예상시간 계산
pure_gap = lead_remain_time - follow_elapsed
gap_minutes = max(pure_gap, 0)

# 🔧 TapTime AI 출선소요시간 예측 (신규 모델)
tap_interval = st.sidebar.number_input("출선간격 (분)", value=20.0)
pig_generation = st.sidebar.number_input("Pig 생성량 (ton/min)", value=0.3)
tap_speed = st.sidebar.number_input("Tap 실측출선속도 (ton/min)", value=5.0)

if pig_generation >= tap_speed:
    st.warning("Pig 생성량이 출선속도보다 클 수 없습니다.")
    expected_tap_time = 0
else:
    expected_tap_time = (tap_interval * pig_generation) / (tap_speed * (1 - (pig_generation / tap_speed)))

# 🔧 결과 출력
st.subheader("🔧 공취예상시간 및 TapTime AI 소요시간 예측결과")
st.write(f"선행 잔여출선량: {lead_remain:.1f} ton")
st.write(f"선행 잔여출선시간: {lead_remain_time:.1f} 분")
st.write(f"AI 공취예상시간: {gap_minutes:.1f} 분")
st.write(f"AI 출선소요시간 (TapTime AI): {expected_tap_time:.1f} 분")

# ------------------ 🟢 5부: 실시간 시각화 및 누적 리포트 기록 ------------------

# ✅ 실시간 수지추적 시각화
st.header("📊 실시간 용융물 수지추적 그래프")

time_labels = [i for i in range(0, int(adjusted_elapsed_minutes)+1, 15)]

gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent/100) * reduction_efficiency
    for t in time_labels
]

# 체류시간 보정반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

gen_series = [min(g, production_ton) for g in gen_series]
tap_series = [total_tapped] * len(time_labels)
residual_series = [max(g - total_tapped, 0) for g in gen_series]

plt.figure(figsize=(8, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지추적")
plt.ylim(0, production_ton * 1.2)
plt.xlim(0, max(adjusted_elapsed_minutes, 240))
plt.legend()
plt.grid()
st.pyplot(plt)

# ✅ 누적 리포트 기록용 세션 상태 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "실측생산량": production_ton_tap,
    "이중수지평균": production_ton,
    "출선량": total_tapped,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "저선고도": height_ratio,
    "예상일일생산량": expected_daily_production,
    "Tf예측": Tf_predict,
    "풍량원단위": blast_unit,
    "공취예상시간": gap_minutes,
    "소요시간(TapTime)": expected_tap_time,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# ✅ 누적 리포트 테이블 및 다운로드
st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_9.6_MasterPlus_Report.csv", mime='text/csv')
