# main.py — Sistema Integrado de Control Aeronáutico (RP2040)
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
# CONFIGURACIÓN DE PINES (RP2040)
# ============================================================================

# Sensores ADC (RP2040 solo tiene 3 externos: GP26–GP28). El cuarto usa TEMP.
SENSOR_PINS = {
    'altitude': 26,    # GP26 / ADC0
    'speed': 27,       # GP27 / ADC1
    'attitude': 28,    # GP28 / ADC2
    'light': 'TEMP'    # ADC4 interno (temperatura) como canal 4
}

# Servos (cualquier GP con PWM). Recomendados: GP14, GP15
SERVO_PINS = {
    'aileron': 14,     # GP14
    'elevator': 15     # GP15
}

# Motor PWM (propulsión)
MOTOR_PIN = 13         # GP13 PWM

# Motor a pasos (tren de aterrizaje)
STEPPER_DRIVER = "A4988"  # Cambiar a "ULN2003" si usas ese driver
STEPPER_PINS_A4988 = {
    'step': 18,        # GP18
    'dir': 19,         # GP19
    'en': 5            # GP5 (ENABLE, LOW activo)
}
# Nota: Esta configuración ULN2003 usa GP26–GP28, que confligen con ADC.
# Si eliges ULN2003, remapea sensores a otros pines o usa TEMP + entradas digitales.
STEPPER_PINS_ULN2003 = {
    'pins': [26, 27, 28, 22]
}
ENDSTOP_PIN = 4        # GP4 con pull-up interno


# ============================================================================
# UTILIDADES DE INTERFAZ
# ============================================================================

def clear_screen():
    print("\033[2J\033[H", end='')


def print_banner():
    print("\n" + "═" * 66)
    print("║" + " " * 64 + "║")
    print("║" + "  SISTEMA DE CONTROL AERONÁUTICO - SISELA v1.0 (RP2040)".center(64) + "║")
    print("║" + "  Práctica 8: Integración Total".center(64) + "║")
    print("║" + " " * 64 + "║")
    print("═" * 66)
    print()


def print_menu():
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
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    result = poll.poll(timeout_ms if timeout_ms > 0 else -1)
    if result:
        return sys.stdin.read(1)
    return None


def check_menu_command():
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    if poll.poll(0):
        char = sys.stdin.read(1)
        if char and char.lower() == 'm':
            return True
    return False


# ============================================================================
# MODO 1: PANEL DE INSTRUMENTOS
# ============================================================================

