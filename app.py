import streamlit as st
import datetime

# -- 세션에 고정시각 변수 선언 --
if 'fixed_now_time' not in st.session_state:
    st.session_state['fixed_now_time'] = datetime.datetime.now().time()
if 'lock_now_time' not in st.session_state:
    st.session_state['lock_now_time'] = False

st.sidebar.header("기준일자 및 현재시각 입력")

# 기준일자 & Tap 시작 기준시각
base_date = st.sidebar.date_input("기준일자 (Tap 기준)", value=datetime.date.today())
day_start_time = st.sidebar.time_input("Tap 시작 기준시각", value=datetime.time(7, 0))

# --- 현재시각 입력과 고정 체크박스 ---
user_now_time = st.sidebar.time_input("현재 시각 (예: 17:00)", value=st.session_state['fixed_now_time'])
lock_now_time = st.sidebar.checkbox("입력한 현재시각 고정", value=st.session_state['lock_now_time'])

if lock_now_time:
    # 고정모드: 입력값이 변경될 때만 업데이트
    if user_now_time != st.session_state['fixed_now_time']:
        st.session_state['fixed_now_time'] = user_now_time
    st.session_state['lock_now_time'] = True
    now_time = st.session_state['fixed_now_time']
else:
    # 해제모드: 매번 최신 입력값 사용
    st.session_state['fixed_now_time'] = user_now_time
    st.session_state['lock_now_time'] = False
    now_time = user_now_time

# 기준일시/현재시각 계산
base_datetime = datetime.datetime.combine(base_date, day_start_time)
now_datetime = datetime.datetime.combine(base_date, now_time)
if now_time < day_start_time:
    now_datetime += datetime.timedelta(days=1)
elapsed_minutes = (now_datetime - base_datetime).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

# 안내문
st.write(f"**기준일시:** {base_datetime.strftime('%Y-%m-%d %H:%M')} ~ {(base_datetime + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}")
st.write(f"**현재시각:** {now_datetime.strftime('%Y-%m-%d %H:%M')}")
st.write(f"**경과분:** {elapsed_minutes:.1f}분 (현재시각 체크 고정: {'ON' if lock_now_time else 'OFF'})")

# --------------------- 2부: 정상조업 입력 ---------------------
st.sidebar.header("① 정상조업 기본입력")

# 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge if charging_time_per_charge > 0 else 0

# 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)

# O/C 자동표시 (계산)
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"**O/C 비율:** {ore_coke_ratio:.2f}")

# 철광석 성분 (슬래그비율·기본환원율은 자동표시)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# 슬래그비율 자동(예: 2.25), 기본환원율 자동(예: 1.0)
auto_slag_ratio = round(ore_coke_ratio * 0.15, 2)   # 예시 공식(원하는 값 조정)
auto_reduction_eff = round(0.8 + ore_coke_ratio * 0.02, 3)  # 예시 공식
st.sidebar.markdown(f"**[자동] 슬래그 비율:** {auto_slag_ratio:.2f}")
st.sidebar.markdown(f"**[자동] 기본 환원율:** {auto_reduction_eff:.3f}")

slag_ratio = auto_slag_ratio
reduction_efficiency = auto_reduction_eff

# 용해능력
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 송풍 및 산소
blast_volume = st.sidebar.number_input("송풍량 (Nm3/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm3/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

# 조습 및 미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm3)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

# 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm2)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm2)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

# 송풍 원단위 (Nm3/t)
wind_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

# --------------------- 3부: 비상조업/감풍·휴풍 보정입력 ---------------------
st.sidebar.header("② 비상조업/감풍·휴풍 보정입력")

# 비상조업 체크박스
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False, key="abnormal_active")
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0), key="abnormal_start_time")
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0), key="abnormal_end_time")

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0, key="abnormal_charging_delay")
    abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정 (분)", value=300, key="abnormal_total_melting_delay")

    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm3/min)", value=blast_volume, key="abnormal_blast_volume")
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm3/hr)", value=oxygen_volume, key="abnormal_oxygen_volume")
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual, key="abnormal_oxygen_enrichment")
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm3)", value=humidification, key="abnormal_humidification")
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate, key="abnormal_pci_rate")
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm3/t)", value=wind_unit, key="abnormal_wind_unit")

