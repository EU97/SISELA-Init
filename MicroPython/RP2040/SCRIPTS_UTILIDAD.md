# 🔧 Scripts de Utilidad - Migración ESP32 → RP2040

## 📋 Comandos PowerShell Útiles

### Copiar estructura de prácticas

```powershell
# Copiar P3 de ESP32 a RP2040
Copy-Item -Recurse MicroPython\ESP32\P3\* MicroPython\RP2040\P3\ -Force

# Copiar P4
Copy-Item -Recurse MicroPython\ESP32\P4\* MicroPython\RP2040\P4\ -Force

# Copiar P5
Copy-Item -Recurse MicroPython\ESP32\P5\* MicroPython\RP2040\P5\ -Force

# Copiar P6
Copy-Item -Recurse MicroPython\ESP32\P6\* MicroPython\RP2040\P6\ -Force

# Copiar P7
Copy-Item -Recurse MicroPython\ESP32\P7\* MicroPython\RP2040\P7\ -Force

# Copiar P8
Copy-Item -Recurse MicroPython\ESP32\P8\* MicroPython\RP2040\P8\ -Force
```

### Copiar TODAS las prácticas restantes de una vez
```powershell
# Copiar P3-P8
3..8 | ForEach-Object { 
    $p = "P$_"
    Copy-Item -Recurse "MicroPython\ESP32\$p\*" "MicroPython\RP2040\$p\" -Force
    Write-Host "✓ Copiado $p" -ForegroundColor Green
}
```

---

## 🔍 Buscar y Reemplazar Masivo

### Script para reemplazar pines en múltiples archivos

```powershell
# Reemplazar GPIO por GP en archivos .py
$files = Get-ChildItem -Path "MicroPython\RP2040\" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    # Reemplazos comunes
    $content = $content -replace 'GPIO2', 'GP25'    # LED onboard
    $content = $content -replace 'GPIO4', 'GP16'    # LED2
    $content = $content -replace 'GPIO5', 'GP17'    # LED3
    $content = $content -replace 'GPIO13', 'GP14'   # BTN1
    $content = $content -replace 'GPIO14', 'GP15'   # BTN2
    $content = $content -replace 'GPIO34', 'GP26'   # ADC0
    $content = $content -replace 'GPIO35', 'GP27'   # ADC1
    $content = $content -replace 'GPIO32', 'GP28'   # ADC2
    
    Set-Content $file.FullName -Value $content
    Write-Host "✓ Actualizado: $($file.Name)" -ForegroundColor Cyan
}
```

### Reemplazar código ADC

```powershell
# Buscar y reemplazar patrones de ADC en archivos Python
$files = Get-ChildItem -Path "MicroPython\RP2040\" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    # Cambiar inicialización ADC
    $content = $content -replace 'ADC\(Pin\((\d+)\)\)', 'ADC($1)'
    
    # Eliminar configuración ESP32
    $content = $content -replace 'adc\.atten\(ADC\.ATTN_11DB\)\s*', ''
    $content = $content -replace 'adc\.width\(ADC\.WIDTH_12BIT\)\s*', ''
    
    # Cambiar función de lectura
    $content = $content -replace 'adc\.read\(\)', 'adc.read_u16()'
    
    # Cambiar constante ADC_MAX
    $content = $content -replace 'ADC_MAX\s*=\s*4095', 'ADC_MAX = 65535'
    
    Set-Content $file.FullName -Value $content
    Write-Host "✓ ADC actualizado: $($file.Name)" -ForegroundColor Yellow
}
```

---

## 📊 Verificación de Archivos

### Listar estructura de RP2040

```powershell
# Ver árbol de directorios
tree MicroPython\RP2040 /F

# Ver solo prácticas completas (con main.py)
Get-ChildItem -Path "MicroPython\RP2040\P*\main.py" -Recurse | 
    Select-Object Directory, Name
```

### Contar líneas de código

