#!/usr/bin/env bash
set -u

study=/study
retry=/study/retries
mkdir -p "$retry/work" "$retry/venvs" "$retry/install" "$retry/pytest" "$retry/environments" "$retry/outcomes"

# The first attrs-new run used the venv's Python but omitted venv/bin from PATH.
# pytest-mypy-plugins launches the mypy console script by name, so rerun under the
# PATH tox would provide while keeping the exact installed freeze unchanged.
name=attrs-new
env_dir="$study/venvs/$name"
source_dir="$study/work/$name"
"$env_dir/bin/python" --version >"$retry/environments/$name.runtime.txt" 2>&1
"$env_dir/bin/python" -m pip freeze --all >"$retry/environments/$name.freeze.txt"
set +e
(cd "$source_dir" && PATH="$env_dir/bin:$PATH" "$env_dir/bin/python" -m pytest -q) >"$retry/pytest/$name.log" 2>&1
test_rc=$?
set -e
printf '{"snapshot":"%s","attempt":"PATH-corrected","test_command":"PATH=<venv>/bin python -m pytest -q","test_exit":%s}\n' "$name" "$test_rc" >"$retry/outcomes/$name.json"

for project in old new; do
  name="pytest-$project"
  source_dir="$retry/work/$name"
  env_dir="$retry/venvs/$name"
  mkdir -p "$source_dir"
  tar -xf "/source/$name.tar" -C "$source_dir"
  python -m venv "$env_dir" >"$retry/install/$name.venv.log" 2>&1
  if [ "$project" = old ]; then
    project_version=7.2.0
    extra=testing
  else
    project_version=8.3.4
    extra=dev
  fi
  set +e
  (cd "$source_dir" && SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST="$project_version" \
    "$env_dir/bin/python" -m pip install -e ".[${extra}]" --disable-pip-version-check) >"$retry/install/$name.log" 2>&1
  install_rc=$?
  set -e
  test_rc=null
  if [ "$install_rc" -eq 0 ]; then
    set +e
    (cd "$source_dir" && PATH="$env_dir/bin:$PATH" "$env_dir/bin/python" -m pytest -q) >"$retry/pytest/$name.log" 2>&1
    test_rc=$?
    set -e
  fi
  "$env_dir/bin/python" -m pip freeze --all >"$retry/environments/$name.freeze.txt" 2>"$retry/environments/$name.freeze.err" || true
  printf '{"snapshot":"%s","attempt":"source-version-and-venv-PATH-corrected","install_exit":%s,"test_command":"PATH=<venv>/bin python -m pytest -q","test_exit":%s}\n' "$name" "$install_rc" "$test_rc" >"$retry/outcomes/$name.json"
done
