# Backend Code Standards

To maintain technical excellence in Voice2Machine, we follow strict asynchronous development and typing rules.

## 🐍 Modern Python (3.12+)

### Strict Typing

- All functions must have complete Type Hints (arguments and return).
- Use `typing.Protocol` to define interfaces instead of `ABC`.

### AsyncIO and Concurrency

- **Do Not Block the Event Loop**: Never use `time.sleep()` or blocking I/O in `async` functions.
- **Intensive Tasks**: Use `asyncio.to_thread()` for CPU-bound processing (e.g., heavy NumPy calculations) or GPU-bound if the library is not natively asynchronous.

## 📝 Pydantic V2

- Use Pydantic V2 exclusively.
- Prefer `ConfigDict(frozen=True)` for domain entities to ensure data immutability during the processing flow.

## 💬 Comments and Documentation

- Code comments: **Latin American Spanish**.
- Docstrings: Google or NumPy style, preferably in Spanish for consistency with the team.
- Commit messages: **English** (Conventional Commits: `feat:`, `fix:`, `refactor:`).

## 🚨 Error Handling

- Use a custom exception hierarchy based on `ApplicationError`.
- Avoid using generic `try/except` without logging the appropriate context.
