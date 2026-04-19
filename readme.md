1. the speciality is kept as an optional field and only populated if the role == DOCTOR
2. to run the code `uv run -m fastapi dev app/main.py`
3. run the seed `uv run python -m app.scripts.seed`


```
Clinic MS
├─ .python-version
├─ app
│  ├─ api
│  │  └─ v1
│  │     ├─ dependencies.py
│  │     ├─ endpoints
│  │     │  ├─ appointments.py
│  │     │  ├─ auth.py
│  │     │  └─ users.py
│  │     └─ router.py
│  ├─ core
│  │  ├─ auth.py
│  │  └─ config.py
│  ├─ db
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ models
│  │  ├─ appointment.py
│  │  ├─ patient.py
│  │  ├─ settings.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ schemas
│  │  ├─ appointment.py
│  │  ├─ auth.py
│  │  ├─ patient.py
│  │  ├─ settings.py
│  │  └─ user.py
│  └─ scripts
│     └─ seed.py
├─ data
│  └─ clinic.db
├─ errors.md
├─ extras
│  ├─ Database Tables.drawio
│  ├─ Database Tables.png
│  └─ Demo Project.pdf
├─ main.py
├─ notes.md
├─ pyproject.toml
├─ readme.md
└─ uv.lock

```

* change the current use display_id and remove the calculation of the display_id for the endpoint( for user, appointment, doctor)
"""
from sqlalchemy import Identity

display_id: int = Field(
    sa_column=Column(
        Integer,
        Identity(start=1, cycle=False),
        nullable=False,
        unique=True,
        index=True,
    )
)
"""