import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# 한글 폰트 설정 (OS 자동 인식)
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
else:
    matplotlib.rcParams['font.family'] = 'NanumGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="BlastTap 10.0 Pro — 감풍·휴풍 통합 AI 고로조업엔진", layout="wide")
st.title("🔥 BlastTap 10.0 Pro — 감풍·휴풍 통합 AI 고로조업지원 엔진")

# 세션 상태 초기화 (누적 기록용)
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

# ✅ 정상조업 입력부
st.sidebar.header("① 정상조업 기본입력")

charging_time_per_charge = st.sidebar.number_input("1 Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그 비율 (용선:슬래그)", value=2.25)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7175.0)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.92)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1183.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=90.0)

# ✅ 산소부화량·부화율 입력
oxygen_enrichment_manual = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=37062.0)
oxygen_ratio_input = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)
oxygen_ratio_auto = (oxygen_enrichment_manual * 60) / (blast_volume * 60 * 0.21)
st.sidebar.write(f"자동 산소부화율 계산: {oxygen_ratio_auto:.2f}%")

# ✅ 송풍원단위 입력
wind_unit = st.sidebar.number_input("송풍원단위 (Nm³/t)", value=1189.0)

# ✅ 체류시간·K보정
melting_delay = st.sidebar.number_input("체류시간 (분)", value=240)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

adjusted_elapsed_minutes = elapsed_minutes
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# ✅ 비상조업 입력부 (기존 구조)
st.sidebar.header("② 비상조업 입력")

abnormal_active = st.sidebar.checkbox("비상조업 적용", value=False)
if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))
    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)
    abnormal_oxygen = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_enrichment_manual)
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 (kg/thm)", value=pci_rate)
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍원단위 (Nm³/t)", value=wind_unit)

# ✅ 감풍·휴풍 보정 입력부 (신규 추가)
st.sidebar.header("③ 감풍·휴풍 입력")

air_reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)
if air_reduction_active:
    # 감풍구간 입력
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(7, 0))
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(9, 0))
    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm³/min)", value=5000.0)

    # 휴풍구간 입력
    blowoff_start_time = st.sidebar.time_input("휴풍 시작시각", value=datetime.time(9, 0))
    blowoff_end_time = st.sidebar.time_input("휴풍 종료시각", value=datetime.time(10, 0))

# 🔧 시간분할 경과시간 초기화
normal_elapsed = adjusted_elapsed_minutes
abnormal_elapsed = 0
reduction_elapsed = 0
blowoff_elapsed = 0

# ✅ 비상조업 구간 시간 분리
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)

    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60, elapsed_minutes - normal_elapsed), 0)

# ✅ 감풍·휴풍 시간 분리 (비상조업과 병합)
if air_reduction_active:
    reduction_start_dt = datetime.datetime.combine(base_date, reduction_start_time)
    reduction_end_dt = datetime.datetime.combine(base_date, reduction_end_time)
    blowoff_start_dt = datetime.datetime.combine(base_date, blowoff_start_time)
    blowoff_end_dt = datetime.datetime.combine(base_date, blowoff_end_time)

    # 감풍구간 시간 계산
    reduction_elapsed = max(min((reduction_end_dt - reduction_start_dt).total_seconds() / 60, elapsed_minutes - normal_elapsed), 0)

    # 휴풍구간 시간 계산
    blowoff_elapsed = max(min((blowoff_end_dt - blowoff_start_dt).total_seconds() / 60, elapsed_minutes - (normal_elapsed + reduction_elapsed)), 0)

    # 남은 시간 (비감풍구간)
    normal_elapsed = elapsed_minutes - (reduction_elapsed + blowoff_elapsed + abnormal_elapsed)

# ✅ 생산속도 계산함수 (구간별 송풍량 적용)
def calculate_hourly_production(blast_vol, oxygen_vol, humid, pci, temp, K):
    size_effect = 1.0
    melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
    gas_effect = 1 + (blast_vol - 4000) / 8000
    oxygen_ratio = (oxygen_vol * 60) / (blast_vol * 60 * 0.21)
    oxygen_boost = 1 + (oxygen_ratio / 10)
    humidity_effect = 1 - (humid / 100)
    pressure_boost = 1 + (top_pressure - 2.5) * 0.05
    blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
    temp_effect = 1 + ((temp - 1100) / 100) * 0.03
    pci_effect = 1 + (pci - 150) / 100 * 0.02

    reduction_eff = size_effect * melting_effect * gas_effect * oxygen_boost * \
                    humidity_effect * pressure_boost * blow_pressure_boost * temp_effect * pci_effect * K * 0.9
    ore_hour = ore_per_charge * charge_rate
    fe_hour = ore_hour * (tfe_percent / 100)
    production_hour = fe_hour * reduction_eff
    return production_hour

