#!/usr/bin/env sh
set -eu

# Use a per-run account so these checks never rely on, reset, or retain a
# shopper account in a developer's database.
export RESPONSIVE_TEST_USERNAME="responsive-checker-$$"
export RESPONSIVE_TEST_PASSWORD="responsive-test-only"

python3 manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_user(username=os.environ['RESPONSIVE_TEST_USERNAME'], email='responsive-checker@example.invalid', password=os.environ['RESPONSIVE_TEST_PASSWORD'], first_name='Responsive')"

cleanup() {
  python3 manage.py shell -c "import os; from django.contrib.auth import get_user_model; get_user_model().objects.filter(username=os.environ['RESPONSIVE_TEST_USERNAME']).delete()" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

./node_modules/.bin/playwright test "$@"
