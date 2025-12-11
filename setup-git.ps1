# Script para configurar Git y GitHub
# Ejecutar: .\setup-git.ps1

Write-Host "=== Configuración de Git para controlStock ===" -ForegroundColor Green

# Verificar si git está instalado
try {
    $gitVersion = git --version
    Write-Host "Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git no está instalado" -ForegroundColor Red
    exit 1
}

# Verificar si ya existe .git
if (Test-Path .git) {
    Write-Host "Repositorio Git ya inicializado" -ForegroundColor Yellow
    $continue = Read-Host "¿Continuar de todos modos? (s/n)"
    if ($continue -ne "s") {
        exit 0
    }
} else {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Cyan
    git init
}

# Crear rama develop
Write-Host "`nCreando rama develop..." -ForegroundColor Cyan
git checkout -b develop 2>$null

# Agregar archivos
Write-Host "Agregando archivos..." -ForegroundColor Cyan
git add .

# Hacer commit inicial
Write-Host "Haciendo commit inicial..." -ForegroundColor Cyan
git commit -m "Initial commit: Django controlStock app structure"

# Crear rama main limpia
Write-Host "`nCreando rama main limpia..." -ForegroundColor Cyan
git checkout --orphan main
git rm -rf . 2>$null
git commit --allow-empty -m "Initial empty commit - main branch"

# Volver a develop
Write-Host "Volviendo a rama develop..." -ForegroundColor Cyan
git checkout develop

Write-Host "`n=== Configuración local completada ===" -ForegroundColor Green
Write-Host "`nPróximos pasos:" -ForegroundColor Yellow
Write-Host "1. Crea el repositorio en GitHub (sin inicializar con README)"
Write-Host "2. Ejecuta estos comandos (reemplaza USERNAME y REPO_NAME):"
Write-Host "   git remote add origin https://github.com/USERNAME/REPO_NAME.git"
Write-Host "   git push -u origin develop"
Write-Host "   git checkout main"
Write-Host "   git push -u origin main"
Write-Host "   git checkout develop"
Write-Host "`nVer ramas actuales:" -ForegroundColor Cyan
git branch