```powershell
# Contar líneas en todos los .py de RP2040
$totalLines = 0
Get-ChildItem -Path "MicroPython\RP2040\" -Recurse -Filter "*.py" | ForEach-Object {
    $lines = (Get-Content $_.FullName).Count
    $totalLines += $lines
    Write-Host "$($_.Name): $lines líneas"
}
Write-Host "`nTotal: $totalLines líneas" -ForegroundColor Green
```

---

## 🔧 Comandos de Desarrollo

### Instalar Thonny (si no lo tienes)

```powershell
# Descargar e instalar Thonny
winget install --id=AivarAnnamaa.Thonny -e
```

### Instalar MicroPython en Pico

```powershell
# 1. Mantén presionado BOOTSEL y conecta el Pico
# 2. Aparecerá como unidad RPI-RP2

# Descargar firmware (PowerShell)
$url = "https://micropython.org/resources/firmware/RPI_PICO-20241025-v1.24.0.uf2"
$output = "$env:USERPROFILE\Downloads\micropython-pico.uf2"
Invoke-WebRequest -Uri $url -OutFile $output

# Copiar a Pico (ajusta la letra de unidad)
Copy-Item $output "E:\" -Force

Write-Host "✓ MicroPython instalado. El Pico se reiniciará automáticamente." -ForegroundColor Green
```

### Subir archivos a Pico con ampy (alternativa a Thonny)

```powershell
# Instalar ampy
pip install adafruit-ampy

# Listar archivos en Pico
ampy --port COM3 ls

# Subir main.py
ampy --port COM3 put MicroPython\RP2040\P1\main.py

# Subir carpeta lib completa
ampy --port COM3 put MicroPython\RP2040\P8\lib
```

---

## 📝 Generar Reportes

### Crear reporte de estado de prácticas

```powershell
# Script para generar reporte Markdown
$report = @"
# Estado de Prácticas RP2040

Generado: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

| Práctica | boot.py | main.py | PINES.md | README.md | Estado |
|----------|---------|---------|----------|-----------|--------|
"@

1..8 | ForEach-Object {
    $p = "P$_"
    $path = "MicroPython\RP2040\$p"
    
    $boot = if (Test-Path "$path\boot.py") { "✅" } else { "❌" }
    $main = if (Test-Path "$path\main.py") { "✅" } else { "❌" }
    $pines = if (Test-Path "$path\PINES.md") { "✅" } else { "❌" }
    $readme = if (Test-Path "$path\README.md") { "✅" } else { "❌" }
    
    $completitud = @($boot, $main, $pines, $readme) | Where-Object { $_ -eq "✅" } | Measure-Object | Select-Object -ExpandProperty Count
    $estado = switch ($completitud) {
        4 { "🟢 Completa" }
        3 { "🟡 Casi completa" }
        2 { "🟠 En progreso" }
        1 { "🔴 Iniciada" }
        0 { "⚪ Pendiente" }
    }
    
    $report += "`n| $p | $boot | $main | $pines | $readme | $estado |"
}

$report | Out-File "MicroPython\RP2040\ESTADO_PRACTICAS.md" -Encoding UTF8
Write-Host "✓ Reporte generado en ESTADO_PRACTICAS.md" -ForegroundColor Green
```

---

## 🧪 Scripts de Prueba

### Verificar sintaxis Python

```powershell
# Verificar sintaxis de todos los .py en RP2040
Get-ChildItem -Path "MicroPython\RP2040\" -Recurse -Filter "*.py" | ForEach-Object {
    Write-Host "Verificando $($_.Name)..." -NoNewline
    python -m py_compile $_.FullName 2>$null
    if ($?) {
        Write-Host " ✓ OK" -ForegroundColor Green
    } else {
        Write-Host " ✗ ERROR" -ForegroundColor Red
    }
}
```

### Buscar TODOs y FIXMEs

```powershell
# Buscar comentarios pendientes
Select-String -Path "MicroPython\RP2040\*.py" -Pattern "TODO|FIXME|XXX" -Recurse | 
    Select-Object Filename, LineNumber, Line |
    Format-Table -AutoSize