def mode_instruments(sensors, controls, propulsion, landing_gear):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           PANEL DE INSTRUMENTOS - MODO MONITOREO            ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Presiona 'm' + ENTER para volver al menú                   ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    while True:
        sensor_data = sensors.read_all()
        clear_screen()
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│ INSTRUMENTOS DE VUELO                       [m] Menú        │")
        print("├─────────────────────────────────────────────────────────────┤")

        for name in ['altitude', 'speed', 'attitude', 'light']:
            value = sensor_data[name]
            pct = sensors.get_percentage(name)
            unit = sensors.scales[name]['unit']
            bar_w = 10
            filled = int((pct / 100.0) * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)
            label_map = {'altitude': 'Altitud', 'speed': 'Velocidad', 'attitude': 'Actitud', 'light': 'Luminosidad'}
            label = label_map[name].ljust(12)
            value_str = f"{value:7.1f} {unit:3s}"
            print(f"│ {label} {value_str} [{bar}] {pct:5.1f}%{' '*13}│")

        print("├─────────────────────────────────────────────────────────────┤")
        print("│ SUPERFICIES DE CONTROL                                      │")
        for name in ['aileron', 'elevator']:
            angle = controls.get_angle(name)
            bar_w = 10
            filled = int((angle / 180.0) * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)
            label_map = {'aileron': 'Alerón', 'elevator': 'Elevador'}
            label = label_map[name].ljust(12)
            print(f"│ {label} {angle:3d}° [{bar}]{' '*28}│")

        throttle = propulsion.get_throttle()
        bar_w = 10
        filled = int((throttle / 100.0) * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        print(f"│ Motor{' '*6} {throttle:3d}% [{bar}]{' '*28}│")

        gear_state = landing_gear.get_state() if landing_gear else 'NO DISPONIBLE'
        print(f"│ Tren:{' '*7} {gear_state.ljust(42)}│")
        print("└─────────────────────────────────────────────────────────────┘")

        if check_menu_command():
            break
        utime.sleep_ms(200)


# ============================================================================
# MODO 2: CONTROL MANUAL DE SUPERFICIES
# ============================================================================

def mode_manual_surfaces(controls):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║          CONTROL MANUAL DE SUPERFICIES DE VUELO              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [a/d] Alerón izquierda/derecha                              ║")
    print("║  [w/s] Elevador arriba/abajo                                 ║")
    print("║  [0-9] Ángulo directo (x20, ej: 5 → 100°)                    ║")
    print("║  [c]   Centrar todas (90°)                                   ║")
    print("║  [m]   Menú                                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    print(controls.get_status())
    while True:
        key = wait_key(100)
        if key:
            k = key.lower()
            if k == 'm':
                break
            elif k == 'a':
                controls.increment('aileron', -5)
            elif k == 'd':
                controls.increment('aileron', 5)
            elif k == 'w':
                controls.increment('elevator', 5)
            elif k == 's':
                controls.increment('elevator', -5)
            elif k == 'c':
                controls.center_all()
            elif k.isdigit():
                angle = int(k) * 20
                controls.set_surface('aileron', angle)
                controls.set_surface('elevator', angle)


# ============================================================================
# MODO 3: CONTROL DE POTENCIA
# ============================================================================

def mode_power_control(propulsion):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           CONTROL DE POTENCIA (MOTOR/HÉLICE)                ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [+/-]   Incrementar/decrementar (5%)                        ║")
    print("║  [0-9]   Potencia directa (x10)                              ║")
    print("║  [SPACE] Emergencia (corte)                                  ║")
    print("║  [r]     Rampa suave a 100%                                  ║")
    print("║  [m]     Menú                                                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    print(propulsion.get_status())
    while True:
        key = wait_key(100)
        if key:
            if key.lower() == 'm':
                break
            elif key == '+':
                propulsion.increment(5)
            elif key == '-':
                propulsion.increment(-5)
            elif key == ' ':
                propulsion.emergency_stop()
            elif key.lower() == 'r':
                propulsion.ramp_up(100, 3000)
            elif key.isdigit():
                propulsion.set_throttle(int(key) * 10)


# ============================================================================
# MODO 4: CONTROL DE TREN DE ATERRIZAJE
# ============================================================================

def mode_landing_gear_control(landing_gear):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║         CONTROL DE TREN DE ATERRIZAJE (STEPPER)             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [e] Extender  [r] Retraer  [h] Homing  [s] Estado  [m] Menú ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    print(landing_gear.get_status())
    while True:
        key = wait_key(100)
        if key:
            k = key.lower()
            if k == 'm':
                break
            elif k == 'e':
                landing_gear.extend()
            elif k == 'r':
                landing_gear.retract()
            elif k == 'h':
                landing_gear.homing()
            elif k == 's':
                print(landing_gear.get_status())


# ============================================================================
# MODO 5: PILOTO AUTOMÁTICO SIMPLE
# ============================================================================

def mode_autopilot(sensors, controls, propulsion):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║            MODO PILOTO AUTOMÁTICO (SIMPLE)                  ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    propulsion.ramp_up(60, 2000)
    iteration = 0
    while True:
        data = sensors.read_all()
        attitude = data['attitude']
        target_elevator = 90 - (attitude * 0.5)
        target_elevator = max(45, min(135, target_elevator))
        controls.set_surface('elevator', int(target_elevator))
        controls.set_surface('aileron', 90)
        if iteration % 10 == 0:
            print(f"[AUTO] Actitud: {attitude:+6.1f}° → Elevador: {int(target_elevator):3d}°")
        iteration += 1
        if check_menu_command():
            controls.center_all()
            propulsion.ramp_down(2000)
            break
        utime.sleep_ms(100)


# ============================================================================
# MODO 6: DIAGNÓSTICO
# ============================================================================

def mode_diagnostics(sensors, controls, propulsion, landing_gear):
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              DIAGNÓSTICO DEL SISTEMA                         ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    errors = []
    print("► Test de sensores ADC...")
    data = sensors.read_all()
    for name, value in data.items():
        pct = sensors.get_percentage(name)
        status = "✓ OK" if 1 < pct < 99 else "⚠ VERIFICAR"
        print(f"  {name.capitalize().ljust(12)}: {value:7.1f} ({pct:5.1f}%) {status}")
        if pct < 1 or pct > 99:
            errors.append(f"Sensor {name} en extremo de rango")
    print("\n► Test de servos...")
    for name in ['aileron', 'elevator']:
        print(f"  Barrido {name}...", end=' ')
        controls.sweep(name, 1000)
        print("✓")
    print("\n► Test de motor PWM...")
    print("  Rampa 0% → 50% → 0%...", end=' ')
    propulsion.ramp_up(50, 1500)
    utime.sleep_ms(500)
    propulsion.ramp_down(1500)
    print("✓")
    if landing_gear:
        print("\n► Test de tren de aterrizaje...")
        print(f"  Estado actual: {landing_gear.get_state()}")
        print(f"  Endstop: {'ACTIVADO' if landing_gear.is_endstop_triggered() else 'LIBRE'}")
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
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                   CONFIGURACIÓN DEL SISTEMA                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  [1] Calibrar sensores                                       ║")
    print("║  [2] Ajustar límites de servos                               ║")
    print("║  [3] Test rápido de componentes                              ║")
    print("║  [m] Menú principal                                          ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    opt = input("Selecciona opción: ").strip()
    if opt == '1':
        print("\nCALIBRACIÓN DE SENSORES (vista previa de lecturas)")
        print(sensors.get_summary())
        print("\nPor ahora usando valores por defecto; ajuste manual pendiente.")
    elif opt == '2':
        controls.center_all()
        print("Servos centrados a 90°")
    elif opt == '3':
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
    print_banner()
    print("Inicializando subsistemas...\n")
    print("  [1/4] Sensores ADC...", end=' ')
    sensors = FlightSensors(SENSOR_PINS)
    print("✓")
    print("  [2/4] Superficies de control (servos)...", end=' ')
    controls = FlightControls(SERVO_PINS)
    print("✓")
    print("  [3/4] Sistema de propulsión (PWM)...", end=' ')
    propulsion = PropulsionSystem(MOTOR_PIN)
    print("✓")
    print("  [4/4] Tren de aterrizaje (stepper)...", end=' ')
    stepper_pins = STEPPER_PINS_A4988 if STEPPER_DRIVER == "A4988" else STEPPER_PINS_ULN2003
    try:
        landing_gear = LandingGear(driver_type=STEPPER_DRIVER, pins=stepper_pins, endstop_pin=ENDSTOP_PIN)
        print("✓")
    except RuntimeError as e:
        print(f"⚠ {e}")
        landing_gear = None
    print("\n✓ Sistema inicializado correctamente\n")
    utime.sleep(1)

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


if __name__ == '__main__':
    main()
