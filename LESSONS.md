# Lessons Learned

Patterns and mistakes to avoid, updated after corrections.

---

## pip

- **Windows keyring blocks pip**: On this machine, pip hangs indefinitely due to the Windows keyring module. Always set `$env:PYTHON_KEYRING_BACKEND="keyring.backends.null.NullKeyring"` before any pip command.
- **Batch installs can hang**: When installing many packages at once, the install can hang during extraction of large packages. Install large packages individually if batch install hangs.

## Path Handling

- **Always convert session_dir to Path**: Functions that accept a path parameter and use the `/` operator must defensively convert to `Path(session_dir)` at the top. Python type hints don't enforce types at runtime, so a string passed to a `Path`-typed parameter silently fails on `/` operations.
- **Pattern**: Add `session_dir = Path(session_dir)` as the first line after the docstring in any public function that takes a path.

## Gradio 6.0

- **theme parameter moved**: In Gradio 6.0+, `theme` must be passed to `app.launch()`, not to `gr.Blocks()`. Passing it to `Blocks()` triggers a UserWarning.

## PyInstaller

- **pathex must use absolute paths**: `Path(".")` or `Path("..")` in `pathex` silently fails to resolve modules. Always use `.resolve()` to get absolute paths, e.g. `Path(".").resolve()`.
- **Frozen-mode path handling**: Two different base paths exist in a frozen .exe:
  - `sys._MEIPASS` — temp extraction dir for **read-only bundled assets** (QSS themes, game_data.json)
  - `Path(sys.executable).resolve().parent` — the .exe's actual directory for **user data** (characters, campaigns, sessions, .env)
- **sys.path manipulation in frozen mode**: Any `sys.path.insert()` calls for dev-mode imports must be wrapped in `if not getattr(sys, "frozen", False):` — otherwise they add nonexistent paths and can cause import failures.
- **Don't exclude unittest**: `scipy → numpy.testing` requires `unittest`. Excluding it crashes the app at startup.
- **Size optimization**: Exclude heavy packages not used at runtime (torch, tensorflow, pandas, boto3, sqlalchemy, numba, matplotlib, Pillow, gradio, uvicorn, opentelemetry, IPython, pytest, setuptools, pip, wheel, tkinter). Reduced .exe from 301MB → 110MB.
