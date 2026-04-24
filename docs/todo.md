# Implementation TODOs

## Packages

- [pydantic](https://github.com/pydantic/pydantic) models
- [miniflux client module](https://github.com/miniflux/python-client)
- [pydantic-ai](https://github.com/pydantic/pydantic-ai), for llms under [llms.txt](https://pydantic.dev/docs/ai/llms.txt)
- minimal email client module with [smtplib](https://docs.python.org/3/library/smtplib.html)

## Considerations

- Keep in mind that I might want to make this an CLI with [typer](https://github.com/fastapi/typer)
- Make this package very modular so that I can replace or extend functionality easily by adding new modules, e.g. replace miniflux with another RSS feed reader, or replace the email client with another one, or replace clause with another LLM provider. The directory structure should reflect this modularity.
- Any secret as environment variables for miniflux, anthropic and email credentials or any better way to manage secrets in a secure way. Secret are:
  - miniflux api key
  - anthropic api key
  - email server, port, username and password

## Miscellaneous

- Add logging to the script for better debugging and monitoring
- Add error handling to manage potential issues with API calls, email sending, etc.
- Write unit tests for the different modules to ensure reliability and maintainability, tox, pytest, ruff and ty are set up for testing and linting
- Add documentation for the package, including usage instructions and examples
- Consider adding a configuration file (e.g. YAML or JSON) to manage settings and credentials more easily, instead of relying solely on environment variables

## How to run it

- Github action which runs the python script (or cli) on a schedule, e.g. every day at 8am