# ✅ 정상조업 생산량
normal_hourly = calculate_hourly_production(blast_volume, oxygen_enrichment_manual, humidification, pci_rate, hot_blast_temp, K_factor)
normal_production = normal_hourly * (normal_elapsed / 60)

# ✅ 비상조업 생산량
if abnormal_active:
    abnormal_hourly = calculate_hourly_production(abnormal_blast_volume, abnormal_oxygen, abnormal_humidification, abnormal_pci_rate, hot_blast_temp, K_factor)
    abnormal_production = abnormal_hourly * (abnormal_elapsed / 60)
else:
    abnormal_production = 0

# ✅ 감풍 생산량
if air_reduction_active:
    reduction_hourly = calculate_hourly_production(reduction_blast_volume, oxygen_enrichment_manual, humidification, pci_rate, hot_blast_temp, K_factor)
    reduction_production = reduction_hourly * (reduction_elapsed / 60)
    blowoff_production = 0  # 휴풍은 송풍량 0 → 생산량 0
else:
    reduction_production = 0
    blowoff_production = 0

# ✅ 누적 AI 이론생산량 (전체 통합)
production_ton_ai = normal_production + abnormal_production + reduction_production + blowoff_production

# ✅ 체류시간 보정 적용
if adjusted_elapsed_minutes > melting_delay:
    active_minutes = adjusted_elapsed_minutes - melting_delay
else:
    active_minutes = 0

effective_production_ton = production_ton_ai * (active_minutes / adjusted_elapsed_minutes)

# ✅ 실측 TAP 기반 출선량 입력
st.sidebar.header("④ 실측 TAP 출선 실적 입력")

completed_taps = st.sidebar.number_input("종료된 TAP 수 (EA)", value=6)
tap_avg_output = st.sidebar.number_input("TAP당 평균 출선량 (ton)", value=1250.0)

tap_total_output = completed_taps * tap_avg_output

# ✅ 이중수지 평균 생산량 (AI+실측 병합)
avg_total_production = (effective_production_ton + tap_total_output) / 2
avg_total_production = max(avg_total_production, 0)

# ✅ 선행/후행 출선 실적 입력
st.sidebar.header("⑤ 실시간 선행/후행 출선 실적 입력")

# 선행 출선 입력
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=5.0)
lead_slag_ratio = st.sidebar.number_input("선행 슬래그 비율 (용선:슬래그)", value=slag_ratio)

# 후행 출선 입력
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=5.0)
follow_slag_ratio = st.sidebar.number_input("후행 슬래그 비율 (용선:슬래그)", value=slag_ratio)

# ✅ 실시간 경과시간 계산
lead_start_dt = datetime.datetime.combine(base_date, lead_start_time)
follow_start_dt = datetime.datetime.combine(base_date, follow_start_time)

lead_elapsed = max((now - lead_start_dt).total_seconds() / 60, 0)
follow_elapsed = max((now - follow_start_dt).total_seconds() / 60, 0)

# ✅ 실시간 누적 출선량 계산
lead_output = lead_elapsed * lead_speed
follow_output = follow_elapsed * follow_speed

# ✅ 실시간 누적 용선출선량
total_tapped_hot_metal = tap_total_output + lead_output + follow_output

# ✅ 누적 슬래그출선량 (자동계산)
lead_slag_output = lead_output / lead_slag_ratio
follow_slag_output = follow_output / follow_slag_ratio
tap_slag_output = tap_total_output / slag_ratio

total_tapped_slag = lead_slag_output + follow_slag_output + tap_slag_output

# ✅ 저선량 추적 (잔류용융물량)
residual_molten = avg_total_production - total_tapped_hot_metal
residual_molten = max(residual_molten, 0)
residual_rate = (residual_molten / avg_total_production) * 100 if avg_total_production > 0 else 0

# ✅ 저선경보판
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상운전"

