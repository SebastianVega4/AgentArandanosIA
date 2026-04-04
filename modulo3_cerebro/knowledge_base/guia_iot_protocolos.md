# Guía de Monitoreo IoT y Protocolos de Emergencia
## Sistema BerryMind — Cultivo Inteligente de Arándanos
### Valle de Sotaquirá, Boyacá, Colombia

---

## 1. SISTEMA DE SENSORES IoT

### 1.1 Red de Sensores Instalados
El sistema BerryMind emplea una red de sensores distribuidos en el lote de arándanos, conectados a un nodo central Raspberry Pi/Arduino con transmisión WiFi/LoRaWAN.

**Sensores activos por nodo**:
| Sensor | Modelo Referencia | Ubicación | Frecuencia |
|---|---|---|---|
| Temperatura ambiente | DHT22 / DS18B20 | 1,5 m de altura | Cada 5 min |
| Humedad relativa | DHT22 | 1,5 m de altura | Cada 5 min |
| pH del suelo | soil pH meter | 20 cm profundidad | Cada hora |
| Conductividad eléctrica | EC-5 / 5TM | 20 cm profundidad | Cada 5 min |
| Humedad del suelo | VH400 / 5TM | 20 cm profundidad | Cada 5 min |
| Luminosidad (PAR) | BH1750 | Sin sombra | Cada 5 min |

### 1.2 Rangos Óptimos de Operación
| Variable | Rango Óptimo | Rango de Alerta | Rango Crítico |
|---|---|---|---|
| Temperatura | 10–25°C | <4°C o >32°C | <0°C o >38°C |
| Humedad relativa | 60–80% | <45% o >90% | <30% o >95% |
| pH suelo | 4,5–5,5 | <4,0 o >6,0 | <3,5 o >6,5 |
| CE suelo | 0,5–2,0 mS/cm | <0,2 o >3,0 | <0,1 o >4,0 |
| Humedad suelo | 60–80% | <40% o >90% | <25% |
| Luminosidad | 15.000–50.000 lux | <5.000 lux | <1.000 lux |

---

## 2. PROTOCOLOS DE ALERTA Y RESPUESTA

### 2.1 Protocolo HELADA INMINENTE
**Disparador**: Temperatura ≤ 2°C por más de 10 minutos consecutivos

**Acciones secuenciales a ejecutar**:
1. **Minuto 0** — Enviar alerta push al operario de turno
2. **Minuto 0** — Abrir válvulas de riego por aspersión (zonas A1 a A6)
3. **Minuto 2** — Verificar que la presión de agua es > 2,5 bar
4. **Minuto 5** — Activar calefactores de parafina en zona de mayor riesgo (ladera norte)
5. **Continuo** — Monitorear temperatura cada 2 minutos mientras dure el evento
6. **Fin** — Apagar aspersores SOLO cuando temperatura supere 3°C Y no haya hielo visible
7. **Post-evento** — Inspección visual de florones y brotes nuevos al amanecer

**Consumo de agua estimado**: 3,5 mm/hora × superficie protegida

### 2.2 Protocolo SEQUÍA / ESTRÉS HÍDRICO
**Disparador**: Humedad de suelo < 40% por más de 6 horas

**Acciones**:
1. Activar riego por goteo en modo intensivo (2× la dosis normal)
2. Revisar filtros y emisores por posible obstrucción
3. Aplicar mulch adicional si no se ha hecho recientemente
4. Si CE > 2,5: hacer lavado de sales antes del riego de recuperación
5. Registrar duración del evento de sequía

**Riego de recuperación recomendado**:
- Duración: 45–60 minutos (dosis doble)
- Repetir si humedad no supera 55% en 4 horas

### 2.3 Protocolo LLUVIA EXCESIVA / RIESGO DE ENCHARCAMIENTO
**Disparador**: Humedad de suelo > 90% o precipitación > 40 mm en 6 horas

