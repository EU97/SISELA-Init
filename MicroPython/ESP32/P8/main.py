# main.py — Sistema Integrado de Control Aeronáutico
# Práctica 8: Integración de sensores y actuadores

import sys
import utime
import uselect

# Importar módulos del sistema
from lib.sensors import FlightSensors
from lib.flight_controls import FlightControls
from lib.propulsion import PropulsionSystem
from lib.landing_gear import LandingGear


# ============================================================================
# CONFIGURACIÓN DE PINES
# ============================================================================

# Sensores ADC
SENSOR_PINS = {
    'altitude': 34,    # ADC1_CH6
    'speed': 35,       # ADC1_CH7
    'attitude': 32,    # ADC1_CH4
    'light': 33        # ADC1_CH5
}

# Servos (superficies de control)
SERVO_PINS = {
    'aileron': 25,     # Alerón
    'elevator': 26     # Elevador
}

# Motor PWM (propulsión)
MOTOR_PIN = 18

# Motor a pasos (tren de aterrizaje)
STEPPER_DRIVER = "A4988"  # Cambiar a "ULN2003" si usas ese driver
STEPPER_PINS_A4988 = {
    'step': 19,
    'dir': 21,
    'en': 5
}
STEPPER_PINS_ULN2003 = {
    'pins': [19, 21, 22, 23]
}
ENDSTOP_PIN = 4


# ============================================================================
# UTILIDADES DE INTERFAZ
# ============================================================================

def clear_screen():
    """Limpia la pantalla (ANSI escape codes)"""
    print("\033[2J\033[H", end='')


def print_banner():
    """Imprime banner principal del sistema"""
    print("\n" + "═" * 66)
    print("║" + " " * 64 + "║")
    print("║" + "  SISTEMA DE CONTROL AERONÁUTICO - SISELA v1.0".center(64) + "║")
    print("║" + "  Práctica 8: Integración Total".center(64) + "║")
    print("║" + " " * 64 + "║")
    print("═" * 66)
    print()


