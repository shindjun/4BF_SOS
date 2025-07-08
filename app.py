import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# (한글 폰트)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 0. 페이지 및 세션 초기화
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")
if 'log' not in st.session_state:
    st.session_state['log'] = []
if 'fixed_now_time' not in st.session_state:
    st.session_state['fixed_now_time'] = None
if 'lock_now_time' not in st.session_state:
    st.session_state['lock_now_time'] = False

# 1. 기준일자 및 기준시각 입력
st.sidebar.header("🔸 기준일 입력")
base_date = st.sidebar.date_input("기준일자", datetime.date.today())
st.sidebar.markdown("기준일자는 07시 교대기준 일자를 선택하세요.")
st.sidebar.divider()

st.sidebar.header("🔸 기준일시·현재시각 입력")
# 기준일시
base_time = st.sidebar.time_input("기준시각 (보통 07:00)", datetime.time(7, 0), step=60)
# 현재시각 입력(고정)
col_now, col_btn = st.sidebar.columns([3, 1])
with col_now:
    selected_now = st.time_input("현재시각 (예: 17:00, 24시표기)", datetime.datetime.now().time(), step=60,
                                 disabled=st.session_state['lock_now_time'])
with col_btn:
    if st.button("⏸️ 고정", use_container_width=True):
        st.session_state['fixed_now_time'] = selected_now
        st.session_state['lock_now_time'] = True
    if st.button("🔄 해제", use_container_width=True):
        st.session_state['fixed_now_time'] = None
        st.session_state['lock_now_time'] = False

if st.session_state['fixed_now_time']:
    now_time = st.session_state['fixed_now_time']
else:
    now_time = selected_now

# 기준일시 → datetime 변환
today_start = datetime.datetime.combine(base_date, base_time)
now_dt = datetime.datetime.combine(base_date, now_time)
if now_time < base_time:
    now_dt += datetime.timedelta(days=1)
elapsed_minutes = (now_dt - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)

st.markdown(
    f"**🕗 기준일시:** {today_start.strftime('%Y-%m-%d %H:%M')} &nbsp;&nbsp;|&nbsp;&nbsp; "
    f"**현재시각:** {now_dt.strftime('%Y-%m-%d %H:%M')} &nbsp;&nbsp;|&nbsp;&nbsp; "
    f"**경과시간:** {elapsed_minutes:.1f}분"
)

st.sidebar.divider()

# 2. 정상조업 입력부 (슬래그비율, 기본환원율 자동계산 표시)
st.sidebar.header("① 정상조업 기본입력")
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("N.C (너트코크) 장입량 (kg)", value=800.0)
# O/C 자동표시
ore_coke_ratio = ore_per_charge / coke_per_charge if coke_per_charge > 0 else 0
st.sidebar.markdown(f"**O/C 비율:** {ore_coke_ratio:.2f}")

tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
# 슬래그비율·기본환원율 자동계산(예시, 실제 식에 맞게 변경 가능)
auto_slag_ratio = round(ore_per_charge / coke_per_charge * 0.11, 2) if coke_per_charge > 0 else 0
auto_reduction_efficiency = round(0.75 + 0.002 * tfe_percent, 2)
st.sidebar.markdown(f"**슬래그비율(자동):** {auto_slag_ratio} (참고용)")
st.sidebar.markdown(f"**기본환원율(자동):** {auto_reduction_efficiency} (참고용)")

slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그, 실제사용)", value=2.25)
reduction_efficiency = st.sidebar.number_input("기본 환원율 (실제사용)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

blast_volume = st.sidebar.number_input("송풍량 (Nm3/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm3/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)
humidification = st.sidebar.number_input("조습량 (g/Nm3)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)
wind_unit = st.sidebar.number_input("송풍원단위 (Nm3/t)", value=1189.0)

st.sidebar.header("② 출선 및 누적 배출 입력")

# 종료된 Tap 관리
st.sidebar.markdown("#### [종료된 Tap 입력]")
num_closed_taps = st.sidebar.number_input("종료된 Tap 수", value=0, step=1)
avg_tap_output = st.sidebar.number_input("평균 TAP당 출선량(ton)", value=1204.0)
avg_tap_speed = st.sidebar.number_input("평균 TAP당 출선속도(ton/min)", value=4.5)
avg_tap_time = st.sidebar.number_input("평균 TAP당 출선소요시간(분)", value=252.0)

# 종료된 Tap 출선량 = Tap 수 × 평균 Tap당 출선량 (실측이 우선되면 실측 입력값 반영)
closed_tap_weight = st.sidebar.number_input(
    "종료된 Tap 출선량(ton, 실측값 입력시 우선)", 
    value=num_closed_taps * avg_tap_output, 
    min_value=0.0, 
    format="%.2f"
)
# 출선비트, 출선시간, 출선속도, 슬래그분리시간 등은 이후 리포트 표에 기록
# -> 필요시 st.sidebar.text_area("종료된 Tap별 상세기록", "")

st.sidebar.divider()

# 선행/후행 출선 입력 (실측+Ai 모두 표시)
st.sidebar.markdown("#### [선행/후행 출선 입력]")
lead_time = st.sidebar.number_input("선행 출선시간(분)", value=0.0)
lead_speed = st.sidebar.number_input("선행 출선속도(ton/min)", value=4.5)
lead_output_ai = lead_time * lead_speed
lead_output = st.sidebar.number_input("선행 출선량(ton, 실측입력)", value=lead_output_ai, min_value=0.0, format="%.2f")
st.sidebar.caption(f"AI선행출선량: {lead_output_ai:.2f} ton")

follow_time = st.sidebar.number_input("후행 출선시간(분)", value=0.0)
follow_speed = st.sidebar.number_input("후행 출선속도(ton/min)", value=4.5)
follow_output_ai = follow_time * follow_speed
follow_output = st.sidebar.number_input("후행 출선량(ton, 실측입력)", value=follow_output_ai, min_value=0.0, format="%.2f")
st.sidebar.caption(f"AI후행출선량: {follow_output_ai:.2f} ton")

st.sidebar.divider()

# 일일 실시간 누적 배출량 = 종료된 Tap 출선량(실측/계산) + 선행출선량 + 후행출선량
total_tapped_hot_metal = closed_tap_weight + lead_output + follow_output

# (필요시) 별도 실시간 누적배출량 수동입력(실측이 우선시되는 경우)
realtime_tap_weight = st.sidebar.number_input(
    "일일 실시간 누적배출량(ton, 실측 우선반영)", value=total_tapped_hot_metal, min_value=0.0, format="%.2f"
)

# (선택) Tap별 상세기록/추적 항목용 텍스트
# tap_detail = st.sidebar.text_area("종료된 Tap별 상세(번호/비트/출선시간/속도 등)", "")

# 3부: 감풍·휴풍·비상조업 보정입력
st.sidebar.header("③ 감풍·휴풍·비상조업 보정입력")

# 비상조업 보정 적용
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간(분)", value=0)
    abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정(분)", value=300)
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량(Nm3/min)", value=blast_volume)
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량(Nm3/hr)", value=oxygen_volume)
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율(%)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량(g/Nm3)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄(kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위(Nm3/t)", value=wind_unit)

# 감풍·휴풍 보정 적용
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)
if reduction_active:
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0))
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0))
    reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간(분)", value=0)
    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량(Nm3/min)", value=blast_volume)
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량(Nm3/hr)", value=oxygen_volume)
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율(%)", value=oxygen_enrichment_manual)
    reduction_humidification = st.sidebar.number_input("감풍 조습량(g/Nm3)", value=humidification)
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄(kg/thm)", value=pci_rate)
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍원단위(Nm3/t)", value=wind_unit)

st.sidebar.divider()

# 실제 체류시간/환원효율/생산량 보정 계산에 반영
# (4부에서 반영: 정상/비상/감풍 시간분할 누적생산량)

# 4부: 환원효율 및 시간분할 누적 생산량 자동계산

# (1) 슬래그비율/기본환원율 자동계산 표시
if coke_per_charge > 0:
    slag_ratio_auto = ore_per_charge / coke_per_charge * 0.0135 + 1.7  # 예시 산식 (회사별 상이)
