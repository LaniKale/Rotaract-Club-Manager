# Rotaract Club Management System — UWI Mona

A web system for the Rotaract Club of UWI Mona to manage members, events and meeting attendance.
COMP2140 Software Engineering group project (THUR_5-7_G03), built with Python and Django using the MVC pattern.

## Features

| Feature | What it does |
|---|---|
| A1 Add member | Executives add members; a login is created with a temporary password; duplicate warning; names, email and phone are validated |
| A2 View / search members | Search by first name, surname, faculty and status; results in alphabetical order |
| A3 Remove member | Removed members move to the Removed Members list and can no longer log in; they can be restored |
| A4 Edit member | Every changed field is recorded in the change history with who changed it and their role |
| A5 Record attendance | Start attendance to show a QR code; members scan it, log in once and tap Check in; executives can mark members present or remove a wrong check-in; attendance rate per member |
| A6 Add event | Title, date, start and end time, location, description and an optional flyer; clash warning for overlapping events; calendar and list views; event search |
| A7 Delete events | Select upcoming events, confirm, and they move to the Removed Events list |

Also: membership applications from a public Join page, a Roles screen where the President decides what each role can do, and email logins for every member.

## MVC structure

| Part | Where |
|---|---|
| Model | `members/models.py`, `events/models.py`, `attendance/models.py` |
| Controller | `members/views/`, `events/views/`, `attendance/views.py` (one module per feature), plus each app's `urls.py` and `forms.py` |
| View | `templates/` |

## Setup

Requires **Python 3.12 or newer**.

**Mac / Linux**
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

**Windows (PowerShell)**
```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in with your email.

## Demo logins

`seed_demo` loads demo members, events, meetings and attendance. Password for every demo login: `rotaract123`.

| Email | Role | Can do |
|---|---|---|
| kayla.brown@example.com | President | Everything, including the Roles screen |
| jordan.campbell@example.com | Secretary | Members, password resets, applications, events, meetings, attendance |
| rushane.williams@example.com | Treasurer | Events, meetings and attendance |
| tianna.reid@example.com | Member | View events, check in at meetings, see their own attendance |

## Roles and logins

- Every member has a login (their email). A temporary password is shown once when they are added; they choose their own on first login.
- Roles are managed on the **Roles** screen by anyone whose role can manage roles (the President by default). Each role is a set of plain-language permissions, e.g. "Add and edit member records" or "Reset member passwords".
- Forgotten passwords: a role with "Reset member passwords" (President and Secretary by default) opens the member's record and clicks **Reset password**.
- The starting roles are created by `python manage.py setup_roles`, which `seed_demo` also runs.

## Testing QR check-in on a phone

1. Run `python manage.py runserver 0.0.0.0:8000`.
2. Find the computer's IP address (Mac: `ipconfig getifaddr en0`; Windows: `ipconfig`, "IPv4 Address").
3. Open `http://YOUR-IP:8000` on the computer (not 127.0.0.1), start attendance for a meeting, and scan the QR code with a phone on the same network.

## Notes

- Uploaded event flyers are saved in `media/`, which is not committed to git.
- For the Django admin at `/admin/`, create an account with `python manage.py createsuperuser`.
- After changing a model, run `python manage.py makemigrations` and commit the new migration file.
- For deployment, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS` are read from the server's environment.