# 감풍·휴풍 체크박스
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False, key="reduction_active")
if reduction_active:
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0), key="reduction_start_time")
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0), key="reduction_end_time")

    reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간 (분)", value=0, key="reduction_charging_delay")
    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm3/min)", value=blast_volume, key="reduction_blast_volume")
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm3/hr)", value=oxygen_volume, key="reduction_oxygen_volume")
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual, key="reduction_oxygen_enrichment")
    reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm3)", value=humidification, key="reduction_humidification")
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 (kg/thm)", value=pci_rate, key="reduction_pci_rate")
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위 (Nm3/t)", value=wind_unit, key="reduction_wind_unit")

# --------------------- 4부: 출선관리/추적 입력 ---------------------
st.sidebar.header("③ 출선관리/추적 입력")

with st.sidebar.expander("종료된 Tap 정보 입력", expanded=True):
    tap_count = st.number_input("종료된 Tap 수", value=0, step=1, min_value=0, key="tap_count")
    fixed_avg_tap_time = st.number_input("평균 TAP당 출선소요시간(분)", value=252.0, key="fixed_avg_tap_time")
    fixed_avg_tap_speed = st.number_input("평균 TAP당 출선속도(ton/min)", value=4.5, key="fixed_avg_tap_speed")
    fixed_avg_tap_output = st.number_input("평균 TAP당 출선량(ton)", value=1200.0, key="fixed_avg_tap_output")
    # 자동산출 (실측입력 우선, 없으면 자동계산)
    closed_tap_weight_auto = tap_count * fixed_avg_tap_output

# 실측값(수동)과 자동값 중 실측 우선
closed_tap_weight = st.sidebar.number_input("종료된 Tap 출선량(ton, 실측입력시 우선)", value=closed_tap_weight_auto, key="closed_tap_weight")

with st.sidebar.expander("선행/후행 실시간 출선정보", expanded=True):
    # 선행/후행 출선 실측
    lead_elapsed_time = st.number_input("선행 출선시간(분)", value=0.0, key="lead_elapsed_time")
    lead_speed = st.number_input("선행 출선속도(ton/min)", value=fixed_avg_tap_speed, key="lead_speed")
    lead_output_ai = lead_elapsed_time * lead_speed
    lead_output_measured = st.number_input("선행 출선량(ton, 실측값 입력시 우선)", value=lead_output_ai, key="lead_output_measured")

    follow_elapsed_time = st.number_input("후행 출선시간(분)", value=0.0, key="follow_elapsed_time")
    follow_speed = st.number_input("후행 출선속도(ton/min)", value=fixed_avg_tap_speed, key="follow_speed")
    follow_output_ai = follow_elapsed_time * follow_speed
    follow_output_measured = st.number_input("후행 출선량(ton, 실측값 입력시 우선)", value=follow_output_ai, key="follow_output_measured")

# 실시간 누적배출량(자동계산)
realtime_tap_weight_auto = closed_tap_weight + lead_output_measured + follow_output_measured
realtime_tap_weight = st.sidebar.number_input(
    "일일 실시간 누적배출량(ton, 실측값 입력시 우선)", value=realtime_tap_weight_auto, key="realtime_tap_weight"
)

# 누적 출선량 계산(실측 우선)
total_tapped_hot_metal = realtime_tap_weight

# ==================== 5부: 주요 산출/수지/진단/AI 추천 ====================

st.header("④ 수지/AI 진단 및 추천")

