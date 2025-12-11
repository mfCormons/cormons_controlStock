# Script para hacer push a GitHub
Write-Host "=== Push a GitHub ===" -ForegroundColor Green

# Verificar si hay cambios
Write-Host "`n1. Verificando estado..." -ForegroundColor Cyan
git status

# Agregar cambios
Write-Host "`n2. Agregando cambios..." -ForegroundColor Cyan
git add .

# Ver qué se va a commitear
Write-Host "`n3. Cambios a commitear:" -ForegroundColor Cyan
git status --short

# Hacer commit
Write-Host "`n4. Haciendo commit..." -ForegroundColor Cyan
$commitMessage = "feat: implementar sistema de gestión IP/Puerto desde sesión/cookies y eliminar import innecesario"
git commit -m $commitMessage

# Verificar rama
Write-Host "`n5. Verificando rama actual..." -ForegroundColor Cyan
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Rama actual: $currentBranch" -ForegroundColor Yellow

# Si no está en develop, cambiar
if ($currentBranch -ne "develop") {
    Write-Host "Cambiando a rama develop..." -ForegroundColor Yellow
    git checkout develop
}

# Verificar remote
Write-Host "`n6. Verificando remote..." -ForegroundColor Cyan
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Remote configurado: $remote" -ForegroundColor Green
} else {
    Write-Host "ERROR: No hay remote configurado" -ForegroundColor Red
    Write-Host "Ejecuta: git remote add origin https://github.com/mjfernandez-dev/cormons_controlStock.git" -ForegroundColor Yellow
    exit 1
}

# Hacer push
Write-Host "`n7. Haciendo push a GitHub..." -ForegroundColor Cyan
git push -u origin develop

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Push exitoso ===" -ForegroundColor Green
} else {
    Write-Host "`n=== Error en push ===" -ForegroundColor Red
    Write-Host "Verifica que tengas permisos y que el repositorio exista" -ForegroundColor Yellow
}

