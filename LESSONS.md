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