def print_menu():
    """Imprime menú principal"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║        SISTEMA DE CONTROL AERONÁUTICO - SISELA v1.0         ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [1] Panel de instrumentos (monitoreo en tiempo real)       ║")
    print("║  [2] Control manual de superficies                          ║")
    print("║  [3] Control de potencia (motor/hélice)                     ║")
    print("║  [4] Control de tren de aterrizaje                          ║")
    print("║  [5] Modo automático (piloto automático simple)             ║")
    print("║  [6] Diagnóstico del sistema                                ║")
    print("║  [7] Configuración                                          ║")
    print("║  [q] Salir                                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\nSelecciona una opción: ", end='')


def wait_key(timeout_ms=0):
    """
    Espera una tecla con timeout opcional
    
    Args:
        timeout_ms: Timeout en ms, 0 = sin timeout
    
    Returns:
        str: Tecla presionada o None si timeout
    """
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    
    result = poll.poll(timeout_ms if timeout_ms > 0 else -1)
    if result:
        return sys.stdin.read(1)
    return None


def check_menu_command():
    """Verifica si se presionó 'm' para volver al menú"""
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    
    if poll.poll(0):
        char = sys.stdin.read(1)
        if char.lower() == 'm':
            return True
    return False


# ============================================================================
# MODO 1: PANEL DE INSTRUMENTOS
# ============================================================================

def mode_instruments(sensors, controls, propulsion, landing_gear):
    """Panel de instrumentos con monitoreo en tiempo real"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           PANEL DE INSTRUMENTOS - MODO MONITOREO            ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Presiona 'm' + ENTER para volver al menú                   ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    while True:
        # Leer sensores
        sensor_data = sensors.read_all()
        
        # Construir display
        print("\033[2J\033[H", end='')  # Clear screen
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│ INSTRUMENTOS DE VUELO                       [m] Menú        │")
        print("├─────────────────────────────────────────────────────────────┤")
        
        # Sensores
        for name in ['altitude', 'speed', 'attitude', 'light']:
            value = sensor_data[name]
            pct = sensors.get_percentage(name)
            unit = sensors.scales[name]['unit']
            
            # Barra de progreso
            bar_width = 10
            filled = int((pct / 100.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            label_map = {
                'altitude': 'Altitud',
                'speed': 'Velocidad',
                'attitude': 'Actitud',
                'light': 'Luminosidad'
            }
            label = label_map[name].ljust(12)
            value_str = f"{value:7.1f} {unit:3s}"
            print(f"│ {label} {value_str} [{bar}] {pct:5.1f}%{' '*13}│")
        
        print("├─────────────────────────────────────────────────────────────┤")
        print("│ SUPERFICIES DE CONTROL                                      │")
        
        # Servos
        for name in ['aileron', 'elevator']:
            angle = controls.get_angle(name)
            bar_width = 10
            filled = int((angle / 180.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            label_map = {'aileron': 'Alerón', 'elevator': 'Elevador'}
            label = label_map[name].ljust(12)
            print(f"│ {label} {angle:3d}° [{bar}]{' '*28}│")
        
        # Motor
        throttle = propulsion.get_throttle()
        bar_width = 10
        filled = int((throttle / 100.0) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"│ Motor{' '*6} {throttle:3d}% [{bar}]{' '*28}│")
        
        # Tren
        gear_state = landing_gear.get_state()
        print(f"│ Tren:{' '*7} {gear_state.ljust(42)}│")
        
        print("└─────────────────────────────────────────────────────────────┘")
        
        # Check for menu command
        if check_menu_command():
            break
        
        utime.sleep_ms(200)  # Actualizar ~5 Hz


# ============================================================================
# MODO 2: CONTROL MANUAL DE SUPERFICIES
# ============================================================================

def mode_manual_surfaces(controls):
    """Control manual de servos (superficies de vuelo)"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║          CONTROL MANUAL DE SUPERFICIES DE VUELO              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Controles:                                                  ║")
    print("║    [a/d] Alerón izquierda/derecha                            ║")
    print("║    [w/s] Elevador arriba/abajo                               ║")
    print("║    [0-9] Ángulo directo (multiplicar x20, ej: 5 → 100°)      ║")
    print("║    [c]   Centrar todas las superficies (90°)                 ║")
    print("║    [m]   Volver al menú                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print(controls.get_status())
    
    while True:
        key = wait_key(100)
        
        if key:
            key = key.lower()
            
            if key == 'm':
                break
            elif key == 'a':
                controls.increment('aileron', -5)
                print(f"Alerón: {controls.get_angle('aileron')}°")
            elif key == 'd':
                controls.increment('aileron', 5)
                print(f"Alerón: {controls.get_angle('aileron')}°")
            elif key == 'w':
                controls.increment('elevator', 5)
                print(f"Elevador: {controls.get_angle('elevator')}°")
            elif key == 's':
                controls.increment('elevator', -5)
                print(f"Elevador: {controls.get_angle('elevator')}°")
            elif key == 'c':
                controls.center_all()
                print("Todas las superficies centradas a 90°")
                print(controls.get_status())
            elif key.isdigit():
                angle = int(key) * 20
                controls.set_surface('aileron', angle)
                controls.set_surface('elevator', angle)
                print(f"Superficies establecidas a {angle}°")


# ============================================================================
# MODO 3: CONTROL DE POTENCIA
# ============================================================================

def mode_power_control(propulsion):
    """Control del sistema de propulsión"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           CONTROL DE POTENCIA (MOTOR/HÉLICE)                ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Controles:                                                  ║")
    print("║    [+/-]   Incrementar/decrementar potencia (5%)             ║")
    print("║    [0-9]   Potencia directa (multiplicar x10, ej: 7 → 70%)   ║")
    print("║    [SPACE] Emergencia (corte motor)                          ║")
    print("║    [r]     Rampa suave a 100%                                ║")
    print("║    [m]     Volver al menú                                    ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print(propulsion.get_status())
    
    while True:
        key = wait_key(100)
        
        if key:
            if key.lower() == 'm':
                break
            elif key == '+':
                propulsion.increment(5)
                print(f"Potencia: {propulsion.get_throttle()}%")
            elif key == '-':
                propulsion.increment(-5)
                print(f"Potencia: {propulsion.get_throttle()}%")
            elif key == ' ':
                propulsion.emergency_stop()
                print("¡EMERGENCIA! Motor detenido")
                print(propulsion.get_status())
            elif key.lower() == 'r':
                print("Rampa de aceleración a 100%...")
                propulsion.ramp_up(100, 3000)
                print(propulsion.get_status())
            elif key.isdigit():
                throttle = int(key) * 10
                propulsion.set_throttle(throttle)
                print(f"Potencia establecida a {throttle}%")


# ============================================================================
# MODO 4: CONTROL DE TREN DE ATERRIZAJE
# ============================================================================

def mode_landing_gear_control(landing_gear):
    """Control del tren de aterrizaje"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║         CONTROL DE TREN DE ATERRIZAJE (STEPPER)             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Controles:                                                  ║")
    print("║    [e]   Extender tren (hasta endstop)                       ║")
    print("║    [r]   Retraer tren                                        ║")
    print("║    [h]   Homing (búsqueda de límite)                         ║")
    print("║    [s]   Estado actual                                       ║")
    print("║    [m]   Volver al menú                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print(landing_gear.get_status())
    
    while True:
        key = wait_key(100)
        
        if key:
            key = key.lower()
            
            if key == 'm':
                break
            elif key == 'e':
                landing_gear.extend()
                print(landing_gear.get_status())
            elif key == 'r':
                landing_gear.retract()
                print(landing_gear.get_status())
            elif key == 'h':
                landing_gear.homing()
                print(landing_gear.get_status())
            elif key == 's':
                print(landing_gear.get_status())


# ============================================================================
# MODO 5: PILOTO AUTOMÁTICO SIMPLE
# ============================================================================

def mode_autopilot(sensors, controls, propulsion):
    """Piloto automático simple: mantiene estabilidad básica"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║            MODO PILOTO AUTOMÁTICO (SIMPLE)                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Sistema automatizado activo:                                ║")
    print("║    • Lee sensores continuamente                              ║")
    print("║    • Ajusta superficies para compensar actitud               ║")
    print("║    • Mantiene potencia constante al 60%                      ║")
    print("║                                                              ║")
    print("║  Presiona 'm' + ENTER para desactivar                        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Establecer potencia crucero
    propulsion.ramp_up(60, 2000)
    print("Potencia de crucero: 60%")
    
    iteration = 0
    
    while True:
        # Leer sensores
        data = sensors.read_all()
        
        # Lógica simple de compensación de actitud
        attitude = data['attitude']
        
        # Actitud es -90 a +90, centrado en 0
        # Ajustar elevador inversamente
        target_elevator = 90 - (attitude * 0.5)  # Factor de compensación
        target_elevator = max(45, min(135, target_elevator))  # Limitar 45-135°
        
        controls.set_surface('elevator', int(target_elevator))
        
        # Centrar alerón (sin control lateral por ahora)
        controls.set_surface('aileron', 90)
        
        # Display periódico
        if iteration % 10 == 0:
            print(f"[AUTO] Actitud: {attitude:+6.1f}° → Elevador: {int(target_elevator):3d}°")
        
        iteration += 1
        
        # Check menu
        if check_menu_command():
            print("\nDesactivando piloto automático...")
            controls.center_all()
            propulsion.ramp_down(2000)
            break
        
        utime.sleep_ms(100)


# ============================================================================
# MODO 6: DIAGNÓSTICO
# ============================================================================

def mode_diagnostics(sensors, controls, propulsion, landing_gear):
    """Ejecuta diagnóstico de todos los subsistemas"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              DIAGNÓSTICO DEL SISTEMA                         ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    errors = []
    
    # Test sensores
    print("► Test de sensores ADC...")
    data = sensors.read_all()
    for name, value in data.items():
        pct = sensors.get_percentage(name)
        status = "✓ OK" if 1 < pct < 99 else "⚠ VERIFICAR"
        print(f"  {name.capitalize().ljust(12)}: {value:7.1f} ({pct:5.1f}%) {status}")
        if pct < 1 or pct > 99:
            errors.append(f"Sensor {name} en extremo de rango")
    
    # Test servos
    print("\n► Test de servos...")
    for name in ['aileron', 'elevator']:
        print(f"  Barrido {name}...", end=' ')
        controls.sweep(name, 1000)
        print("✓")
    
    # Test motor
    print("\n► Test de motor PWM...")
    print("  Rampa 0% → 50% → 0%...", end=' ')
    propulsion.ramp_up(50, 1500)
    utime.sleep_ms(500)
    propulsion.ramp_down(1500)
    print("✓")
    
    # Test tren
    print("\n► Test de tren de aterrizaje...")
    print(f"  Estado actual: {landing_gear.get_state()}")
    print(f"  Endstop: {'ACTIVADO' if landing_gear.is_endstop_triggered() else 'LIBRE'}")
    
    # Resumen
    print("\n" + "─" * 64)
    if errors:
        print("⚠ ADVERTENCIAS:")
        for err in errors:
            print(f"  • {err}")
    else:
        print("✓ Todos los subsistemas funcionando correctamente")
    print("─" * 64)
    
    input("\nPresiona ENTER para continuar...")


# ============================================================================
# MODO 7: CONFIGURACIÓN
# ============================================================================

def mode_configuration(sensors, controls, propulsion):
    """Menú de configuración del sistema"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                   CONFIGURACIÓN DEL SISTEMA                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [1] Calibrar sensores                                       ║")
    print("║  [2] Ajustar límites de servos                               ║")
    print("║  [3] Test rápido de componentes                              ║")
    print("║  [m] Volver al menú principal                                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    opt = input("Selecciona opción: ").strip()
    
    if opt == '1':
        print("\nCALIBRACIÓN DE SENSORES")
        print("(Funcionalidad de calibración aquí)")
        print("Por ahora, usando valores por defecto")
    elif opt == '2':
        print("\nAJUSTE DE LÍMITES DE SERVOS")
        controls.center_all()
        print("Servos centrados a 90° (posición neutral)")
    elif opt == '3':
        print("\nTEST RÁPIDO...")
        controls.sweep('aileron', 1000)
        propulsion.set_throttle(30)
        utime.sleep_ms(500)
        propulsion.set_throttle(0)
        print("✓ Test completado")
    
    input("\nPresiona ENTER para continuar...")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal del sistema integrado"""
    
    print_banner()
    
    print("Inicializando subsistemas...")
    print()
    
    # Inicializar sensores
    print("  [1/4] Sensores ADC...", end=' ')
    sensors = FlightSensors(SENSOR_PINS)
    print("✓")
    
    # Inicializar controles de vuelo (servos)
    print("  [2/4] Superficies de control (servos)...", end=' ')
    controls = FlightControls(SERVO_PINS)
    print("✓")
    
    # Inicializar propulsión
    print("  [3/4] Sistema de propulsión (PWM)...", end=' ')
    propulsion = PropulsionSystem(MOTOR_PIN)
    print("✓")
    
    # Inicializar tren de aterrizaje
    print("  [4/4] Tren de aterrizaje (stepper)...", end=' ')
    stepper_pins = STEPPER_PINS_A4988 if STEPPER_DRIVER == "A4988" else STEPPER_PINS_ULN2003
    try:
        landing_gear = LandingGear(
            driver_type=STEPPER_DRIVER,
            pins=stepper_pins,
            endstop_pin=ENDSTOP_PIN
        )
        print("✓")
    except RuntimeError as e:
        print(f"⚠ {e}")
        landing_gear = None
    
    print("\n✓ Sistema inicializado correctamente\n")
    utime.sleep(1)
    
    # Bucle principal del menú
    try:
        while True:
            print_menu()
            choice = input().strip()
            
            if choice == '1':
                mode_instruments(sensors, controls, propulsion, landing_gear)
            elif choice == '2':
                mode_manual_surfaces(controls)
            elif choice == '3':
                mode_power_control(propulsion)
            elif choice == '4':
                if landing_gear:
                    mode_landing_gear_control(landing_gear)
                else:
                    print("\n⚠ Tren de aterrizaje no disponible")
                    input("Presiona ENTER para continuar...")
            elif choice == '5':
                mode_autopilot(sensors, controls, propulsion)
            elif choice == '6':
                mode_diagnostics(sensors, controls, propulsion, landing_gear)
            elif choice == '7':
                mode_configuration(sensors, controls, propulsion)
            elif choice.lower() == 'q':
                print("\nCerrando sistema...")
                break
            else:
                print("\n⚠ Opción inválida")
                utime.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupción detectada")
    
    finally:
        # Limpieza y apagado
        print("\nApagando subsistemas...")
        controls.center_all()
        propulsion.set_throttle(0)
        
        print("  Liberando recursos...", end=' ')
        controls.deinit()
        propulsion.deinit()
        if landing_gear:
            landing_gear.deinit()
        sensors.deinit()
        print("✓")
        
        print("\nSistema apagado. Hasta pronto.\n")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    main()
