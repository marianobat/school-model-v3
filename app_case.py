
import streamlit as st
import pandas as pd
import numpy as np
from simulate_case import Params, simulate

st.set_page_config(page_title="Simulador Escolar – Calidad Dinámica", layout="wide")

st.title("Simulador de Sistema Escolar • Calidad, Demanda y Capacidad")

with st.sidebar:
    st.header("Parámetros")
    with st.expander("⏳ Horizonte y Estado inicial", expanded=True):
        anios = st.number_input("Años a simular", 3, 30, 10, 1)
        alumnos_inicial_por_grado = st.slider("Alumnos iniciales por grado", 0, 50, 20, 1)
        demanda_inicial = st.slider("Demanda inicial (pool familias)", 0, 2000, 300, 25)
        divisiones_iniciales = st.slider("Divisiones iniciales por grado", 1, 5, 1, 1)

    with st.expander("🏫 Capacidad e Infraestructura", expanded=False):
        cupo_optimo = st.slider("Cupo óptimo por aula", 15, 35, 25, 1)
        cupo_maximo = st.slider("Cupo MÁXIMO por aula", 20, 40, 30, 1)
        capex_aula = st.number_input("CAPEX por aula nueva", 10000.0, 500000.0, 100000.0, 1000.0)
        costo_docente_por_aula = st.number_input("Costo docente anual por aula", 10000.0, 200000.0, 60000.0, 1000.0)
        sueldos_no_docentes = st.number_input("Sueldos NO docentes (anual)", 0.0, 500000.0, 120000.0, 1000.0)
        mantenimiento_prop = st.slider("Mantenimiento (% facturación)", 0.0, 0.2, 0.03, 0.01)
        trigger_auto_aula = st.checkbox("Construcción endógena de aulas", True)
        regla_dos_div = st.checkbox("Disparar si admitidos deseados ≥ 2*cupo_max", True)

    with st.expander("📣 Demanda y Marketing", expanded=False):
        prop_mkt = st.slider("Proporción de marketing sobre facturación", 0.0, 0.2, 0.05, 0.01)
        mkt_floor = st.number_input("MKT mínimo anual", 0.0, 100000.0, 2000.0, 100.0)
        cac_base = st.number_input("CAC base", 10.0, 2000.0, 200.0, 10.0)
        k_saturacion = st.slider("Sensibilidad CAC a saturación", 0.0, 2.0, 0.5, 0.1)
        k_calidad_candidatos = st.slider("Efecto de calidad en orgánico", 0.0, 2.0, 0.8, 0.1)

    with st.expander("💵 Precio y Retención", expanded=False):
        cuota_mensual = st.number_input("Cuota mensual", 0.0, 1000.0, 50.0, 1.0)
        meses_cobro = st.slider("Meses de cobro/año", 1, 12, 10, 1)
        ref_precio = st.number_input("Precio de referencia", 1.0, 2000.0, 50.0, 1.0)
        k_bajas_precio = st.slider("Sensibilidad bajas al precio", 0.0, 0.5, 0.08, 0.01)
        k_precio_cac = st.slider("Sensibilidad CAC al precio", 0.0, 1.0, 0.5, 0.05)
        tasa_bajas_base = st.slider("Tasa de bajas base", 0.0, 0.2, 0.04, 0.01)
        k_bajas_calidad = st.slider("Sensibilidad bajas a baja calidad", 0.0, 0.5, 0.12, 0.01)

    with st.expander("🌟 Calidad y Reputación (blandos)", expanded=False):
        calidad_base = st.slider("Calidad base", 0.0, 1.0, 0.7, 0.01)
        k_hacinamiento = st.slider("Castigo por hacinamiento", 0.0, 2.0, 1.0, 0.05)
        gamma_hacinamiento = st.slider("No linealidad de hacinamiento", 1.0, 2.0, 1.3, 0.05)
        k_inv_alumno = st.slider("Rendimiento de inversión por alumno", 0.0, 1.0, 0.3, 0.05)
        ref_inv_alumno = st.number_input("Ref. inversión por alumno (anual)", 1.0, 5000.0, 200.0, 10.0)
        k_inv_infra = st.slider("Rendimiento de inversión en infraestructura", 0.0, 1.0, 0.2, 0.05)
        ref_inv_infra = st.number_input("Ref. inversión en infraestructura (anual)", 1000.0, 200000.0, 50000.0, 1000.0)
        k_selectividad = st.slider("Efecto de selectividad", 0.0, 1.0, 0.2, 0.05)
        alpha_calidad = st.slider("Suavizado de calidad (inercia)", 0.0, 1.0, 0.4, 0.05)
        nivel_articulacion = st.slider("Nivel de articulación", 0.0, 1.0, 0.2, 0.05)
        nivel_comunicacion = st.slider("Nivel de comunicación", 0.0, 1.0, 0.2, 0.05)
        nivel_diferenciacion = st.slider("Nivel de diferenciación", 0.0, 1.0, 0.2, 0.05)
        k_articulacion = st.slider("Peso articulación", 0.0, 0.5, 0.05, 0.01)
        k_comunicacion = st.slider("Peso comunicación", 0.0, 0.5, 0.05, 0.01)
        k_diferenciacion = st.slider("Peso diferenciación", 0.0, 0.5, 0.05, 0.01)

    with st.expander("📝 Admisiones", expanded=False):
        politica_seleccion = st.slider("Política de selección (admitidos/candidatos)", 0.0, 1.0, 0.7, 0.05)
        admitidos_max_abs = st.number_input("Tope absoluto de admitidos (-1 desactiva)", -1, 2000, -1, 1)