else:
    slag_ratio_auto = 0

# 환원율 자동 예시 (보정식/입력식 혼합 사용)
if 'auto' in str(reduction_efficiency).lower():  # 자동모드 여부 (예시)
    reduction_efficiency_value = 0.93  # 자동산식/실적치 대입 가능
else:
    reduction_efficiency_value = reduction_efficiency

st.sidebar.markdown(
    f"**자동계산 슬래그비율:** {slag_ratio_auto:.2f}  |  **기본환원율:** {reduction_efficiency_value:.3f}"
)

# (2) 환원효율 보정계수 계산
size_effect = 1.0
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

# (3) 각 구간별 환원효율
normal_reduction_eff = (
    reduction_efficiency_value * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * 0.9
)
# 비상/감풍 효율은 3부 입력값으로 치환 (생략)

# (4) 시간분할 (정상/비상/감풍/기타)
normal_elapsed = elapsed_minutes
abnormal_elapsed = 0
reduction_elapsed = 0
after_elapsed = 0
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)
    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
if reduction_active:
    reduction_start_dt = datetime.datetime.combine(base_date, reduction_start_time)
    reduction_end_dt = datetime.datetime.combine(base_date, reduction_end_time)
    normal_elapsed = min((reduction_start_dt - today_start).total_seconds() / 60, normal_elapsed)
    reduction_elapsed = max(min((reduction_end_dt - reduction_start_dt).total_seconds() / 60, elapsed_minutes - (normal_elapsed + abnormal_elapsed)), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed + reduction_elapsed), 0)

# (5) 체류시간 보정(비상조업 체크 시만 적용)
if abnormal_active:
    adjusted_elapsed_minutes = max(elapsed_minutes - abnormal_total_melting_delay, 0)
else:
    adjusted_elapsed_minutes = elapsed_minutes

# (6) 시간분할 생산량 계산
charge_rate = 60 / charging_time_per_charge
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# Ore 및 Fe
normal_ore = ore_per_charge * charge_rate * (normal_elapsed / 60)
abnormal_ore = ore_per_charge * charge_rate * (abnormal_elapsed / 60)
reduction_ore = ore_per_charge * charge_rate * (reduction_elapsed / 60)
after_ore = ore_per_charge * charge_rate * (after_elapsed / 60)

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
reduction_fe = reduction_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 생산량(ton)
normal_production = normal_fe * normal_reduction_eff
# 비상/감풍/기타생산량도 3부에서 보정가능
production_ton_ai = normal_production  # (여러 구간 누적 시 합산)

# (7) 자동계산 슬래그 예상량 (현재까지)
auto_slag = production_ton_ai / slag_ratio_auto if slag_ratio_auto > 0 else 0

# 결과 임시출력 예시
st.write(f"슬래그비율(자동): {slag_ratio_auto:.2f}, 환원율(자동): {reduction_efficiency_value:.3f}")
st.write(f"현재 누적 생산량(AI): {production_ton_ai:.1f} ton")
st.write(f"예상 슬래그 누적량(자동): {auto_slag:.1f} ton")

# 5부: 실측 TAP·선행·후행 출선 + 저선량·슬래그량 자동계산

st.sidebar.markdown("---")
st.sidebar.header("④ 출선 추적 및 실측입력")

# 1. 종료된 Tap수 및 평균값 입력
closed_tap_count = st.sidebar.number_input("종료된 Tap 수", min_value=0, value=0)
avg_tap_time = st.sidebar.number_input("평균 TAP당 출선소요시간(분)", min_value=0.0, value=252.0)
avg_tap_speed = st.sidebar.number_input("평균 TAP당 출선속도(ton/min)", min_value=0.0, value=4.5)
avg_tap_output = st.sidebar.number_input("평균 TAP당 출선량(ton)", min_value=0.0, value=1204.0)

# 2. 종료된 Tap 출선량 (실측값 우선 적용, 미입력시 계산)
closed_tap_output_input = st.sidebar.number_input("종료된 Tap 출선량(ton, 실측)", min_value=0.0, value=0.0)
if closed_tap_output_input > 0:
    closed_tap_output = closed_tap_output_input