**Acciones**:
1. Cerrar válvulas de riego automáticamente (modo lluvia)
2. Revisar estado de canales de drenaje
3. Activar alerta de riesgo de Phytophthora y Botrytis
4. Registrar acumulado de lluvia para ajuste de fertilización
5. Aplicar fungicida preventivo (Metalaxil para Phytophthora) si lluvia > 5 días consecutivos

### 2.4 Protocolo pH FUERA DE RANGO
**Disparador**: pH suelo < 4,0 o > 6,0

**Para pH > 6,0 (alcalinización)**:
1. Riego de lavado con agua de lluvia (si disponible) o agua destilada
2. Aplicar azufre elemental agrícola (50 g/m² en zona radicular)
3. Cambio de fertilizante nitrogenado a sulfato de amonio
4. Repetir análisis de pH en 30 días

**Para pH < 3,5 (hiperacidificación)**:
1. Suspender aplicación de enmiendas ácidas
2. Riego de lavado abundante
3. Aplicar pequeña dosis de cal calcítica (max 100 g/m²) disuelta en agua (extremo precaución)
4. Monitoreo diario hasta estabilización

---

## 3. INTERPRETACIÓN DE DATOS DE SENSORES

### 3.1 Combinación Temperatura + Humedad Relativa → Riesgo de Botrytis
La Escala de Riesgo de Botrytis (ERB) combina:

| Temperatura | HR > 85% | HR 70-85% | HR < 70% |
|---|---|---|---|
| 15–25°C | **RIESGO ALTO** → Fungicida preventivo | RIESGO MEDIO → Vigilar | Riesgo bajo |
| 10–15°C | RIESGO MEDIO | Riesgo bajo | Riesgo mínimo |
| > 25°C | Riesgo bajo | Riesgo mínimo | Riesgo mínimo |
| < 10°C | Riesgo bajo | Riesgo mínimo | Riesgo mínimo |

**Regla general**: Si temperatura está entre 15-25°C Y humedad supera 85% por más de 12 horas → **aplicar fungicida preventivo**.

### 3.2 Conductividad Eléctrica → Estado Nutricional
| CE (mS/cm) | Diagnóstico | Acción |
|---|---|---|
| < 0,2 | Suelo empobrecido | Plan de fertilización urgente |
| 0,2 – 0,5 | Bajo nivel nutricional | Aumentar frecuencia de fertilización |
| **0,5 – 2,0** | **Nivel óptimo** | **Mantener programa actual** |
| 2,0 – 3,0 | Exceso de sales | Reducir fertilización 30% + riego de lavado |
| > 3,0 | Estrés salino severo | Suspender fertilización + riego intensivo de lavado |

### 3.3 Luminosidad → Ajuste de Pulverización
- **< 5.000 lux** (nublado): Condiciones favorables para pulverización foliar (menos evaporación)
- **15.000–50.000 lux** (sol): Evitar pulverización foliar (quemaduras por concentración)
- **> 60.000 lux** (sol fuerte): Solo riego al suelo; riesgo alto de fitotoxicidad por aplicaciones foliares

---

## 4. INTERPRETACIÓN DE IMÁGENES DE HOJAS (VISIÓN ARTIFICIAL)

### 4.1 Diagnóstico Visual de Estados Foliares

**HOJA SANA**:
- Color: Verde uniforme e intenso (ausencia de manchas)
- Textura: Lisa, turgente, brillante en haz
- Síntoma en imagen: Dominancia de verde saturado (HSV: H=40-70, S>50%)

**HOJA EN ALERTA (clorosis)**:
- Color: Verde pálido a amarillento
- Síntoma típico: Amarillamiento intervenal (nervios verdes, tejido amarillo)
- Causas posibles:
  - Deficiencia de hierro (pH elevado)
  - Deficiencia de nitrógeno
  - Estrés hídrico prolongado
  - Deficiencia de magnesio

