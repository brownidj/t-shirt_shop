const { execFileSync } = require("node:child_process");

const username = `responsive-checker-${process.pid}-${Date.now()}`;
const password = "responsive-test-only";

function manage(command) {
  execFileSync("python3", ["manage.py", "shell", "-c", command], {
    stdio: "inherit",
    env: process.env,
  });
}

module.exports = async function globalSetup() {
  // Live smoke checks must not create accounts on the production site.
  if (process.env.BASE_URL) {
    return;
  }

  process.env.RESPONSIVE_TEST_USERNAME = username;
  process.env.RESPONSIVE_TEST_PASSWORD = password;
  manage(
    "import os; from django.contrib.auth import get_user_model; " +
      "get_user_model().objects.create_user(username=os.environ['RESPONSIVE_TEST_USERNAME'], " +
      "email='responsive-checker@example.invalid', password=os.environ['RESPONSIVE_TEST_PASSWORD'], " +
      "first_name='Responsive')"
  );

  return async () => {
    manage(
      "import os; from django.contrib.auth import get_user_model; " +
        "get_user_model().objects.filter(username=os.environ['RESPONSIVE_TEST_USERNAME']).delete()"
    );
  };
};
