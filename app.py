import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# ✅ 한글 폰트 설정 (OS별 적용)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ✅ Streamlit 기본 페이지 설정
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# ✅ 세션 로그 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# ✅ 기준일자 설정 (07시 교대 기준)
now = datetime.datetime.now()
if now.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# ✅ 현재 시각 기반 경과 시간 계산 (단위: 분)
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)  # 최대 1440분 = 1일

# 📌 현재 시각을 화면에 표시
st.markdown(f"🕒 현재 시각: **{now.strftime('%Y-%m-%d %H:%M:%S')}**, 기준시작: **07:00**, 경과: **{int(elapsed_minutes)}분**")

# 💡 참고: 이후 파트에서 사용될 기준시간은 위에서 계산된 `elapsed_minutes`를 기반으로 함

# ========================= ② 정상조업 입력 =========================
st.sidebar.header("② 정상조업 기본입력")

# 1️⃣ 장입속도 및 장입비율
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# 2️⃣ 장입량 (ton/ch)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("너트코크 장입량 (kg)", value=800.0)

# 3️⃣ O/C 비율 계산 및 출력
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"🧮 O/C 비율: **{ore_coke_ratio:.2f}**")

# 4️⃣ 슬래그/철광석 성분 입력
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_fixed_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)

# 5️⃣ 기본 환원지수 및 용해능력
reduction_efficiency = st.sidebar.number_input("기본 환원율 (환원지수)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800.0)
K_factor = st.sidebar.number_input("환산계수 K", value=0.0024)

# 6️⃣ 송풍·산소 입력
blast_volume = st.sidebar.number_input("송풍량 (Nm3/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm3/hr)", value=36941.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 (%)", value=6.0)

# 7️⃣ 조습·미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm3)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 투입량 (kg/thm)", value=170.0)

# 8️⃣ 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.50)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.90)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180.0)
measured_temp = st.sidebar.number_input("실측 용선온도 Tf (°C)", value=1515.0)

# 9️⃣ 송풍원단위 (Nm3/t)
wind_unit = st.sidebar.number_input("송풍 원단위 (Nm3/t)", value=1189.0)

# 10️⃣ 참고지수: 일일예상 생산량 (송풍 기준)
wind_air_day = blast_volume * 1440 + (oxygen_volume * 24 / 0.21)
daily_production_by_wind = wind_air_day / wind_unit

# ========================= ③ 비상조업 보정 입력 =========================
st.sidebar.header("③ 비상조업 보정입력")
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

# ========================= ④ 감풍/휴풍 보정 입력 =========================
st.sidebar.header("④ 감풍/휴풍 보정입력")
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

# ========================= ⑤ 환원효율 및 생산량 계산 =========================

# 환원계수 보정
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

# 기본 환원효율
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor * 0.9
)

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

if abnormal_active:
    abnormal_gas_effect = 1 + (abnormal_blast_volume - 4000) / 8000
    abnormal_oxygen_boost = 1 + (abnormal_oxygen_enrichment / 10)
    abnormal_humidity_effect = 1 - (abnormal_humidification / 100)
    abnormal_pci_effect = 1 + (abnormal_pci_rate - 150) / 100 * 0.02
    abnormal_temp_effect = temp_effect  # 풍온 동일
    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
        abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor * 0.9
    )
else:
    abnormal_reduction_eff = normal_reduction_eff

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

# ============================= ⑥ 출선 및 저선량 계산 =============================

# ✅ 실측 출선값 (종료된 Tap + 선행 + 후행 + 실시간)
closed_tap_weight = st.sidebar.number_input("종료된 Tap 출선량 (ton)", value=0.0)
lead_tap_weight = st.sidebar.number_input("선행 Tap 출선량 (ton)", value=0.0)
follow_tap_weight = st.sidebar.number_input("후행 Tap 출선량 (ton)", value=0.0)
realtime_tap_weight = st.sidebar.number_input("일일 실시간 용선 출선량 (ton)", value=0.0)

# 🔄 총 누적 출선량 계산
total_tapped_hot_metal = closed_tap_weight + lead_tap_weight + follow_tap_weight + realtime_tap_weight

# 🔢 일일예상생산량 (송풍기준, 보정식 포함)
daily_expected_production = ((blast_volume * 1440) + (oxygen_volume * 24 / 0.21)) / wind_unit

# ⏱️ 현재 시각까지 누적 예상 생산량
elapsed_ratio = elapsed_minutes / 1440
expected_till_now = daily_expected_production * elapsed_ratio