```

---

## 🔄 Sincronización con Git

### Comandos Git útiles

```powershell
# Ver estado actual
git status

# Añadir solo archivos RP2040
git add MicroPython/RP2040/

# Commit con mensaje descriptivo
git commit -m "feat(RP2040): Completar P1 y P2, añadir guías de migración"

# Push a GitHub
git push origin main

# Ver diferencias antes de commit
git diff MicroPython/RP2040/
```

---

## 📦 Backup y Compresión

### Crear backup de RP2040

```powershell
# Crear zip de todo RP2040
$date = Get-Date -Format "yyyyMMdd-HHmm"
$output = "SISELA-RP2040-Backup-$date.zip"

Compress-Archive -Path "MicroPython\RP2040\*" -DestinationPath $output -Force
Write-Host "✓ Backup creado: $output" -ForegroundColor Green
```

### Exportar solo prácticas completas

```powershell
# Crear zip solo de P1 y P2 (completas)
$output = "SISELA-RP2040-P1-P2.zip"
Compress-Archive -Path "MicroPython\RP2040\P1", "MicroPython\RP2040\P2" -DestinationPath $output -Force
```

---

## 🎯 Script Todo-en-Uno

### Migración completa automatizada (usar con precaución)

```powershell
# Script maestro de migración
Write-Host "=== MIGRACIÓN ESP32 → RP2040 ===" -ForegroundColor Cyan

# 1. Copiar estructuras
Write-Host "`n1. Copiando estructuras P3-P8..." -ForegroundColor Yellow
3..8 | ForEach-Object { 
    Copy-Item -Recurse "MicroPython\ESP32\P$_\*" "MicroPython\RP2040\P$_\" -Force
}

# 2. Actualizar pines
Write-Host "`n2. Actualizando mapeo de pines..." -ForegroundColor Yellow
$files = Get-ChildItem -Path "MicroPython\RP2040\P[3-8]" -Recurse -Filter "*.py"
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $content = $content -replace 'GPIO34', 'GP26'
    $content = $content -replace 'GPIO35', 'GP27'
    $content = $content -replace 'GPIO32', 'GP28'
    Set-Content $file.FullName -Value $content
}

# 3. Actualizar ADC
Write-Host "`n3. Actualizando código ADC..." -ForegroundColor Yellow
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $content = $content -replace 'ADC\(Pin\((\d+)\)\)', 'ADC($1)'
    $content = $content -replace 'adc\.read\(\)', 'adc.read_u16()'
    $content = $content -replace 'ADC_MAX\s*=\s*4095', 'ADC_MAX = 65535'
    Set-Content $file.FullName -Value $content
}

# 4. Generar reporte
Write-Host "`n4. Generando reporte..." -ForegroundColor Yellow
# (código del reporte anterior)

Write-Host "`n✓ Migración completada. Revisa manualmente cada práctica." -ForegroundColor Green
```

---

## 📖 Alias Útiles

### Crear alias en PowerShell profile

```powershell
# Editar profile
notepad $PROFILE

# Añadir estos alias:
function rp2040 { Set-Location "C:\Users\edgar\Documents\GitHub\SISELA-Init\MicroPython\RP2040" }
function esp32 { Set-Location "C:\Users\edgar\Documents\GitHub\SISELA-Init\MicroPython\ESP32" }
function guia { code "C:\Users\edgar\Documents\GitHub\SISELA-Init\MicroPython\RP2040\GUIA_MIGRACION.md" }

# Guardar y recargar
. $PROFILE
```

---

**Última actualización**: Noviembre 2025  
**Plataforma**: Windows PowerShell 5.1+  
**Repositorio**: EU97/SISELA-Init