#!/usr/bin/env bash
# Deploy the current GitHub main branch to the Spaceship Passenger application.
#
# This is intentionally a code-only deployment. The production SQLite database,
# uploads, collected static files, search index, Passenger entry point and logs
# remain on the server and are never copied from Git.

set -Eeuo pipefail

branch="${BRANCH:-main}"
repository="${REPOSITORY:-https://github.com/brownidj/t-shirt_shop.git}"
home_dir="${HOME_DIR:-/home/qtjifjjliu}"
live_dir="${LIVE_DIR:-${home_dir}/django_shop}"
release_dir="${RELEASE_DIR:-${home_dir}/releases/t-shirt_shop}"
venv_dir="${VENV_DIR:-${home_dir}/virtualenv/django_shop/3.13}"

if [[ ! -d "${live_dir}" ]]; then
    echo "Live application directory does not exist: ${live_dir}" >&2
    exit 1
fi

if [[ -d "${release_dir}/.git" ]]; then
    git -C "${release_dir}" fetch --prune origin "${branch}"
    git -C "${release_dir}" reset --hard "origin/${branch}"
else
    mkdir -p "$(dirname "${release_dir}")"
    git clone --branch "${branch}" --single-branch "${repository}" "${release_dir}"
fi

rsync -a \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='*.sqlite3' \
    --exclude='data/' \
    --exclude='media/' \
    --exclude='staticfiles/' \
    --exclude='whoosh_index/' \
    --exclude='tmp/' \
    --exclude='public/' \
    --exclude='passenger_wsgi.py' \
    --exclude='stderr.log' \
    --exclude='topository-shop.zip' \
    "${release_dir}/" "${live_dir}/"

# Use these flags only when the commit being deployed changes dependencies or
# includes a migration. Keeping them opt-in avoids unexpected package or data
# changes during an ordinary template/CSS deployment.
if [[ "${INSTALL_DEPENDENCIES:-0}" == "1" ]]; then
    "${venv_dir}/bin/pip" install -r "${live_dir}/requirements.txt"
fi

if [[ "${RUN_MIGRATIONS:-0}" == "1" ]]; then
    "${venv_dir}/bin/python" "${live_dir}/manage.py" migrate --noinput
fi

"${venv_dir}/bin/python" "${live_dir}/manage.py" collectstatic --noinput
touch "${live_dir}/tmp/restart.txt"

echo "Deployment complete: $(git -C "${release_dir}" rev-parse --short HEAD)"
