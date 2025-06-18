# =========================== 1부: 기본 설정 및 현재시각 입력 ===========================
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform

# ✅ 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rcParams["font.family"] = "Malgun Gothic"
else:
    matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

# ✅ 페이지 기본설정
st.set_page_config(page_title="BlastTap 10.3 Pro — AI 조업엔진", layout="wide")
st.title("🔥 BlastTap 10.3 Pro — AI 기반 고로조업 실시간 통합관리")

# ✅ 세션 로그 초기화
if "log" not in st.session_state:
    st.session_state["log"] = []

# ✅ 현재시각 입력 (사용자 직접 입력: 24시간 형식)
st.sidebar.header("⏱️ 현재 시각 입력")
user_time_input = st.sidebar.time_input("현재 시각 (예: 17:00)", value=datetime.datetime.now().time())

# ✅ 기준일자 설정 (07시 교대 기준)
now = datetime.datetime.combine(datetime.date.today(), user_time_input)
if user_time_input.hour < 7:
    base_date = datetime.date.today() - datetime.timedelta(days=1)
else:
    base_date = datetime.date.today()
today_start = datetime.datetime.combine(base_date, datetime.time(7, 0))

# ✅ 경과 시간 계산 (단위: 분)
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = max(min(elapsed_minutes, 1440), 0)  # 하루 1440분 범위 제한

# ✅ 현재 시각 정보 출력
st.sidebar.markdown(f"**기준일자:** {base_date}")
st.sidebar.markdown(f"**경과시간:** {elapsed_minutes:.1f}분")

# =========================== 2부: 정상조업 입력 ===========================
st.sidebar.header("① 정상조업 기본입력")

# ✅ 장입속도
charging_time_per_charge = st.sidebar.number_input("1Charge 장입시간 (분)", value=11.0)
charge_rate = 60 / charging_time_per_charge

# ✅ 장입량
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.0)
nut_coke_kg = st.sidebar.number_input("너트코크 (kg)", value=800.0)

# ✅ O/C 계산 자동출력
if coke_per_charge > 0:
    ore_coke_ratio = ore_per_charge / coke_per_charge
else:
    ore_coke_ratio = 0
st.sidebar.markdown(f"🔍 **O/C 비율:** `{ore_coke_ratio:.2f}`")

# ✅ 철광석 성분 자동설정
tfe_percent = st.sidebar.number_input("T.Fe 함량 (%)", value=58.0)

# ✅ 슬래그 비율 자동계산 (기준: O/C 비율 기준 추정)
slag_ratio = round(0.2 + ore_coke_ratio * 0.03, 2)  # 예시 수식 기반
st.sidebar.markdown(f"🧪 **자동 계산 슬래그 비율 (용선:슬래그):** `{slag_ratio:.2f}`")

# ✅ 조업지수 및 용해능력
reduction_efficiency = st.sidebar.number_input("기본 환원율 (정상기준)", value=1.00)

# 자동 계산 예시 (실제 적용은 이후 파트에서)
K_factor = 0.9  # 고정 K 계수 예시
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# ✅ 송풍·산소
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=7200.0)
oxygen_volume = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36961.0)
oxygen_enrichment_manual = st.sidebar.number_input("산소부화율 수동입력 (%)", value=6.0)

# ✅ 조습·미분탄
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=14.0)
pci_rate = st.sidebar.number_input("미분탄 취입량 (kg/thm)", value=170)

# ✅ 압력 및 온도
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.9)
hot_blast_temp = st.sidebar.number_input("풍온 (°C)", value=1180)
measured_temp = st.sidebar.number_input("실측 용선온도 (°C)", value=1515.0)

# ✅ 송풍 원단위
wind_unit = st.sidebar.number_input("송풍 원단위 (Nm3/t)", value=1189.0)

# =========================== 3부: 비상조업 + 감풍/휴풍 보정 입력 ===========================

# ✅ 비상조업 보정 입력
st.sidebar.header("② 비상조업 보정 입력")
abnormal_active = st.sidebar.checkbox("비상조업 보정 적용", value=False)