# 🔥 저선량 계산 = 예상 생산 - 총 출선
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 🔶 슬래그 자동계산 (출선량 기반)
slag_ratio = 0.33
accumulated_slag = total_tapped_hot_metal * slag_ratio

# 🔎 Tf 예상값 (AI 환원 조건 기반 예측)
tf_ai_effect = 1510 + ((oxygen_enrichment_manual - 5) * 2) + ((hot_blast_temp - 1150) * 0.05)

# ============================= ⑦ 리포트 출력 요약 =============================

st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

# 🌐 일일 생산량 예측
st.subheader("📈 일일 생산량 예측")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재 시각까지 누적 예상 생산량: {expected_till_now:.1f} ton")

# 🔩 실측 출선량
st.subheader("💧 누적 출선량 요약")
st.write(f"종료된 Tap 출선량: {closed_tap_weight:.1f} ton")
st.write(f"선행 Tap 출선량: {lead_tap_weight:.1f} ton")
st.write(f"후행 Tap 출선량: {follow_tap_weight:.1f} ton")
st.write(f"일일 실시간 출선량: {realtime_tap_weight:.1f} ton")
st.write(f"총 누적 출선량: {total_tapped_hot_metal:.1f} ton")

# 🔥 저선 및 슬래그
st.subheader("🔥 저선량 및 슬래그량 추정")
st.write(f"현재 시각 기준 예상 저선량: {residual_molten:.1f} ton")
st.write(f"누적 슬래그량 (0.33 배율): {accumulated_slag:.1f} ton")

# 🌡️ AI 기반 Tf 온도
st.subheader("🌡️ AI 기반 Tf 예상 온도")
st.write(f"AI 기반 Tf 예상 온도: {tf_ai_effect:.1f} °C")

# ⚠️ 저선 경보 진단
st.subheader("🔴 저선 경보판")
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"
st.write(f"조업 상태 진단: {status}")

# ============================= ⑧ 실시간 시각화 =============================

st.subheader("📊 실시간 용융물 수지 시각화")

# 경과 시간 단위 (15분 간격)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량 시뮬레이션 (송풍 기준 일일 생산량으로 환산)
gen_series = [daily_expected_production * (t / 1440) for t in time_labels]

# 누적 출선량 고정 (현재 시점 누적출선량 기준으로 시계열 고정 표시)
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선량 시계열 = 누적생산 - 누적출선
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화 그래프
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="예상 저선량 (ton)")

plt.xlabel("경과 시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.legend()
plt.grid(True)

st.pyplot(plt)

# ============================= ⑨ 누적 조업 리포트 기록 =============================

st.subheader("📋 누적 조업 리포트 기록")

# 리포트 항목 기록용 dict
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "일일예상생산량(t/day)": daily_expected_production,
    "현재누적생산량(t)": expected_till_now,
    "AI기반출선예측(t)": production_ton_ai,
    "종료된출선량(t)": closed_tap_weight,
    "선행출선량(t)": lead_tap_weight,
    "후행출선량(t)": follow_tap_weight,
    "일일실시간출선량(t)": realtime_tap_weight,
    "총누적출선량(t)": total_tapped_hot_metal,
    "현재저선량(t)": residual_molten,
    "저선율(%)": residual_rate,
    "추천비트경": recommended_bit_diameter,
    "추천출선간격(min)": recommended_interval,
    "선행출선경과(min)": lead_elapsed_time,
    "후행출선경과(min)": follow_elapsed_time,
    "AI기반 Tf예상온도(°C)": predicted_tf,
    "조업상태": status,
    "경과시간(min)": elapsed_minutes
}

# 세션 state에 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)

# 500건 초과 시 oldest 삭제
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 데이터프레임으로 시각화
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

# ============================= ⑩ 마무리 안내 및 제작 정보 =============================

st.markdown("---")
st.markdown("#### 🛠️ BlastTap 10.3 Pro — AI 기반 고로조업 통합 시스템")
st.markdown("- 제작자: **신동준** ")
st.markdown("- 최종 업데이트: **2025년 6월 기준**")
st.markdown("- 구성 항목: 입력 > 계산 > 실측 반영 > 출선 및 저선량 > 예상온도 > 시각화 > CSV 저장")
st.markdown("- 기능: 일일생산량 예측, 실시간 저선관리, 출선간격 제안, 온도예측, 기록 저장 및 시각화")

st.info("💡 모든 조업 지표는 매일 **07시 기준으로 초기화**되며, 실시간 데이터에 따라 자동 갱신됩니다.")
st.success("📌 현재 버전은 **BlastTap 10.3 Pro** 베타이며, 고로조업 최적화 및 예측정확도 개선을 목표로 지속 개발 중입니다.")
