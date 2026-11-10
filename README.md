# Gravity Lab

A browser-based N-body gravity simulator. A Python/FastAPI service advances the
simulation and reports physical diagnostics; a Next.js/TypeScript frontend draws
the moving bodies on a canvas.

The original Pygame scripts under `sim_files/` are retained as a reference; the
new web app does not depend on them.

## Run locally

From the project directory, start the API in one terminal:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend expects the
API at `http://127.0.0.1:8000`; set `NEXT_PUBLIC_API_URL` to override it.

## API

- `GET /api/health` checks that the simulation service is available.
- `POST /api/simulate` advances the submitted body states and returns updated
  states, elapsed simulation time, and energy/momentum diagnostics.

Each request is independent, so multiple browser sessions do not share
simulation state. Input bounds cap body count, timestep, and steps per request.
Set `GRAVITY_CORS_ORIGINS` to a comma-separated origin list when deploying.

## Test

```powershell
python -m unittest discover -s backend -t . -v
```