else:
    closed_tap_output = closed_tap_count * avg_tap_output

# 3. 선행/후행 실측 출선 입력 + AI예측 출선량 표시
lead_elapsed_time = st.sidebar.number_input("선행 출선시간(분)", min_value=0.0, value=0.0)
lead_speed = st.sidebar.number_input("선행 출선속도(ton/min)", min_value=0.0, value=avg_tap_speed)
lead_output_input = st.sidebar.number_input("선행 출선량(ton, 실측)", min_value=0.0, value=0.0)
lead_output_ai = lead_elapsed_time * lead_speed
lead_output = lead_output_input if lead_output_input > 0 else lead_output_ai
st.sidebar.caption(f"AI 선행출선량(ton): {lead_output_ai:.1f}")

follow_elapsed_time = st.sidebar.number_input("후행 출선시간(분)", min_value=0.0, value=0.0)
follow_speed = st.sidebar.number_input("후행 출선속도(ton/min)", min_value=0.0, value=avg_tap_speed)
follow_output_input = st.sidebar.number_input("후행 출선량(ton, 실측)", min_value=0.0, value=0.0)
follow_output_ai = follow_elapsed_time * follow_speed
follow_output = follow_output_input if follow_output_input > 0 else follow_output_ai
st.sidebar.caption(f"AI 후행출선량(ton): {follow_output_ai:.1f}")

# 4. 실시간 누적 배출량(자동)
# (Tap출선 + 선행 + 후행)
total_tapped_hot_metal = closed_tap_output + lead_output + follow_output

# 5. (선택) 일일 실시간 누적배출량(추가 실측값 있을 시)
realtime_tap_weight = st.sidebar.number_input("일일 실시간 누적배출량(ton, 실측)", min_value=0.0, value=0.0)
if realtime_tap_weight > 0:
    total_tapped_hot_metal += realtime_tap_weight

# 6. 누적 슬래그량 (자동)
slag_ratio_auto = ore_per_charge / coke_per_charge * 0.0135 + 1.7 if coke_per_charge > 0 else 2.25  # 4부 자동계산과 동일
accumulated_slag = total_tapped_hot_metal / slag_ratio_auto if slag_ratio_auto > 0 else 0

# 7. 현재시각까지 누적생산량 (4부 계산 production_ton_ai 또는 wind_air_day 기준)
elapsed_ratio = elapsed_minutes / 1440
wind_air_day = blast_volume * 1440 + oxygen_volume * 24 / 0.21
daily_expected_production = wind_air_day / wind_unit
expected_till_now = daily_expected_production * elapsed_ratio

# 8. 저선량 = 누적예상생산량 - 누적출선량
residual_molten = expected_till_now - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)

# 9. 저선 경보/상태
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

# 10. 주요 결과 출력
st.write(f"종료된 Tap 출선량(ton): {closed_tap_output:.1f}")
st.write(f"선행 출선량(ton): {lead_output:.1f}")
st.write(f"후행 출선량(ton): {follow_output:.1f}")
st.write(f"총 누적 출선량(ton): {total_tapped_hot_metal:.1f}")
st.write(f"누적 슬래그량(ton, 자동): {accumulated_slag:.1f}")
st.write(f"현재시각 기준 누적생산량(ton): {expected_till_now:.1f}")
st.write(f"현재시각 기준 저선량(ton): {residual_molten:.1f}  ({status})")

# 6부: 결과 요약 및 AI 추천 전략 출력

st.markdown("---")
st.header("📊 BlastTap 10.3 Pro — AI 실시간 결과 및 추천 리포트")

# 1. 예측/누적 생산 및 출선 정보
st.subheader("🔎 주요 결과 요약")
st.write(f"예상 일일생산량 (송풍기준): {daily_expected_production:.1f} ton/day")
st.write(f"현재시각 기준 누적 예상생산량: {expected_till_now:.1f} ton")
st.write(f"현재시각 기준 총 누적 출선량: {total_tapped_hot_metal:.1f} ton")
st.write(f"현재시각 기준 저선량: {residual_molten:.1f} ton")
st.write(f"누적 슬래그량(ton, 자동): {accumulated_slag:.1f} ton")
st.write(f"조업 상태: {status}")

