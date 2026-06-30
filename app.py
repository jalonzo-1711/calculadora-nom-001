import streamlit as st
import math

# --- 1. BASES DE DATOS (NOM-001-SEDE-2012 / NEC) ---

calibres = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0", "2/0", "3/0", "4/0", "250", "300", "350", "400", "500", "600", "750", "1000"]
index_min_paralelo = calibres.index("1/0")

# Ampacidades
ampacidad_tubo = {
    "14": [15, 20, 25], "12": [20, 25, 30], "10": [30, 35, 40], "8": [40, 50, 55],
    "6": [55, 65, 75], "4": [70, 85, 95], "3": [85, 100, 115], "2": [95, 115, 130],
    "1": [110, 130, 145], "1/0": [125, 150, 170], "2/0": [145, 175, 195], "3/0": [165, 200, 225],
    "4/0": [195, 230, 260], "250": [215, 255, 290], "300": [240, 285, 320], "350": [260, 310, 350],
    "400": [280, 335, 380], "500": [320, 380, 430], "600": [350, 420, 475], "750": [400, 475, 535], "1000": [455, 545, 615]
}

ampacidad_aire = {
    "14": [20, 25, 35], "12": [25, 30, 40], "10": [30, 40, 55], "8": [60, 70, 80],
    "6": [80, 95, 105], "4": [105, 125, 140], "3": [120, 145, 165], "2": [140, 170, 190],
    "1": [165, 195, 220], "1/0": [195, 230, 260], "2/0": [225, 265, 300], "3/0": [260, 310, 350],
    "4/0": [300, 360, 405], "250": [340, 405, 455], "300": [375, 445, 505], "350": [420, 505, 570],
    "400": [455, 545, 615], "500": [515, 620, 700], "600": [575, 690, 780], "750": [655, 785, 885], "1000": [780, 935, 1055]
}

# Resistencia (R) y Reactancia (X) en Ohms por kilómetro (Cobre en tubo no magnético)
resist_cobre = {
    "14": 10.2, "12": 6.3, "10": 3.94, "8": 2.55, "6": 1.61, "4": 1.01,
    "3": 0.801, "2": 0.633, "1": 0.505, "1/0": 0.400, "2/0": 0.318,
    "3/0": 0.253, "4/0": 0.200, "250": 0.171, "300": 0.144, "350": 0.125,
    "400": 0.108, "500": 0.089, "600": 0.075, "750": 0.062, "1000": 0.049
}

react_cobre = {
    "14": 0.190, "12": 0.177, "10": 0.164, "8": 0.171, "6": 0.167, "4": 0.157,
    "3": 0.154, "2": 0.148, "1": 0.151, "1/0": 0.144, "2/0": 0.141,
    "3/0": 0.138, "4/0": 0.135, "250": 0.135, "300": 0.135, "350": 0.131,
    "400": 0.131, "500": 0.128, "600": 0.128, "750": 0.125, "1000": 0.121
}

factores_temp_ambiente = {
    "21-25°C": [1.08, 1.05, 1.04], "26-30°C": [1.00, 1.00, 1.00],
    "31-35°C": [0.91, 0.94, 0.96], "36-40°C": [0.82, 0.88, 0.91],
    "41-45°C": [0.71, 0.82, 0.87], "46-50°C": [0.58, 0.75, 0.82],
    "51-55°C": [0.41, 0.67, 0.76], "56-60°C": [0.00, 0.58, 0.71]
}

interruptores_std = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000]

tierra_por_interruptor = {
    15: "14", 20: "12", 60: "10", 100: "8", 200: "6", 300: "4", 400: "3", 
    500: "2", 600: "1", 800: "1/0", 1000: "2/0", 1200: "3/0", 1600: "4/0", 2000: "250",
    2500: "350", 3000: "400", 4000: "500", 5000: "700", 6000: "800"
}

# --- 2. FUNCIONES LÓGICAS ---
def formato_calibre(calibre_str):
    try:
        return f"{calibre_str} kcmil" if int(calibre_str) >= 250 else f"{calibre_str} AWG"
    except ValueError:
        return f"{calibre_str} AWG"