**HOJA CON BOTRYTIS**:
- Manchas circulares/irregulares pardo-grisáceas
- Centro necrótico rodeado de halo clorótico
- Masa de conidios gris (visible como polvo)
- Síntoma en imagen: Presencia de zonas grises/pardas con baja saturación

### 4.2 Protocolo Tras Detección Visual de Botrytis
1. **Confirmar** observando múltiples hojas en la misma planta y plantas vecinas
2. **Calcular porcentaje de planta afectada**:
   - < 10% → Control biológico (*Trichoderma*) y monitoreo
   - 10–30% → Fungicida químico (Iprodione 1,5 g/L)
   - > 30% → Poda sanitaria urgente + fungicida + revisión de toda la zona
3. **Establecer cordón sanitario** si afecta > 5% del total de plantas
4. **Registrar la detección** en el sistema con foto, fecha y coordenadas del lote

---

## 5. COMUNICACIÓN Y ALERTAS DEL SISTEMA

### 5.1 Niveles de Alerta BerryMind
| Nivel | Color | Criterio | Canal de Notificación |
|---|---|---|---|
| **INFO** | 🟢 Verde | Parámetros en rango óptimo | Dashboard solamente |
| **ALERTA** | 🟡 Amarillo | Un sensor fuera de rango óptimo pero no crítico | Dashboard + Log |
| **URGENTE** | 🟠 Naranja | Múltiples sensores en alerta o Botrytis detectada | Dashboard + Notificación |
| **CRÍTICO** | 🔴 Rojo | Helada inminente / parámetro en rango crítico | Dashboard + Notificación + Acción automática |

### 5.2 Comandos del Agente de Riego
Los comandos que el sistema puede emitir de forma automática son:

```json
{
  "comando": "abrir_valvulas",
  "zonas": ["A1", "A2", "A3", "A4", "A5", "A6"],
  "modo": "anti_helada",
  "duracion_estimada": "hasta que T > 3°C",
  "caudal": "3.5 mm/hora"
}
```

```json
{
  "comando": "cerrar_valvulas",
  "zonas": ["todas"],
  "razon": "lluvia_excesiva",
  "humedad_suelo_actual": 92
}
```

```json
{
  "comando": "riego_recuperacion",
  "zonas": ["B1", "B2"],
  "duracion_minutos": 45,
  "razon": "sequia_detectada"
}
```

---

## 6. CALENDARIO DE MANEJO BOYACÁ

### 6.1 Ciclo Productivo en Sotaquirá (Dos Cosechas/Año)
| Período | Meses | Actividades Clave |
|---|---|---|
| Cosecha 1 | Feb–Abr | Cosecha, fertilización post-cosecha, poda |
| Período vegetativo 1 | May–Jul | Aplicaciones foliares, monitoreo de plagas |
| Floración / Cuajado 2 | Ago–Sep | Protección anti-Botrytis, polinización |
| Cosecha 2 | Oct–Dic | Cosecha, análisis de suelo |
| Reposo / Preparación | Ene | Poda de formación, enmiendas de suelo |

### 6.2 Promedios Climáticos Valle de Sotaquirá
| Mes | T. Mín. Prom. | T. Máx. Prom. | Lluvia (mm) | Riesgo Helada |
|---|---|---|---|---|
| Dic–Feb | 4–7°C | 18–22°C | 30–60 | **ALTO** |
| Mar–May | 8–11°C | 20–24°C | 90–130 | Medio |
| Jun–Ago | 7–10°C | 18–21°C | 50–90 | Medio |
| Sep–Nov | 9–12°C | 20–23°C | 100–160 | Bajo |

---

*Elaborado para el proyecto BerryMind — Sistema de Inteligencia Artificial para Monitoreo de Arándanos.*
*Valle de Sotaquirá, Boyacá, Colombia. Versión 1.0 — 2024.*