p = Params(
    anios=anios, alumnos_inicial_por_grado=alumnos_inicial_por_grado,
    demanda_inicial=demanda_inicial, divisiones_iniciales=divisiones_iniciales,
    cupo_optimo=cupo_optimo, cupo_maximo=cupo_maximo, capex_aula=capex_aula,
    costo_docente_por_aula=costo_docente_por_aula, sueldos_no_docentes=sueldos_no_docentes,
    mantenimiento_prop=mantenimiento_prop, trigger_auto_aula=trigger_auto_aula, regla_dos_div=regla_dos_div,
    prop_mkt=prop_mkt, mkt_floor=mkt_floor, cac_base=cac_base, k_saturacion=k_saturacion,
    k_calidad_candidatos=k_calidad_candidatos,
    cuota_mensual=cuota_mensual, meses_cobro=meses_cobro, ref_precio=ref_precio,
    k_bajas_precio=k_bajas_precio, k_precio_cac=k_precio_cac, tasa_bajas_base=tasa_bajas_base, k_bajas_calidad=k_bajas_calidad,
    calidad_base=calidad_base, k_hacinamiento=k_hacinamiento, gamma_hacinamiento=gamma_hacinamiento,
    k_inv_alumno=k_inv_alumno, ref_inv_alumno=ref_inv_alumno, k_inv_infra=k_inv_infra, ref_inv_infra=ref_inv_infra,
    k_selectividad=k_selectividad, alpha_calidad=alpha_calidad,
    nivel_articulacion=nivel_articulacion, nivel_comunicacion=nivel_comunicacion, nivel_diferenciacion=nivel_diferenciacion,
    k_articulacion=k_articulacion, k_comunicacion=k_comunicacion, k_diferenciacion=k_diferenciacion,
    politica_seleccion=politica_seleccion, admitidos_max_abs=admitidos_max_abs,
)

df, extras = simulate(p)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Alumnos actuales", f"{int(df['alumnos_totales'].iloc[-1])}")
col2.metric("Calidad (último año)", f"{df['calidad'].iloc[-1]:.2f}")
col3.metric("Aulas totales", f"{int(df['AulasTotales'].iloc[-1])}")
cap_bind = "Sí" if df['capacidad_binding'].iloc[-1] == 1 else "No"
col4.metric("¿Limita la Capacidad?", cap_bind)

st.subheader("Evolución de alumnos")
st.line_chart(df.set_index("anio")[["alumnos_totales"]])

st.subheader("Calidad vs Tasa de bajas")
st.line_chart(df.set_index("anio")[["calidad","tasa_bajas"]])

st.subheader("Candidatos: pagados vs orgánicos")
st.line_chart(df.set_index("anio")[["candidatos_pago","candidatos_organico"]])

with st.expander("📊 Ver tabla completa"):
    st.dataframe(df)

st.caption("Consejo: si 'Admitidos < Admitidos deseados' y la capacidad está limitando, activa 'Construcción endógena' o sube el cupo/DivG1 para ver el efecto.")