def obtener_calibre_optimo(amp_req_per_cable, corriente_total, cables_fase, tabla, col_temp, L_metros, pf, sistema, V_max_drop_volts):
    """Evalúa que el cable cumpla TANTO con Ampacidad como con Caída de Tensión."""
    for cal in calibres:
        # 1. Prueba de Ampacidad
        amp_tabla = tabla.get(cal, [0,0,0])[col_temp]
        if amp_tabla < amp_req_per_cable:
            continue # Si no soporta la corriente, pasa al siguiente calibre mayor
            
        # 2. Prueba de Caída de Tensión
        R = resist_cobre.get(cal, 0)
        X = react_cobre.get(cal, 0)
        
        if sistema == "Corriente Directa (DC)":
            Z_eff = R # En DC no hay reactancia
            factor_fases = 2 # Ida y vuelta
        else:
            # AC: Impedancia efectiva = R*cos(θ) + X*sin(θ)
            sin_phi = math.sin(math.acos(pf))
            Z_eff = (R * pf) + (X * sin_phi)
            factor_fases = math.sqrt(3) if "Trifásico" in sistema else 2

        # Caída de Tensión (Fórmula exacta en Volts)
        # Z_eff está en Ohms/km, así que dividimos la distancia (L) entre 1000
        # Al tener cables paralelos, la impedancia se divide entre la cantidad de cables
        delta_v = factor_fases * (Z_eff / cables_fase) * corriente_total * (L_metros / 1000.0)
        
        if delta_v <= V_max_drop_volts:
            return cal, delta_v # ¡Cumple ambas reglas!
            
    return None, None # Ningún cable cumplió

def seleccionar_interruptor_normativo(corriente_carga_diseno, ampacidad_conductor_corregida):
    it_seleccionado = interruptores_std[-1]
    for it in interruptores_std:
        if it >= corriente_carga_diseno:
            it_seleccionado = it
            break
            
    if it_seleccionado > ampacidad_conductor_corregida:
        idx = interruptores_std.index(it_seleccionado)
        it_inferior = interruptores_std[idx-1] if idx > 0 else it_seleccionado
        if it_inferior > ampacidad_conductor_corregida and ampacidad_conductor_corregida < 800:
             pass 

    return it_seleccionado

def obtener_tierra(interruptor):
    for limite in sorted(tierra_por_interruptor.keys()):
        if interruptor <= limite:
            return tierra_por_interruptor[limite]
    return "800"

def obtener_factor_agrupamiento(n):
    if n <= 3: return 1.00
    elif n <= 6: return 0.80
    elif n <= 9: return 0.70
    elif n <= 20: return 0.50
    elif n <= 30: return 0.45
    elif n <= 40: return 0.40
    else: return 0.35

# --- 3. INTERFAZ GRÁFICA ---
st.set_page_config(page_title="Calculadora Eléctrica Avanzada", layout="wide")
st.title("⚡ Dimensionamiento Integral: NOM-001-SEDE")

