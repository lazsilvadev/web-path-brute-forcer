# Setup do ambiente (PowerShell)
# Executar a partir da raiz do projeto: .\scripts\setup_poetry.ps1

Param()

function ExitIfError($code, $msg) {
    if ($code -ne 0) {
        Write-Error $msg
        exit $code
    }
}

Write-Host "1) Verificando Python..." -ForegroundColor Cyan
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python não encontrado no PATH. Instale o Python 3.13+ e rode novamente."
    exit 1
}

Write-Host "2) Verificando/instalando Poetry (sem pip)..." -ForegroundColor Cyan
$poetryCmd = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryCmd) {
    Write-Host "Poetry não encontrado. Instalando via instalador oficial..." -ForegroundColor Yellow
    try {
        (Invoke-WebRequest -Uri "https://install.python-poetry.org" -UseBasicParsing).Content | python -
        ExitIfError $LASTEXITCODE "Falha ao executar instalador do poetry"
    }
    catch {
        Write-Error "Erro ao baixar/instalar o instalador do poetry: $_"
        exit 1
    }
}
else {
    Write-Host "Poetry encontrado, atualizando (self update)..." -ForegroundColor Yellow
    poetry self update
    ExitIfError $LASTEXITCODE "Falha ao atualizar poetry"
}

# Confirma que o comando `poetry` está disponível no PATH após instalação/atualização
$poetryCmd = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryCmd) {
    Write-Error "Poetry instalado, mas não disponível no PATH. Reinicie o shell ou adicione o local do Poetry ao PATH e execute o script novamente."
    exit 1
}

Write-Host "4) Configurando venv in-project e instalando dependências..." -ForegroundColor Cyan
# Garante que o poetry crie o venv dentro do diretório do projeto
poetry config virtualenvs.in-project true --local
ExitIfError $LASTEXITCODE "Falha ao configurar poetry"

poetry install
ExitIfError $LASTEXITCODE "Falha ao instalar dependências via poetry"

# Tenta ativar o venv criado em .venv e executar run.py
$activatePath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
    Write-Host "Ativando .venv (dot-sourcing Activate.ps1)..." -ForegroundColor Cyan
    try {
        . $activatePath
    }
    catch {
        Write-Warning "Não foi possível ativar o .venv via dot-sourcing: $_. Usando 'poetry run' como fallback."
        poetry run python run.py
        ExitIfError $LASTEXITCODE "Falha ao rodar run.py via poetry"
    }

    # Verifica se o venv foi ativado no shell atual
    if ($env:VIRTUAL_ENV -and (Test-Path (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'))) {
        Write-Host "Ambiente ativado. Executando run.py com o Python do venv..." -ForegroundColor Cyan
        python run.py
        ExitIfError $LASTEXITCODE "Falha ao rodar run.py"
    }
    else {
        Write-Warning "Ambiente não ativado no shell atual. Tentando executar diretamente com .venv\\Scripts\\python.exe..."
        $venvPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
        if (Test-Path $venvPython) {
            & $venvPython run.py
            ExitIfError $LASTEXITCODE "Falha ao rodar run.py com .venv\\Scripts\\python.exe"
        }
        else {
            Write-Host "Fallback final: poetry run python run.py" -ForegroundColor Yellow
            poetry run python run.py
            ExitIfError $LASTEXITCODE "Falha ao rodar run.py via poetry"
        }
    }
}
else {
    Write-Host ".venv não encontrada — executando run.py via 'poetry run'..." -ForegroundColor Yellow
    poetry run python run.py
    ExitIfError $LASTEXITCODE "Falha ao rodar run.py via poetry"
}

Write-Host "Concluído." -ForegroundColor Green
