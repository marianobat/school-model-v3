
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

# Orden oficial de grados (incluye K3-K5, ver §2)
GRADE_NAMES = ["K3", "K4", "K5"] + [f"G{g}" for g in range(1, 13)]
GRADE_INDEX = {name: i for i, name in enumerate(GRADE_NAMES)}
N_GRADES = len(GRADE_NAMES)  # 15

@dataclass
class Params:
    # --- Horizonte y estado inicial ---
    anios: int = 10
    alumnos_inicial_por_grado: int = 25
    demanda_inicial: int = 1500
    divisiones_iniciales: int = 2

    # --- Capacidad y aulas ---
    cupo_optimo: int = 25
    cupo_maximo: int = 30
    capex_aula: float = 100000.0
    costo_docente_por_aula: float = 60000.0
    sueldos_no_docentes: float = 120000.0
    mantenimiento_prop: float = 0.03
    trigger_auto_aula: bool = True
    regla_dos_div: bool = True

    # --- Crecimiento manual de aulas ---
    manual_crecimiento: bool = False
    solo_manual: bool = False
    extra_div_k3_per_year: int = 0
    extra_div_k4_per_year: int = 0
    extra_div_k5_per_year: int = 0
    extra_div_g1_per_year: int = 0
    
    # --- Demanda y Marketing ---
    prop_mkt: float = 0.05
    mkt_floor: float = 2000.0
    cac_base: float = 200.0
    k_saturacion: float = 0.5
    k_calidad_candidatos: float = 0.8        
    # Dinámica de Demanda (nuevos controles)
    beta_demanda_calidad: float = 10.0        # Δdemanda por punto de calidad
    delta_demanda_saturacion: float = 0.05    # caída por alumno actual
    piso_demanda_gap: int = 20                # Demanda >= alumnos + piso

    # --- Precio y Retención ---
    cuota_mensual: float = 300.0
    meses_cobro: int = 10
    ref_precio: float = 50.0
    k_bajas_precio: float = 0.08
    k_precio_cac: float = 0.5
    tasa_bajas_base: float = 0.04
    k_bajas_calidad: float = 0.12

    # --- Admisiones ---
    politica_seleccion: float = 0.7
    admitidos_max_abs: int = -1

    # --- Calidad y reputación ---
    calidad_base: float = 0.7
    k_hacinamiento: float = 1.0
    gamma_hacinamiento: float = 1.3
    k_inv_alumno: float = 0.3
    ref_inv_alumno: float = 200.0
    k_inv_infra: float = 0.2
    ref_inv_infra: float = 50000.0
    k_selectividad: float = 0.2
    alpha_calidad: float = 0.4

    # Factores blandos (0..1) y sus pesos
    nivel_articulacion: float = 0.20
    nivel_comunicacion: float = 0.20
    nivel_diferenciacion: float = 0.20
    k_articulacion: float = 0.05
    k_comunicacion: float = 0.05
    k_diferenciacion: float = 0.05

    # --- Grados y admisiones por grados de entrada ---
    # Proporciones de candidatos a grados de entrada (deben sumar 1.0)
    prop_cand_k3: float = 0.25
    prop_cand_k4: float = 0.25
    prop_cand_k5: float = 0.25
    prop_cand_g1: float = 0.25

    # Continuidad de Kinder a 1° (aplica al paso K5 -> G1)
    tasa_cont_k_to_g1: float = 0.95

    # (Opcional) Cobranza/morosidad: si tu app lo pasa, DEBE estar acá
    tasa_cobro: float = 1.0                # 1.0 = 100%