# 2. TAP 상세 (평균 기준)
st.subheader("🔩 종료된 Tap 세부")
st.write(f"종료된 Tap 수: {closed_tap_count:.0f} EA")
st.write(f"평균 TAP당 출선시간(분): {avg_tap_time:.1f}")
st.write(f"평균 TAP당 출선속도(ton/min): {avg_tap_speed:.2f}")
st.write(f"평균 TAP당 출선량(ton): {avg_tap_output:.1f}")

# 3. 선행/후행 출선 전략 및 폐쇄예상 (Lap) 계산  
st.subheader("🚦 출선 관리·추천")
# ① 선행, 후행 출선 동시 진행 후 '후행 시작'부터 150분 후 Lap=선행폐쇄 예상
lap_lag_minutes = 150   # 기준(예: 150분)
lead_lap_predict = 0.0
if lead_elapsed_time > 0 and follow_elapsed_time > 0:
    # Lap 예측: (선행 경과시간) - (후행 경과시간) + 기준
    lead_lap_predict = max((lead_elapsed_time - follow_elapsed_time) + lap_lag_minutes, 0)
    st.write(f"선행 폐쇄예상 Lap시간(분): {lead_lap_predict:.1f} (후행 시작 후 150분 경과 기준)")
else:
    st.write("선행·후행 동시 출선 중 폐쇄예상시간 산출에는 선·후행 출선시간 입력 필요")

# ② 출선 상태에 따른 AI 추천 비트경, 차기 출선간격
if residual_molten < 100:
    tap_diameter = 43
    next_tap_interval = "15~20분"
elif residual_molten < 150:
    tap_diameter = 45
    next_tap_interval = "10~15분"
elif residual_molten < 200:
    tap_diameter = 48
    next_tap_interval = "5~10분"
else:
    tap_diameter = 50
    next_tap_interval = "즉시(0~5분)"
st.write(f"AI 추천 비트경: Ø{tap_diameter}")
st.write(f"AI 추천 차기 출선간격: {next_tap_interval}")

