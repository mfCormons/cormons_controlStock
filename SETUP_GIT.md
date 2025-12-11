# Configuración de Git y GitHub

## Pasos para subir el proyecto a GitHub

### 1. Inicializar Git (si no está inicializado)
```bash
git init
```

### 2. Crear rama develop y hacer commit inicial
```bash
# Crear y cambiar a rama develop
git checkout -b develop

# Agregar todos los archivos
git add .

# Hacer commit inicial
git commit -m "Initial commit: Django controlStock app structure"
```

### 3. Crear rama main limpia
```bash
# Crear rama main desde develop (sin commits aún)
git checkout --orphan main

# Eliminar todos los archivos del staging (main queda limpia)
git rm -rf .

# Hacer commit vacío en main
git commit --allow-empty -m "Initial empty commit - main branch"

# Volver a develop para trabajar
git checkout develop
```

### 4. Crear repositorio en GitHub
1. Ve a https://github.com/new
2. Crea un nuevo repositorio (ej: `cormons_controlStock`)
3. **NO inicialices con README, .gitignore o licencia** (ya los tienes)

### 5. Conectar repositorio local con GitHub
```bash
# Agregar remote (reemplaza USERNAME y REPO_NAME con tus datos)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Verificar que se agregó correctamente
git remote -v
```

### 6. Subir rama develop a GitHub
```bash
# Subir develop
git push -u origin develop
```

### 7. Subir rama main (vacía/limpia)
```bash
# Cambiar a main
git checkout main

# Subir main
git push -u origin main

# Volver a develop para seguir trabajando
git checkout develop
```

## Flujo de trabajo recomendado

### Trabajar en develop
```bash
# Siempre trabajar en develop
git checkout develop

# Hacer cambios, commits, etc.
git add .
git commit -m "Descripción de cambios"

# Subir cambios a develop
git push origin develop
```

### Cuando esté listo, mergear a main
```bash
# Asegurarse de estar en develop y tener todo commiteado
git checkout develop
git status

# Cambiar a main
git checkout main

# Mergear develop en main
git merge develop

# Subir main actualizada
git push origin main

# Volver a develop
git checkout develop
```

## Comandos útiles

```bash
# Ver ramas
git branch

# Ver estado
git status

# Ver historial
git log --oneline --graph --all

# Ver diferencias entre ramas
git diff main..develop
```

