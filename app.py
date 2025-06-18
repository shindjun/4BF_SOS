import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 🔧 폰트 설정 (한글 안정화용)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 🔧 페이지 설정
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

# 경과 시간 계산 (07시 기준)
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

# ========================== 2부: 정상조업 입력부 ==========================
st.sidebar.header("① 정상조업 기본입력")

# 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)

# O/C 비율 계산
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"O/C 비율: **{ore_coke_ratio:.2f}**")

# 철광석 성분 및 슬래그 비율
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio_user = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 조업지수 및 용해능력
reduction_efficiency = st.sidebar.number_input("기본 환원율", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

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

# 송풍 원단위
wind_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

# 예상 일일생산량 (송풍 기준) — 계산식 반영
# ((송풍량 × 1440) + (산소부화량 × 24 / 0.21)) / 송풍원단위
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_expected_production = wind_air_day / wind_unit

# ========================== 3부: 비상조업 + 감풍·휴풍 보정입력 ==========================
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
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

# 송풍기준 일일예상생산량 계산 (0.21 계수 포함)
wind_air_day = blast_volume * 60 * 24  # Nm³/day
daily_expected_production = (wind_air_day / wind_unit) * 0.21  # ton/day 기준 보정

# K-factor 보정값
K_factor = 1.0  # 필요시 조정

# 기본 환원효율 (정상조업 기준)
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9
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
        abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor * 0.9
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
        reduction_temp_effect * reduction_pci_effect * measured_temp_effect * K_factor * 0.9
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

# ============================= 5부: 실측 출선 및 저선량 계산 ============================

# 🔹 실측 출선값 (종료된 Tap)
closed_tap_weight = st.sidebar.number_input("종료된 Tap 출선량 (ton)", value=0.0)

# 🔹 선행·후행 출선량
lead_tap_weight = st.sidebar.number_input("선행 Tap 출선량 (ton)", value=0.0)
follow_tap_weight = st.sidebar.number_input("후행 Tap 출선량 (ton)", value=0.0)

# 🔹 일일 실시간 출선량
realtime_tap_weight = st.sidebar.number_input("일일 실시간 용선 출선량 (ton)", value=0.0)

# 🔹 총 누적 출선량 = 실측 + 선행 + 후행
total_tapped_hot_metal = closed_tap_weight + lead_tap_weight + follow_tap_weight + realtime_tap_weight

# 🔹 예상 누적 생산량 (현재 시각 기준)
elapsed_ratio = elapsed_minutes / 1440  # 하루 1440분 기준
expected_till_now = daily_expected_production * elapsed_ratio

# 🔹 현재 시각 기준 저선량 = 누적생산량 - 출선량
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 🔹 슬래그 자동계산: 누적 용선 출선량 × 고정 슬래그비율
slag_ratio = 0.33  # 슬래그 비율 기본값
accumulated_slag = total_tapped_hot_metal * slag_ratio

# 🔹 저선율 (%)
if expected_till_now > 0:
    residual_rate = residual_molten / expected_till_now * 100
else:
    residual_rate = 0.0

# ============================= 6부: 주요 결과 요약 및 리포트 ============================

st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

# 🌐 예상 누적 생산량
st.subheader("📈 일일 생산량 기준 예측")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재 시각까지 누적 예상 생산량: {expected_till_now:.1f} ton")

# 🔩 실측 출선량
st.subheader("💧 누적 출선량")
st.write(f"종료된 Tap 출선량: {closed_tap_weight:.1f} ton")
st.write(f"선행 Tap 출선량: {lead_tap_weight:.1f} ton")
st.write(f"후행 Tap 출선량: {follow_tap_weight:.1f} ton")
st.write(f"일일 실시간 출선량: {realtime_tap_weight:.1f} ton")
st.write(f"총 누적 출선량: {total_tapped_hot_metal:.1f} ton")

# 🔥 저선량 및 슬래그 자동 계산
st.subheader("🔥 저선량 및 슬래그량 추정")
st.write(f"현재 시각 기준 저선량 (예측): {residual_molten:.1f} ton")
st.write(f"누적 슬래그량 (자동계산): {accumulated_slag:.1f} ton")
st.write(f"저선율: {residual_rate:.1f} %")

# 🔴 저선 경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

st.subheader("⚠️ 조업 상태 진단")
st.write(f"조업 상태: {status}")

# ============================= 6부: 출선 관리 및 추천 계산 ============================

st.header("🔧 출선 관리 및 공취예상시간")

# ⏱️ 출선 관련 입력값
lead_elapsed_min = st.sidebar.number_input("선행 출선경과시간 (분)", value=100)
follow_elapsed_min = st.sidebar.number_input("후행 출선경과시간 (분)", value=50)
tap_speed = st.sidebar.number_input("Tap당 평균 출선속도 (ton/min)", value=9.0)
tap_interval = st.sidebar.number_input("선행폐쇄후 차기출선간격 (분)", value=15.0)

# 🔢 예상 폐쇄시각 및 공취 예상 시간
lead_expected_tap_time = lead_tap_weight / tap_speed if tap_speed > 0 else 0
lead_expected_closure = lead_expected_tap_time - lead_elapsed_min
ai_predicted_closure_min = max(lead_expected_closure, 0)

# ⏱️ 전체 예상 출선시간
total_expected_tap_time = (lead_tap_weight + follow_tap_weight) / tap_speed if tap_speed > 0 else 0

# ⏱️ 잔여 공취 시간
ai_remain_tap_time = max(total_expected_tap_time - (lead_elapsed_min + follow_elapsed_min), 0)

# 🛠️ 추천 출선 전략
if tap_speed > 0:
    recommended_interval = total_expected_tap_time + tap_interval
    recommended_bit_dia = round(tap_speed * 1.2, 2)  # 가정: 1.2배 보정계수

# 🧠 출력
st.subheader("🤖 AI 기반 출선 추천 계산")
st.write(f"선행 예상 폐쇄까지 남은시간: {ai_predicted_closure_min:.1f} 분")
st.write(f"AI 공취예상 잔여시간: {ai_remain_tap_time:.1f} 분")
st.write(f"Tap 총 출선소요시간(예상): {total_expected_tap_time:.1f} 분")
st.write(f"추천 출선간격: {recommended_interval:.1f} 분")
st.write(f"추천 비트경 (AI 자동): {recommended_bit_dia:.1f} mm")

# ============================= 7부: 실시간 시각화 ============================

st.subheader("📊 실시간 용융물 수지 시각화")

# 시계열 시간축 설정 (15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량 시뮬레이션 (송풍 기준 예상 일일생산량 기반)
gen_series = []
for t in time_labels:
    prod = daily_expected_production * (t / 1440)
    gen_series.append(prod)

# 누적 출선량 고정값 (Tap 실측 기준)
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선량 시계열 = 누적생산 - 누적출선
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화 출력
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)", linestyle='--')

plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.legend()
plt.grid(True)

st.pyplot(plt)

# ============================ 8부: 누적 리포트 기록 ============================

st.subheader("📋 누적 조업 리포트 기록")

# 누적 리포트 항목 정의
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "일일예상생산량(t/day)": daily_expected_production,
    "현재시각까지 누적생산(t)": expected_till_now,
    "누적출선량(t)": total_tapped_hot_metal,
    "현재저선량(t)": residual_molten,
    "저선율(%)": residual_rate,
    "조업상태": status,
    "선행출선량(t)": lead_tap_weight,
    "후행출선량(t)": follow_tap_weight,
    "종료된Tap출선량(t)": closed_tap_weight,
    "일일실시간출선(t)": realtime_tap_weight,
    "경과시간(min)": elapsed_minutes
}

# 세션 기록 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)

# 최대 500건 유지
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 표 형태로 출력
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

# ============================ 9부: 마무리 안내 및 제작 정보 ============================

st.markdown("---")
st.markdown("#### 🛠️ BlastTap 10.3 Pro — AI 기반 고로조업 통합 시스템")
st.markdown("- **제작자**: 신동준 ")
st.markdown("- **업데이트일**: 2025-06 기준 최종 반영")
st.markdown("- **기능요약**:")
st.markdown("""
    • 일일 생산량 예측 (송풍기준 및 환원계수 기반 동시표기)  
    • 출선량·저선량 실시간 반영  
    • 비상조업/감풍조업 자동 환산 보정  
    • 실시간 시각화 및 저선 경고  
    • 리포트 저장 및 CSV 다운로드 지원  
""")
st.markdown("- **오류신고/기능개선요청**: GitHub 또는 내부 시스템을 통해 접수 바랍니다")

st.info("💡 모든 조업 정보는 07시 기준으로 일일 초기화되며, 실시간 출선소요 기반으로 누적 생산량이 자동 보정됩니다.")
st.success("📌 BlastTap 10.3 Pro는 현재 베타 운영 중이며, 조업 안정성과 자동화 연동 고도화를 목표로 지속 개선됩니다.")