def simulate(par: Params) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    G = np.zeros((par.anios, N_GRADES))
    Div = np.zeros((par.anios, N_GRADES), dtype=int)
    calidad = np.zeros(par.anios)
    Demanda = np.zeros(par.anios)
    Marketing = np.zeros(par.anios)
    CAC = np.zeros(par.anios)
    admitidos = np.zeros(par.anios)
    admitidos_deseados = np.zeros(par.anios)
    nuevos_candidatos = np.zeros(par.anios)
    candidatos_pago = np.zeros(par.anios)
    candidatos_organico = np.zeros(par.anios)
    tasa_bajas = np.zeros(par.anios)
    inv_infra = np.zeros(par.anios)
    inv_calidad_alumno = np.zeros(par.anios)
    hac_prom_hist = np.zeros(par.anios)
    selectividad_hist = np.zeros(par.anios)
    capacidad_binding = np.zeros(par.anios, dtype=bool)
    demanda_binding = np.zeros(par.anios, dtype=bool)

    G[0, :] = par.alumnos_inicial_por_grado
    Div[0, :] = par.divisiones_iniciales
    calidad[0] = par.calidad_base
    Demanda[0] = max(par.demanda_inicial, G[0, :].sum() + 50)
    fact_prev = G[0, :].sum() * par.cuota_mensual * par.meses_cobro
    Marketing[0] = max(par.mkt_floor, par.prop_mkt * fact_prev)

    for k in range(par.anios):
        # --- Crecimiento manual de aulas ---
        if par.manual_crecimiento:
            add_map = {
                GRADE_INDEX["K3"]: par.extra_div_k3_per_year,
                GRADE_INDEX["K4"]: par.extra_div_k4_per_year,
                GRADE_INDEX["K5"]: par.extra_div_k5_per_year,
                GRADE_INDEX["G1"]: par.extra_div_g1_per_year,
            }
            nuevas = 0
            for idx, add in add_map.items():
                if add > 0:
                    Div[k, idx] += int(add)
                    nuevas += int(add)
            if nuevas > 0:
                inv_infra[k] += par.capex_aula * nuevas  # CAPEX por cada aula nueva
        
        # Si es "solo_manual", apagamos el trigger automático
        auto_trigger = (not par.solo_manual) and par.trigger_auto_aula
        alumnos_k = float(G[k, :].sum())
        if k > 0:
            Demanda[k] = max(
                Demanda[k-1]
                + par.beta_demanda_calidad * (calidad[k-1] if k > 0 else par.calidad_base)
                - par.delta_demanda_saturacion * alumnos_k,
                alumnos_k + par.piso_demanda_gap
            )

        saturacion = 0.0 if Demanda[k] <= 0 else (alumnos_k / max(Demanda[k], 1e-9))
        CAC[k] = par.cac_base * (1.0 + par.k_saturacion * saturacion)
        precio_rel = par.cuota_mensual / max(par.ref_precio, 1e-9)
        CAC[k] *= (1.0 + par.k_precio_cac * max(precio_rel - 1.0, 0.0))

        if k > 0:
            fact_prev = G[k-1, :].sum() * par.cuota_mensual * par.meses_cobro
            Marketing[k] = max(par.mkt_floor, par.prop_mkt * fact_prev)

        candidatos_pago[k] = Marketing[k] / max(CAC[k], 1e-9)
        candidatos_organico[k] = par.k_calidad_candidatos * (calidad[k-1] if k > 0 else calidad[0])
        nuevos_candidatos[k] = max(0.0, candidatos_pago[k] + candidatos_organico[k])

        # --- Reparto de candidatos a grados de entrada ---
        # Normalizamos por seguridad para que sumen 1.0
        w_k3 = max(par.prop_cand_k3, 0.0)
        w_k4 = max(par.prop_cand_k4, 0.0)
        w_k5 = max(par.prop_cand_k5, 0.0)
        w_g1 = max(par.prop_cand_g1, 0.0)
        wsum = w_k3 + w_k4 + w_k5 + w_g1
        if wsum <= 0:
            w_k3 = w_k4 = w_k5 = w_g1 = 0.25
            wsum = 1.0
        w_k3, w_k4, w_k5, w_g1 = [w/wsum for w in (w_k3, w_k4, w_k5, w_g1)]
        
        cand_k3 = nuevos_candidatos[k] * w_k3
        cand_k4 = nuevos_candidatos[k] * w_k4
        cand_k5 = nuevos_candidatos[k] * w_k5
        cand_g1 = nuevos_candidatos[k] * w_g1

        # Índices de grados de entrada
        iK3 = GRADE_INDEX["K3"]; iK4 = GRADE_INDEX["K4"]; iK5 = GRADE_INDEX["K5"]; iG1 = GRADE_INDEX["G1"]
        
        cap_k3 = Div[k, iK3] * par.cupo_maximo
        cap_k4 = Div[k, iK4] * par.cupo_maximo
        cap_k5 = Div[k, iK5] * par.cupo_maximo
        cap_g1 = Div[k, iG1] * par.cupo_maximo
        
        # Política de selección por grado
        adm_des_k3 = min(par.politica_seleccion * cand_k3, cap_k3)
        adm_des_k4 = min(par.politica_seleccion * cand_k4, cap_k4)
        adm_des_k5 = min(par.politica_seleccion * cand_k5, cap_k5)
        adm_des_g1 = min(par.politica_seleccion * cand_g1, cap_g1)
        
        # Gap de demanda total puede acotar el total de admitidos (en bloque)
        gap_demanda = max(Demanda[k] - float(G[k, :].sum()), 0.0)
        adm_total_deseado = adm_des_k3 + adm_des_k4 + adm_des_k5 + adm_des_g1
        escala = 1.0 if adm_total_deseado <= 0 else min(1.0, gap_demanda / adm_total_deseado)
        
        adm_k3 = adm_des_k3 * escala
        adm_k4 = adm_des_k4 * escala
        adm_k5 = adm_des_k5 * escala
        adm_g1 = adm_des_g1 * escala
        
        # Guarda "admitidos" de la fila para reportes agregados (suma de todos)
        admitidos[k] = adm_k3 + adm_k4 + adm_k5 + adm_g1
        admitidos_deseados[k] = adm_total_deseado

        capacidad_g1 = int(Div[k, 0] * par.cupo_maximo)
        gap_demanda = max(Demanda[k] - alumnos_k, 0.0)
        cap_politica = par.politica_seleccion * nuevos_candidatos[k]
        if par.admitidos_max_abs >= 0:
            cap_politica = min(cap_politica, float(par.admitidos_max_abs))
        admitidos_deseados[k] = min(cap_politica, gap_demanda)
        admitidos[k] = min(admitidos_deseados[k], float(capacidad_g1))

        build = False
        if par.trigger_auto_aula:
            exceso_g1 = max(admitidos_deseados[k] - float(capacidad_g1), 0.0)
            if (par.regla_dos_div and admitidos_deseados[k] >= 2 * par.cupo_maximo) or (exceso_g1 > 0):
                build = True
        if build:
            inv_infra[k] += par.capex_aula
            if k < par.anios - 1:
                Div[k, 0] += 1

        div_valid = np.maximum(Div[k, :], 1e-9)
        ratio = G[k, :] / (div_valid * par.cupo_optimo)
        exceso = np.clip(ratio - 1.0, 0.0, None)
        hac_prom = 0.0 if alumnos_k <= 0 else float(np.mean(exceso))
        if par.gamma_hacinamiento != 1.0 and hac_prom > 0:
            hac_prom = hac_prom ** par.gamma_hacinamiento
        hac_prom_hist[k] = hac_prom

        inv_calidad_alumno[k] = 0.5 * Marketing[k]
        inv_alum_norm = 0.0
        if alumnos_k > 0:
            inv_alum_norm = (inv_calidad_alumno[k] / max(alumnos_k, 1e-9)) / max(par.ref_inv_alumno, 1e-9)
        inv_infra_norm = (inv_infra[k] / max(par.ref_inv_infra, 1e-9))

        selectividad = 0.0 if nuevos_candidatos[k] <= 0 else (admitidos[k] / max(nuevos_candidatos[k], 1e-9))
        selectividad = float(np.clip(selectividad, 0.0, 1.0))
        selectividad_hist[k] = selectividad

        articulacion = np.clip(par.nivel_articulacion, 0.0, 1.0)
        comunicacion = np.clip(par.nivel_comunicacion, 0.0, 1.0)
        diferenciacion = np.clip(par.nivel_diferenciacion, 0.0, 1.0)

        calidad_inst = (
            par.calidad_base
            - par.k_hacinamiento * hac_prom
            + par.k_inv_alumno * inv_alum_norm
            + par.k_inv_infra * inv_infra_norm
            - par.k_selectividad * (1.0 - selectividad)
            + par.k_articulacion * articulacion
            + par.k_comunicacion * comunicacion
            + par.k_diferenciacion * diferenciacion
        )
        prev_c = calidad[k-1] if k > 0 else par.calidad_base
        calidad[k] = float(np.clip(prev_c + par.alpha_calidad * (calidad_inst - prev_c), 0.0, 1.0))

        tasa = (
            par.tasa_bajas_base
            + (1.0 - calidad[k]) * par.k_bajas_calidad
            + max(precio_rel - 1.0, 0.0) * par.k_bajas_precio
        )
        tasa = float(np.clip(tasa, 0.0, 0.5))
        tasa_bajas[k] = tasa
        bajas_tot = tasa * alumnos_k

        next_row = np.zeros(N_GRADES)
        
        # Ingresos por admisión externa a grados de entrada
        next_row[iK3] += adm_k3
        next_row[iK4] += adm_k4
        next_row[iK5] += adm_k5
        next_row[iG1] += adm_g1
        
        # Bajas totales del año (ya calculaste 'tasa' y 'bajas_tot' antes)
        alumnos_k = float(G[k, :].sum())
        def bajas_por(grado_idx):
            return 0.0 if alumnos_k <= 0 else (G[k, grado_idx] / alumnos_k) * bajas_tot
        
        # Kinder: K3 -> K4 ; K4 -> K5 ; K5 -> G1 (con continuidad)
        iG2 = GRADE_INDEX["G2"]
        iG12 = GRADE_INDEX["G12"]
        
        # K3 -> K4
        k3_net = max(G[k, iK3] - bajas_por(iK3), 0.0)
        next_row[iK4] += k3_net
        
        # K4 -> K5
        k4_net = max(G[k, iK4] - bajas_por(iK4), 0.0)
        next_row[iK5] += k4_net
        
        # K5 -> G1 con continuidad
        k5_net = max(G[k, iK5] - bajas_por(iK5), 0.0)
        next_row[iG1] += par.tasa_cont_k_to_g1 * k5_net
        
        # Primaria/Secundaria: G1 -> G2 -> ... -> G12
        for g in range(1, 13):
            name_src = f"G{g}"
            idx_src = GRADE_INDEX[name_src]
            if g < 12:
                idx_dst = GRADE_INDEX[f"G{g+1}"]
                net = max(G[k, idx_src] - bajas_por(idx_src), 0.0)
                next_row[idx_dst] += net
            # G12 egresa (no se suma)

        if k < par.anios - 1:
            G[k+1, :] = next_row
            Div[k+1, :] = Div[k, :]

        capacidad_binding[k] = admitidos[k] < admitidos_deseados[k]
        demanda_binding[k] = (G[k, :].sum() >= Demanda[k] - 1e-6)

    alumnos_tot = np.array([G[i, :].sum() for i in range(par.anios)])
    facturacion = alumnos_tot * par.cuota_mensual * par.meses_cobro
    sueldos_docentes = np.sum(Div, axis=1) * par.costo_docente_por_aula
    costos = sueldos_docentes + par.sueldos_no_docentes + par.mantenimiento_prop * facturacion + Marketing
    resultado = facturacion - costos - inv_infra

    df = pd.DataFrame({
        "anio": np.arange(par.anios),
        "alumnos_totales": alumnos_tot,
        "calidad": calidad,
        "tasa_bajas": tasa_bajas,
        "nuevos_candidatos": nuevos_candidatos,
        "candidatos_pago": candidatos_pago,
        "candidatos_organico": candidatos_organico,
        "admitidos_deseados": admitidos_deseados,
        "admitidos": admitidos,
        "Demanda": Demanda,
        "Marketing": Marketing,
        "CAC": CAC,
        "DivG1": Div[:, 0],
        "AulasTotales": Div.sum(axis=1),
        "hacinamiento_prom": hac_prom_hist,
        "selectividad": selectividad_hist,
        "capacidad_binding": capacidad_binding.astype(int),
        "demanda_binding": demanda_binding.astype(int),
        "facturacion": facturacion,
        "sueldos_docentes": sueldos_docentes,
        "costos_totales": costos,
        "resultado": resultado,
    })
        # --- Redondeo de variables de conteo ---
    cols_round = [
        "alumnos_totales", "nuevos_candidatos", "candidatos_pago",
        "candidatos_organico", "admitidos_deseados", "admitidos",
        "Demanda", "DivG1", "AulasTotales"
    ]
    for c in cols_round:
        if c in df.columns:
            df[c] = df[c].round().astype(int)

    # También redondeamos la matriz G (alumnos por grado)
    G = np.round(G).astype(int)
    extras = {"G": G, "Div": Div, "params": asdict(par)}
    return df, extras
