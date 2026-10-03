# Updating the Spaceship website with Git

This project is deployed from GitHub to the Spaceship-hosted Django application.
The deployment is deliberately **code-only**: it updates application files while
leaving production data and hosting configuration in place.

## How the deployment works

1. Make and test a change on the development Mac.
2. Commit and push the approved change to GitHub's `main` branch.
3. Connect to the Spaceship account by SSH and run the deployment script.
4. The script refreshes a separate Git staging checkout, copies code into the
   live application, collects static files, and signals Passenger to restart.

The live Django application is kept separate from the Git checkout. Do **not**
run `git pull`, `git reset`, or a clone directly inside the live application
directory.

## Normal release procedure

From the project folder on the development Mac:

```bash
git status
python3 manage.py check
git add path/to/the/approved/files
git commit -m "Describe the change"
git push origin main
```

Only stage the files intended for that release. Check `git status` before the
commit, particularly if there are pre-existing staged or untracked files.

Then run the deployment command from the Mac terminal:

```bash
ssh -p <ssh-port> <hosting-user>@<server-ip> \
  /home/<hosting-user>/bin/deploy_spaceship.sh
```

Find the current server address, port, and hosting username in cPanel under
**Manage SSH**. Do not put passwords or private keys in this document, Git, or
the deployment script.

## What the script changes and preserves

The versioned script is [scripts/deploy_spaceship.sh](../scripts/deploy_spaceship.sh).
It maintains a staging checkout in `~/releases/t-shirt_shop`, then synchronises
that checkout into `~/django_shop`.

It never copies over these live resources:

- SQLite databases (`*.sqlite3`)
- `media/` shopper/product uploads
- `staticfiles/` generated static assets
- `data/`, `whoosh_index/`, `tmp/`, `public/`, and logs
- `.env` and `passenger_wsgi.py`

This is essential because the repository currently contains some data files.
Keeping the database and uploads on the server prevents a code release from
discarding live shop data.

## Releases that change packages or the database schema

The usual deployment does not alter installed Python packages or the database.
For a release that changes `requirements.txt`, run:

```bash
ssh -p <ssh-port> <hosting-user>@<server-ip> \
  'INSTALL_DEPENDENCIES=1 /home/<hosting-user>/bin/deploy_spaceship.sh'
```

For a release containing a Django migration, run:

```bash
ssh -p <ssh-port> <hosting-user>@<server-ip> \
  'RUN_MIGRATIONS=1 /home/<hosting-user>/bin/deploy_spaceship.sh'
```

Use both flags when both apply. Review migrations before running them against
production.

## Verification

After each release:

1. Open `https://tshirts.topository.org/` in a private browser window.
2. Check the changed page at desktop and phone/tablet widths.
3. In cPanel's **Setup Python App**, confirm the application is started.
4. If the release fails, check the cPanel/Python application logs before
   attempting another deployment.

## Rollback

Prefer a reversible Git rollback:

```bash
git revert <bad-commit>
git push origin main
```

Then run the normal deployment command. Avoid manually replacing the live
directory or using destructive Git commands there.

## One-time setup already completed

- SSH access is enabled for the hosting account.
- The development Mac's existing SSH key is authorised in cPanel and GitHub.
- The local Git remote uses GitHub SSH authentication.
- The server has the staging checkout and executable deployment script.