with st.sidebar:
    st.header("1. Sistema Eléctrico")
    tipo_corriente = st.radio("Tipo de Corriente", ["Corriente Alterna (AC)", "Corriente Directa (DC)"])
    
    if tipo_corriente == "Corriente Alterna (AC)":
        tipo_sistema = st.selectbox("Fases del Sistema", ["Monofásico (1F)", "Bifásico (2F)", "Trifásico (3F)"], index=2)
        fp = st.number_input("Factor de Potencia (FP)", min_value=0.1, max_value=1.0, value=1.0, step=0.1)
        fases_activas_base = 3 if "Trifásico" in tipo_sistema else 2
    else:
        tipo_sistema = "Corriente Directa (DC)"
        fp = 1.0
        fases_activas_base = 2

    voltaje = st.number_input("Voltaje del Sistema (V)", min_value=12, value=220, step=10)

    st.header("2. Datos de la Carga")
    metodo_entrada = st.selectbox("Ingreso de la Carga en:", ["Potencia Aparente (kVA)", "Corriente Nominal (A)"])
    
    if metodo_entrada == "Potencia Aparente (kVA)":
        potencia_kva = st.number_input("Potencia (kVA)", min_value=0.1, value=100.0)
        if "Trifásico" in tipo_sistema:
            corriente = (potencia_kva * 1000) / (math.sqrt(3) * voltaje)
        else:
            corriente = (potencia_kva * 1000) / voltaje
        st.info(f"💡 Corriente Calculada: **{corriente:.2f} A**")
    else:
        corriente = st.number_input("Corriente (A)", min_value=1.0, value=100.0)

    factor_utilizacion = st.selectbox("Factor de Utilización", [1.0, 0.8], index=1, help="Usa 0.8 para cargas continuas (>3h)")
    
    st.header("3. Caída de Tensión")
    distancia = st.number_input("Longitud del Circuito (Metros)", min_value=1.0, value=10.0, step=1.0)
    caida_permitida_pct = st.number_input("Caída Máxima Permisible (%)", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
    
    st.header("4. Instalación")
    tipo_inst = st.selectbox("Canalización", ["Ducto/Sobre mas cable", "Al Aire Libre"])
    temp_aislante = st.selectbox("Aislamiento", ["60°C", "75°C", "90°C"], index=3)
    temp_ambiente_str = st.selectbox("Temp. Ambiente", list(factores_temp_ambiente.keys()), index=1)
    misma_canalizacion = st.checkbox("Agrupar cables paralelos", value=True)
    
    st.header("5. Límites")
    calibre_maximo = st.selectbox("Calibre Máximo", calibres, index=calibres.index("500"))

if st.button("🚀 Calcular Sistema Integral", type="primary", use_container_width=True):
    indice_temp = [60, 75, 90].index(int(temp_aislante[:2]))
    tabla_usar = ampacidad_aire if "Aire" in tipo_inst else ampacidad_tubo
    factor_temp = factores_temp_ambiente[temp_ambiente_str][indice_temp]
    
    if factor_temp == 0:
        st.error(f"Aislamiento insuficiente para {temp_ambiente_str}.")
        st.stop()
        
    corriente_diseno = corriente / factor_utilizacion
    volts_caida_maxima = voltaje * (caida_permitida_pct / 100.0)
    
    cables_fase = 1
    resuelto = False
    
    while cables_fase <= 20:
        total_conductores = (fases_activas_base * cables_fase) if misma_canalizacion else fases_activas_base
        f_agrup = obtener_factor_agrupamiento(total_conductores)
        
        amp_necesaria_por_cable = corriente_diseno / (cables_fase * factor_temp * f_agrup)
        
        # Nueva función de búsqueda que verifica Ampacidad Y Caída de Tensión
        cal_cand, dv_cand = obtener_calibre_optimo(
            amp_req_per_cable=amp_necesaria_por_cable, 
            corriente_total=corriente, # Caída de tensión se calcula con la corriente real conectada
            cables_fase=cables_fase, 
            tabla=tabla_usar, 
            col_temp=indice_temp, 
            L_metros=distancia, 
            pf=fp, 
            sistema=tipo_sistema, 
            V_max_drop_volts=volts_caida_maxima
        )
        
        if cal_cand:
            idx_cand = calibres.index(cal_cand)
            if (cables_fase == 1 or idx_cand >= index_min_paralelo) and idx_cand <= calibres.index(calibre_maximo):
                calibre_final = cal_cand
                f_agrup_final = f_agrup
                caida_tension_final = dv_cand
                resuelto = True
                break
        cables_fase += 1

    if resuelto:
        amp_tabla = tabla_usar[calibre_final][indice_temp]
        amp_corregida_total = amp_tabla * cables_fase * factor_temp * f_agrup_final
        
        interruptor = seleccionar_interruptor_normativo(corriente_diseno, amp_corregida_total)
        tierra = obtener_tierra(interruptor)
        pct_caida_real = (caida_tension_final / voltaje) * 100
        
        st.success(f"### Resultado: {cables_fase}x {formato_calibre(calibre_final)} por fase")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interruptor ITM", f"{interruptor} A")
        c2.metric("Cable de Tierra", formato_calibre(tierra))
        c3.metric("Ampacidad Instalada", f"{amp_corregida_total:.1f} A")
        c4.metric("Caída de Tensión Real", f"{pct_caida_real:.2f}%", f"-{caida_tension_final:.1f} Volts", delta_color="inverse")
        
        with st.expander("Ver Reporte de Ingeniería"):
            st.write(f"**Criterio de Ampacidad:**")
            st.write(f"- Corriente de diseño (con F.U.): {corriente_diseno:.2f} A")
            st.write(f"- Factores de derateo: Temp={factor_temp}, Agrupamiento={f_agrup_final} ({total_conductores} hilos)")
            st.write(f"- Ampacidad base del cable ({formato_calibre(calibre_final)}): {amp_tabla} A")
            
            st.write(f"**Criterio de Caída de Tensión:**")
            st.write(f"- Distancia evaluada: {distancia} metros")
            if tipo_corriente != "Corriente Directa (DC)":
                st.write(f"- Factor de Potencia: {fp}")
            st.write(f"- Límite máximo establecido: {caida_permitida_pct}% ({volts_caida_maxima:.2f} V)")
            st.write(f"- Caída calculada exacta: {pct_caida_real:.2f}% ({caida_tension_final:.2f} V)")
            
            # Nota inteligente
            if amp_necesaria_por_cable <= tabla_usar["14"][indice_temp] and calibres.index(calibre_final) > calibres.index("10"):
                st.info("💡 **Nota:** El calibre seleccionado es grande principalmente para superar la caída de tensión por la larga distancia, no por exceso de ampacidad.")
    else:
        st.error("No se encontró solución. La distancia es muy larga o la corriente muy alta para el calibre máximo permitido.")