# ✅ AI 추천 비트경
if residual_molten < 100 and residual_rate < 5:
    tap_diameter = 43
elif residual_molten < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# ✅ AI 추천 차기 출선간격
if residual_rate < 5:
    next_tap_interval = "15~20분"
elif residual_rate < 9:
    next_tap_interval = "10~15분"
elif residual_rate < 12:
    next_tap_interval = "5~10분"
else:
    next_tap_interval = "즉시 (0~5분)"

# ✅ 동시출선 예상 잔여출선시간 계산 (공취예상시간)

# 선행 출선 잔여량
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1250.0)
lead_remain = max(lead_target - lead_output, 0)
lead_remain_time = lead_remain / lead_speed if lead_speed > 0 else 0

# 후행 잔여시간
follow_remain_time = max((lead_remain_time - follow_elapsed), 0)

# 공취 예상시간 (선행-후행 간격 기반 실시간 공취 시점 추적)
gap_minutes = max(lead_remain_time - follow_elapsed, 0)

# 📊 실시간 용융물 수지 시각화

st.header("📈 실시간 용융물 수지곡선")

# 시간축 생성 (15분 간격)
time_labels = [i for i in range(0, int(adjusted_elapsed_minutes) + 1, 15)]

# 이론 누적 생산량 시뮬레이션 (AI 수지 기반)
gen_series = [
    ore_per_charge * (charge_rate * (t / 60)) * (tfe_percent / 100) * normal_hourly / (ore_per_charge * charge_rate)
    for t in time_labels
]

# 체류시간 보정 반영
gen_series = [
    g * (max(t - melting_delay, 0) / t) if t > 0 else 0
    for g, t in zip(gen_series, time_labels)
]

# 최종 누적 AI 생산량 시뮬레이션 제한
gen_series = [min(g, avg_total_production) for g in gen_series]

# 누적 출선량 시뮬레이션
tap_series = [total_tapped_hot_metal] * len(time_labels)
residual_series = [max(g - total_tapped_hot_metal, 0) for g in gen_series]

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="AI 누적 생산량 (ton)")
plt.plot(time_labels, tap_series, label="누적 용선출선량 (ton)")
plt.plot(time_labels, residual_series, label="잔류 저선량 (ton)")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융물 수지곡선")
plt.legend()
plt.grid()
st.pyplot(plt)

# ✅ AI 리포트 출력
st.header("📊 AI 실시간 통합 조업 리포트")

st.write(f"AI 이론생산량 (누적): {production_ton_ai:.1f} ton")
st.write(f"체류시간 보정 생산량: {effective_production_ton:.1f} ton")
st.write(f"실시간 TAP 누적 용선출선량: {tap_total_output:.1f} ton")
st.write(f"실시간 선행 출선량: {lead_output:.1f} ton")
st.write(f"실시간 후행 출선량: {follow_output:.1f} ton")
st.write(f"이중수지 평균 생산량: {avg_total_production:.1f} ton")
st.write(f"누적 용선출선량 (총): {total_tapped_hot_metal:.1f} ton")
st.write(f"누적 슬래그 출선량 (자동): {total_tapped_slag:.1f} ton")
st.write(f"잔류 저선량: {residual_molten:.1f} ton ({residual_rate:.2f}%)")
st.write(f"조업 상태: {status}")
st.write(f"추천 비트경: Ø{tap_diameter}")
st.write(f"차기 출선간격 추천: {next_tap_interval}")
st.write(f"실시간 공취 예상시간: {gap_minutes:.1f} 분")

# ✅ 누적 리포트 기록 (세션 상태 유지)
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "AI생산량": production_ton_ai,
    "체류보정생산량": effective_production_ton,
    "TAP용선출선량": tap_total_output,
    "선행출선량": lead_output,
    "후행출선량": follow_output,
    "이중수지평균": avg_total_production,
    "누적출선량": total_tapped_hot_metal,
    "누적슬래그": total_tapped_slag,
    "저선량": residual_molten,
    "저선율": residual_rate,
    "공취예상시간": gap_minutes,
    "조업상태": status
}
st.session_state['log'].append(record)
if len(st.session_state['log']) > 100:
    st.session_state['log'].pop(0)

# ✅ 누적 리포트 출력 및 CSV 다운로드
st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.0_Report.csv", mime='text/csv')