if abnormal_active:
    abnormal_start_time = st.sidebar.time_input("비상 시작시각", value=datetime.time(10, 0))
    abnormal_end_time = st.sidebar.time_input("비상 종료시각", value=datetime.time(13, 0))

    abnormal_charging_delay = st.sidebar.number_input("비상 장입지연 누적시간 (분)", value=0)  
    abnormal_total_melting_delay = st.sidebar.number_input("비상 체류시간 보정 (분)", value=300)  

    abnormal_blast_volume = st.sidebar.number_input("비상 송풍량 (Nm³/min)", value=blast_volume)  
    abnormal_oxygen_volume = st.sidebar.number_input("비상 산소부화량 (Nm³/hr)", value=oxygen_volume)  
    abnormal_oxygen_enrichment = st.sidebar.number_input("비상 산소부화율 (%)", value=oxygen_enrichment_manual)  
    abnormal_humidification = st.sidebar.number_input("비상 조습량 (g/Nm³)", value=humidification)  
    abnormal_pci_rate = st.sidebar.number_input("비상 미분탄 투입량 (kg/thm)", value=pci_rate)  
    abnormal_wind_unit = st.sidebar.number_input("비상 송풍 원단위 (Nm³/t)", value=wind_unit)

# ✅ 감풍·휴풍 보정 입력
st.sidebar.header("③ 감풍·휴풍 보정 입력")
reduction_active = st.sidebar.checkbox("감풍·휴풍 보정 적용", value=False)

if reduction_active:
    reduction_start_time = st.sidebar.time_input("감풍 시작시각", value=datetime.time(15, 0))
    reduction_end_time = st.sidebar.time_input("감풍 종료시각", value=datetime.time(18, 0))

    reduction_charging_delay = st.sidebar.number_input("감풍 장입지연 누적시간 (분)", value=0)  

    reduction_blast_volume = st.sidebar.number_input("감풍 송풍량 (Nm³/min)", value=blast_volume)  
    reduction_oxygen_volume = st.sidebar.number_input("감풍 산소부화량 (Nm³/hr)", value=oxygen_volume)  
    reduction_oxygen_enrichment = st.sidebar.number_input("감풍 산소부화율 (%)", value=oxygen_enrichment_manual)  
    reduction_humidification = st.sidebar.number_input("감풍 조습량 (g/Nm³)", value=humidification)  
    reduction_pci_rate = st.sidebar.number_input("감풍 미분탄 투입량 (kg/thm)", value=pci_rate)  
    reduction_wind_unit = st.sidebar.number_input("감풍 송풍 원단위 (Nm³/t)", value=wind_unit)

# =========================== 4부: 환원효율 계산 및 시간 분할 생산량 계산 ===========================

# 계수 계산용 보정값들
size_effect = (20 / 20 + 60 / 60) / 2  # 통기성
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment_manual / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
temp_effect = 1 + ((hot_blast_temp - 1100) / 100) * 0.03
pci_effect = 1 + (pci_rate - 150) / 100 * 0.02
measured_temp_effect = 1 + ((measured_temp - 1500) / 100) * 0.03

# AI 기반 K 계수 적용
K_factor = 0.9

# 기본 환원효율 (정상조업 기준)
normal_reduction_eff = (
    reduction_efficiency * size_effect * melting_effect * gas_effect *
    oxygen_boost * humidity_effect * pressure_boost * blow_pressure_boost *
    temp_effect * pci_effect * measured_temp_effect * K_factor
)

# 조업시간 분할
normal_elapsed = elapsed_minutes
abnormal_elapsed = 0
reduction_elapsed = 0

# 비상조업 구간 분리
if abnormal_active:
    abnormal_start_dt = datetime.datetime.combine(base_date, abnormal_start_time)
    abnormal_end_dt = datetime.datetime.combine(base_date, abnormal_end_time)
    normal_elapsed = min((abnormal_start_dt - today_start).total_seconds() / 60, elapsed_minutes)
    abnormal_elapsed = max(min((abnormal_end_dt - abnormal_start_dt).total_seconds() / 60,
                               elapsed_minutes - normal_elapsed), 0)
    after_elapsed = max(elapsed_minutes - (normal_elapsed + abnormal_elapsed), 0)
else:
    after_elapsed = max(elapsed_minutes - normal_elapsed, 0)

# 감풍조업 구간 분리
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
    abnormal_temp_effect = temp_effect  # 풍온 동일
    abnormal_reduction_eff = (
        reduction_efficiency * size_effect * melting_effect * abnormal_gas_effect *
        abnormal_oxygen_boost * abnormal_humidity_effect * pressure_boost * blow_pressure_boost *
        abnormal_temp_effect * abnormal_pci_effect * measured_temp_effect * K_factor
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
        reduction_temp_effect * reduction_pci_effect * measured_temp_effect * K_factor
    )
else:
    reduction_reduction_eff = normal_reduction_eff