# 1. 현재시각 기준 누적예상생산량 (송풍기준)
elapsed_ratio = elapsed_minutes / 1440   # 일 단위 비율
wind_air_day = (blast_volume * 1440) + (oxygen_volume * 24 / 0.21)
daily_expected_production = wind_air_day / wind_unit
expected_till_now = daily_expected_production * elapsed_ratio

# 2. 누적 출선량 (종료된 Tap+선행+후행+실시간)
total_tapped_hot_metal = realtime_tap_weight

# 3. 저선량(ton) = 현재시각 기준 누적예상생산량 - 누적 출선량
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / expected_till_now) * 100 if expected_till_now > 0 else 0

# 4. 슬래그 자동계산 (누적출선 × 슬래그비율)
slag_ratio_auto = 0.33
accumulated_slag = total_tapped_hot_metal * slag_ratio_auto

# 5. AI 기반 용선온도 예측 (Tf)
pci_ton_hr = pci_rate * daily_expected_production / 1000
try:
    tf_predict = (
        (hot_blast_temp * 0.836)
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1000000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except Exception:
    tf_predict = 0
tf_predict = max(tf_predict, 1200)

# 6. 출선전략: 추천 비트경·차기출선간격(저선기준)
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# 7. 선행 폐쇄예상Lap시간 (후행 시작 후 150분 도달 시)
if lead_elapsed_time > 0 and follow_elapsed_time > 0:
    lap_time = max(150 - follow_elapsed_time, 0)
else:
    lap_time = 0

# 8. AI공취예상 잔여시간 (선행 목표출선량-현재출선량/출선속도)
lead_target = fixed_avg_tap_output
lead_remain = max(lead_target - lead_output_measured, 0)
ai_gap_minutes = lead_remain / lead_speed if lead_speed > 0 else 0

# 9. 진단 경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

# =================== 주요 결과표시 ====================
st.subheader("💡 생산·출선·진단·AI추천")

st.write(f"예상 일일생산량(송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재시각 기준 누적 예상생산량: {expected_till_now:.1f} ton")
st.write(f"현재시각 기준 누적 출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"현재시각 기준 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"누적 슬래그량(자동): {accumulated_slag:.1f} ton")
st.write(f"AI 기반 Tf예상온도(°C, 참고지수): {tf_predict:.1f}")

st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"선행 폐쇄예상 Lap시간(분): {lap_time:.1f}")
st.write(f"AI 공취예상 잔여시간(분): {ai_gap_minutes:.1f}")
st.write(f"조업상태 진단: {status}")

# ======================= 6부: 실시간 수지 시각화 =======================
st.subheader("📊 실시간 용융물 수지 시각화")

# 시계열 시간축(예: 15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 누적 생산량 시계열 (예상)
gen_series = []
for t in time_labels:
    prod = daily_expected_production * (t / 1440)
    gen_series.append(prod)

# 누적 출선량 시계열 (현재시각까지 실측 출선량은 변하지 않음)
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선량 시계열 (예상 생산 - 출선)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 플롯
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)")
plt.plot(time_labels, residual_series, label="저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# ======================= 7부: 누적 리포트 기록 =======================
st.subheader("📋 누적 조업 리포트 기록")

# 리포트 항목 기록용 dict
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "일일예상생산량(t/day)": daily_expected_production,
    "현재시각기준예상생산량(t)": expected_till_now,
    "현재시각기준출선량(t)": total_tapped_hot_metal,
    "현재저선량(t)": residual_molten,
    "저선율(%)": residual_rate,
    "슬래그량(t)": accumulated_slag,
    "AI기반Tf예상온도": tf_predict,
    "추천비트경": tap_diameter,
    "추천출선간격": next_tap_interval,
    "Lap예상(분)": lap_time,
    "AI공취잔여시간(분)": ai_gap_minutes,
    "조업상태": status,
    "현재경과시간(min)": elapsed_minutes
}

# 세션에 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []
st.session_state['log'].append(record)

# 500건 초과 시 oldest 삭제
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 테이블 표시
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드 버튼
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')
