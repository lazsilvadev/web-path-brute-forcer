#!/usr/bin/env bash
# Setup do ambiente (POSIX shell)
# Executar na raiz do projeto: ./scripts/setup_poetry.sh
set -euo pipefail

echo "1) Verificando Python..."
if ! command -v python >/dev/null 2>&1; then
  echo "Python não encontrado no PATH. Instale Python 3.13+ e tente novamente." >&2
  exit 1
fi

echo "2) Verificando/instalando Poetry (sem pip)..."
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry não encontrado. Instalando via instalador oficial..."
  curl -sSL https://install.python-poetry.org | python3 -
  if [ $? -ne 0 ]; then
    echo "Falha ao instalar o Poetry. Saindo." >&2
    exit 1
  fi
else
  echo "Poetry encontrado, atualizando (self update)..."
  poetry self update || { echo "Falha ao atualizar poetry" >&2; exit 1; }
fi

# Confirma que o comando `poetry` está disponível no PATH após instalação/atualização
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry instalado, mas não disponível no PATH. Reinicie o shell ou adicione o local do Poetry ao PATH e execute o script novamente." >&2
  exit 1
fi

echo "3) Configurando venv in-project e instalando dependências..."
poetry config virtualenvs.in-project true --local
poetry install

# Ativa .venv e executa run.py se possível; caso contrário usa 'poetry run'
if [ -d ".venv" ]; then
  echo ".venv detectada. Tentando ativar e executar run.py..."
  if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . .venv/bin/activate
    python run.py
  elif [ -f ".venv/Scripts/Activate.ps1" ]; then
    echo "Ambiente Windows detectado. Execute .\\.venv\\Scripts\\Activate.ps1 manualmente no PowerShell, ou use 'poetry run'."
    poetry run python run.py
  else
    echo "Script de ativação não encontrado; executando via 'poetry run'..."
    poetry run python run.py
  fi
else
  echo ".venv não encontrada; executando run.py via 'poetry run'..."
  poetry run python run.py
fi

echo "Concluído."

echo "4) Configurando poetry para criar venvs in-project e instalando dependências..."
poetry config virtualenvs.in-project true --local
poetry install

GREEN='\033[0;32'
NC='\033[0m'
echo "Concluído. Ative o venv com: source .venv/bin/activate e rode a aplicação."