# 체류시간 보정 반영
if abnormal_active:
    adjusted_elapsed_minutes = max(elapsed_minutes - abnormal_total_melting_delay, 0)
else:
    adjusted_elapsed_minutes = elapsed_minutes

# Charge 수 계산
elapsed_charges = charge_rate * (adjusted_elapsed_minutes / 60)

# Ore량 → Fe량 환산
normal_ore = ore_per_charge * charge_rate * (normal_elapsed / 60)
abnormal_ore = ore_per_charge * charge_rate * (abnormal_elapsed / 60)
reduction_ore = ore_per_charge * charge_rate * (reduction_elapsed / 60)
after_ore = ore_per_charge * charge_rate * (after_elapsed / 60)

normal_fe = normal_ore * (tfe_percent / 100)
abnormal_fe = abnormal_ore * (tfe_percent / 100)
reduction_fe = reduction_ore * (tfe_percent / 100)
after_fe = after_ore * (tfe_percent / 100)

# 생산량 계산 (AI 기반 Fe → ton)
normal_production = normal_fe * normal_reduction_eff
abnormal_production = abnormal_fe * abnormal_reduction_eff
reduction_production = reduction_fe * reduction_reduction_eff
after_production = after_fe * normal_reduction_eff

production_ton_ai = (
    normal_production + abnormal_production + reduction_production + after_production
)

# =========================== 5부: 실측 출선 및 저선량 계산 ===========================

st.sidebar.header("⑤ 출선 입력")

# 출선 기본항목
closed_tap_count = st.sidebar.number_input("종료된 Tap 수", value=0, step=1)
avg_tap_duration = st.sidebar.number_input("평균 Tap당 출선 소요시간 (분)", value=230.0)
avg_tap_speed = st.sidebar.number_input("평균 Tap당 출선 속도 (ton/분)", value=4.7)

# 선행·후행 출선 항목 (실측값 + AI 보정)
lead_elapsed_time = st.sidebar.number_input("선행 출선 시간 (분)", value=120.0)
lead_real_output = st.sidebar.number_input("선행 출선량 (실측 ton)", value=0.0)
lead_ai_output = lead_elapsed_time * avg_tap_speed

follow_elapsed_time = st.sidebar.number_input("후행 출선 시간 (분)", value=90.0)
follow_real_output = st.sidebar.number_input("후행 출선량 (실측 ton)", value=0.0)
follow_ai_output = follow_elapsed_time * avg_tap_speed

# 실시간 출선량 (운전중 계량 포함)
realtime_tap_output = st.sidebar.number_input("일일 실시간 출선량 (ton)", value=0.0)

# 종료된 Tap 출선량 총합 (자동)
closed_tap_output = closed_tap_count * avg_tap_duration * avg_tap_speed / avg_tap_duration  # = count × speed × duration / duration = count × speed

# 총 출선량 (실측 기반)
total_tapped_hot_metal = closed_tap_output + lead_real_output + follow_real_output + realtime_tap_output

# 예상 일일생산량 = (송풍량×1440 + 산소×24 / 0.21) ÷ 송풍원단위
daily_expected_production = ((blast_volume * 1440) + (oxygen_volume * 24 / 0.21)) / wind_unit

# 현재 시각 기반 누적 예상 생산량
elapsed_ratio = elapsed_minutes / 1440
expected_production_until_now = daily_expected_production * elapsed_ratio

# 현재 시각 기준 누적 출선량
actual_tap_output_until_now = closed_tap_output + lead_real_output + follow_real_output + realtime_tap_output

# 현재 시각 기준 저선량 = 누적 생산량 - 누적 출선량
residual_molten = expected_production_until_now - actual_tap_output_until_now
residual_molten = max(residual_molten, 0)

# 슬래그 자동계산 (예: 0.33 비율)
slag_ratio = 0.33
accumulated_slag = actual_tap_output_until_now * slag_ratio

# AI 기반 예상 용선온도 추정 (단순 참고지수)
ai_tf_predicted = measured_temp + (normal_reduction_eff - 1) * 50  # 예: 평균 보정 50°C

# =========================== 6부: 주요 결과 요약 및 리포트 ===========================

st.header("📊 BlastTap 10.3 Pro — AI 고로조업 실시간 리포트")

# 1. 생산량 예측
st.subheader("📈 예상 생산량 (송풍 기준)")
st.write(f"예상 일일생산량 (송풍 기준): **{daily_expected_production:.1f} ton/day**")
st.write(f"현재 시각 기준 누적 예상 생산량: **{expected_production_until_now:.1f} ton**")

