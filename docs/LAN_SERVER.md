# Run Topository on a local network

Use these steps to let other machines on the same Wi-Fi or Ethernet network
open the development site. This is suitable for local demos and testing, not
for a public internet-facing deployment.

## 1. Put the project on the server Mac

The simplest approach is to copy the whole `Topository_01` folder to the Mac
that will run the server. This preserves the SQLite database, uploaded product
images, and shirt-preview assets.

If using Git instead, also copy these files and folders from the current Mac:

- `db.sqlite3`
- `media/`
- `static/`

## 2. Install the Python packages

On the server Mac, open Terminal and run:

```bash
cd /path/to/Topository_01
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Find the server Mac's network address

Open **System Settings → Wi-Fi**, click **Details** for the connected network,
and note the IP address. It will usually look like `192.168.1.25`.

## 4. Allow that address in Django

Edit `topository_01/settings.py` on the server Mac. Add the server's IP address
to `ALLOWED_HOSTS`, for example:

```python
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.1.25"]
```

Use the actual address found in step 3. Repeat this change if the server Mac
receives a different IP address from the router later.

## 5. Start the server

With the virtual environment still active, run:

```bash
python manage.py runserver 0.0.0.0:8000
```

`0.0.0.0` tells Django to accept connections from the local network, rather
than only from the server Mac itself.

If macOS asks whether to allow incoming connections for Python, choose
**Allow**.

## 6. Open the site from another machine

On another machine connected to the same network, open:

```text
http://192.168.1.25:8000/
```

Replace `192.168.1.25` with the server Mac's actual IP address.

Keep the Terminal window running while the site is needed. Press `Ctrl+C` in
that Terminal window to stop the server.

## If it does not open

- Confirm both machines are on the same Wi-Fi or Ethernet network.
- Confirm the address in the browser exactly matches the server Mac's IP.
- Confirm `ALLOWED_HOSTS` includes that IP address.
- Allow Python through the macOS firewall, or temporarily turn off the firewall
  only to confirm it is the cause.
- Do not use this development server to expose the shop to the public internet.