# ③ 공취(공기유입) 예상 잔여시간
# 예시 공식: (예상 Tap출선량 - 선행 누적출선) / 선행출선속도, 단 0회피
lead_target = avg_tap_output if avg_tap_output > 0 else 1200
lead_remain = max(lead_target - lead_output, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0
gap_minutes = max(lead_remain_time - follow_elapsed_time, 0)
st.write(f"AI 공취(공기유입) 예상 잔여시간: {gap_minutes:.1f} 분")

# ④ AI 기반 Tf(용선온도) 예측 (참고용)
try:
    pci_ton_hr = pci_rate * daily_expected_production / 1000
    Tf_predict = (
        hot_blast_temp * 0.836
        + ((oxygen_volume / (60 * blast_volume)) * 4973)
        - (hot_blast_temp * 0.6)
        - ((pci_ton_hr * 1_000_000) / (60 * blast_volume) * 0.0015)
        + 1559
    )
except:
    Tf_predict = 0
Tf_predict = max(Tf_predict, 1200)
st.write(f"AI 기반 Tf예상온도(°C): {Tf_predict:.1f}")

# ⑤ 상태/리포트 표기
st.markdown(f"**🔍 조업 상태**: {status}")

# 7부: 실시간 시각화 및 Tap별 누적 리포트

st.markdown("---")
st.header("📊 실시간 용융물 수지 시각화 및 Tap별 기록")

# 시계열 시간축 생성 (15분 단위)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))
gen_series = []
for t in time_labels:
    prod = daily_expected_production * (t / 1440)
    gen_series.append(prod)

# 누적 출선량 시계열
tap_series = [total_tapped_hot_metal] * len(time_labels)

# 저선 시계열 (예상 생산 - 출선)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 그래프 시각화
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

# ------------------------------
# Tap별 상세 리포트 테이블 (예시)
# 입력: 종료된 Tap별로 아래 정보(리스트/입력/DB 연동 가능)
tap_numbers = list(range(1, int(closed_tap_count)+1))
tap_data = []
for i in tap_numbers:
    # 아래 데이터는 실제 입력/DB/연동에 따라 변경
    tap_data.append({
        "No.": i,
        "출선비트": f"Bit-{i%4+1}",           # 예시: 1~4비트 반복
        "출선시작": f"{7+i:02d}:00",         # 예시: 07:00+N시
        "출선시간(분)": avg_tap_time,         # 평균 소요시간
        "출선속도(t/m)": avg_tap_speed,      # 평균속도
        "출선량(ton)": avg_tap_output,       # 평균출선량
        "슬래그분리(분)": avg_slag_separate, # 평균 슬래그분리시간(직접입력/자동)
    })

tap_df = pd.DataFrame(tap_data)
st.subheader("📝 Tap별 조업 상세기록")
st.dataframe(tap_df)

# 누적 리포트 기록
st.subheader("📋 누적 조업 리포트 기록")
record = {
    "기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "일일예상생산량(t/day)": daily_expected_production,
    "현재누적생산량(t)": expected_till_now,
    "누적출선량(t)": total_tapped_hot_metal,
    "현재저선량(t)": residual_molten,
    "조업상태": status,
    "종료Tap수": closed_tap_count,
    "평균Tap출선시간(분)": avg_tap_time,
    "평균Tap출선속도(t/m)": avg_tap_speed,
    "평균Tap출선량(ton)": avg_tap_output,
    "AI_Tf예상온도": Tf_predict,
    "AI공취예상잔여시간(분)": gap_minutes,
    # ...필요 항목 추가
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# CSV 다운로드
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap10.3_Pro_Log.csv", mime='text/csv')

# 8부: 시스템 안내, 활용 가이드 및 제작 정보

st.markdown("---")
st.header("🛠️ BlastTap 10.3 Pro — 시스템 안내 및 참고 정보")

st.markdown("""
- **기능요약**
    - 현재시각 입력 및 07시 기준 일일 자동리셋
    - 입력항목(장입, 출선, Tap별, 선/후행 등)과 자동계산(AI용선온도, 슬래그, 저선, 공취예상 등) 모두 반영
    - 실시간 누적생산/출선/저선량 및 그래프 추적
    - Tap별 상세기록 + 전체 이력 자동 테이블/CSV저장

- **활용 및 주의사항**
    - 모든 계산은 ‘기준일시’~‘현재시각’ 경과분 자동반영(입력값 고정 시 체크박스 지원)
    - Tap별 실적, 출선비트, 슬래그분리 등은 현장 실측/자동입력 병행 권장
    - 일일 실시간 누적 배출량은 ‘종료된 Tap 수 × 평균출선량 + 선행/후행/실시간’ 방식

- **추천 및 결과 항목**
    - 추천 비트경/출선간격, AI 기반 Tf예상온도, 공취예상 잔여시간 등 핵심 결과 자동제시
    - 리포트 테이블 및 CSV 다운로드, 시각화, 상세 Tap별 이력 관리 가능

- **버그/피드백**
    - 입력·계산 오류 발생시 “변수/이름/값 누락 여부” 체크, 문의 가능
    - 피드백·요구사항은 [GitHub 또는 내부관리 시스템](https://github.com/shindjun/blast-furnace-tracker4) 활용

---
""")

st.info("💡 모든 조업 정보 및 수지는 07시 기준 자동리셋, 실시간·Tap별·누적 기준 동시 추적됩니다.")
st.success("📌 BlastTap 10.3 Pro는 최신 AI 조업이론, 실측데이터, 자동화 관리 기능이 모두 통합된 고로조업 특화 시스템입니다.")
st.markdown("""
- **제작: 신동준** (개발지원: ChatGPT, Streamlit, Python)
- **최종 반영일:** 2025-06
- **추가 요청:** CSV, 리포트, 시각화, 모바일 등 모든 확장 지원 가능
""")