# 2. 누적 출선량
st.subheader("💧 현재 누적 출선량")
st.write(f"종료된 Tap 수: {closed_tap_count}개 → 출선량: **{closed_tap_output:.1f} ton**")
st.write(f"선행 출선량 (실측): **{lead_real_output:.1f} ton** (AI예상: {lead_ai_output:.1f} ton)")
st.write(f"후행 출선량 (실측): **{follow_real_output:.1f} ton** (AI예상: {follow_ai_output:.1f} ton)")
st.write(f"일일 실시간 출선량: **{realtime_tap_output:.1f} ton**")
st.write(f"총 누적 출선량: **{actual_tap_output_until_now:.1f} ton**")

# 3. 현재 저선량 및 슬래그량
st.subheader("🔥 현재 시각 기준 저선량 및 슬래그량")
st.write(f"현재 시각 기준 저선량 (예측): **{residual_molten:.1f} ton**")
st.write(f"누적 슬래그량 (자동계산, 비율 {slag_ratio}): **{accumulated_slag:.1f} ton**")

# 4. AI 기반 용선온도 예측
st.subheader("🌡️ AI 기반 예상 용선온도")
st.write(f"실측 용선온도: {measured_temp:.1f} ℃")
st.write(f"AI 기반 Tf 예상 온도 (참고): **{ai_tf_predicted:.1f} ℃**")

# 5. 조업 상태 진단
st.subheader("⚠️ 조업 상태 진단")
if residual_molten >= 200:
    status = "🔴 저선 위험 (비상)"
elif residual_molten >= 150:
    status = "🟠 저선 과다 누적"
elif residual_molten >= 100:
    status = "🟡 저선 관리 권고"
else:
    status = "✅ 정상 운영"

st.write(f"현재 조업 상태: **{status}**")

# =========================== 7부: 실시간 누적 시각화 ===========================

st.subheader("📊 시간대별 생산/출선/저선량 시각화")

# ⏱️ 시계열 시간축 (15분 간격)
time_labels = list(range(0, int(elapsed_minutes) + 1, 15))

# 📈 누적 예상 생산량 시계열
gen_series = [daily_expected_production * (t / 1440) for t in time_labels]

# 📉 누적 출선량은 현재시각 이전까지 실측 기준 고정
tap_series = [actual_tap_output_until_now] * len(time_labels)

# 🔥 누적 저선량 = 생산 - 출선
residual_series = [max(g - actual_tap_output_until_now, 0) for g in gen_series]

# 📊 시각화 출력
plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="📈 누적 예상 생산량 (ton)", linewidth=2)
plt.plot(time_labels, tap_series, label="📉 누적 출선량 (ton)", linestyle='--')
plt.plot(time_labels, residual_series, label="🔥 누적 저선량 (ton)", linestyle='-.')

plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("⏱️ 시간대별 누적 수지 시각화")
plt.grid(True)
plt.legend()
st.pyplot(plt)

# =========================== 8부: 누적 조업 리포트 기록 ===========================

st.subheader("📋 누적 조업 리포트 기록")

# 리포트 항목 딕셔너리 정의
record = {
    "📅 기준시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "현재시각": now.strftime('%H:%M'),
    "예상일일생산량(t/day)": daily_expected_production,
    "현재시각 누적예상생산량(t)": expected_till_now,
    "현재시각 누적출선량(t)": actual_tap_output_until_now,
    "현재시각 기준 저선량(t)": residual_molten_now,
    "저선율(%)": (residual_molten_now / expected_till_now * 100) if expected_till_now > 0 else 0,
    "출선상태": molten_status,
    "종료된Tap수": closed_tap_count,
    "종료된Tap출선량(t)": closed_tap_weight,
    "선행출선량(t)": lead_tap_weight,
    "후행출선량(t)": follow_tap_weight,
    "실시간출선량(t)": realtime_tap_weight,
    "경과시간(min)": elapsed_minutes
}

# 세션 저장소에 저장
if 'log' not in st.session_state:
    st.session_state['log'] = []

st.session_state['log'].append(record)

# 최대 500건까지 기록 유지
if len(st.session_state['log']) > 500:
    st.session_state['log'].pop(0)

# 데이터프레임으로 표시
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)

# 📥 CSV 다운로드 버튼 제공
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="BlastTap_10.3_Log.csv", mime='text/csv')

