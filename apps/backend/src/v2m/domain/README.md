# domain

The domain layer encapsulates business rules and fundamental definitions of the problem the application solves. This layer should not depend on any external technology (database, web frameworks, etc.).

## Content

- `errors.py` - Domain exception hierarchy representing semantic business errors (e.g., `MicrophoneNotFoundError`, `TranscriptionError`)

## Philosophy

The domain is the heart of the application and should remain pure and infrastructure-agnostic. Changes in external libraries should not affect this directory.
