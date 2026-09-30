#!/usr/bin/env bash
set -u

snapshot="$SNAPSHOT"
study=/study
source_dir="$study/work/$snapshot"
env_dir="$study/venvs/$snapshot"
mkdir -p "$source_dir" "$study/pytest" "$study/install" "$study/environments" "$study/outcomes"

tar -xf "/source/$snapshot.tar" -C "$source_dir"
python --version >"$study/environments/$snapshot.runtime.txt" 2>&1
python -m pip --version >>"$study/environments/$snapshot.runtime.txt" 2>&1
python -m venv "$env_dir" >"$study/install/$snapshot.venv.log" 2>&1
venv_python="$env_dir/bin/python"

case "$snapshot" in
  httpx-old|httpx-new) install=("$venv_python" -m pip install -r requirements.txt) ;;
  attrs-old) install=("$venv_python" -m pip install -e '.[tests]') ;;
  attrs-new) install=("$venv_python" -m pip install -e '.[tests]') ;;
  pytest-old) install=("$venv_python" -m pip install -e '.[testing]') ;;
  pytest-new) install=("$venv_python" -m pip install -e '.[dev]') ;;
  *) echo "unknown snapshot $snapshot" >&2; exit 2 ;;
esac

set +e
(cd "$source_dir" && "${install[@]}" --disable-pip-version-check) >"$study/install/$snapshot.log" 2>&1
install_rc=$?
set -e

test_rc=null
test_command='python -m pytest -q'
if [ "$install_rc" -eq 0 ]; then
  set +e
  (cd "$source_dir" && "$venv_python" -m pytest -q) >"$study/pytest/$snapshot.log" 2>&1
  test_rc=$?
  set -e
fi

if [ -x "$venv_python" ]; then
  "$venv_python" -m pip freeze --all >"$study/environments/$snapshot.freeze.txt" 2>"$study/environments/$snapshot.freeze.err" || true
fi

printf '{"snapshot":"%s","install_exit":%s,"test_command":"%s","test_exit":%s}\n' \
  "$snapshot" "$install_rc" "$test_command" "$test_rc" >"$study/outcomes/$snapshot.json"
