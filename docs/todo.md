# Implementation TODOs

#### Documentation:

- Add docs on how to setup credential manually with rc file and env vars
- Add module and function docstrings to the codebase, to explain the purpose and usage of each module and function

- Improve the workflow: Make it possible to run the minizen run command without the setup wizard so we do not store credentials locally. Add flags for all option we need for the setup so we can run the command with all necessary information

#### Setup wizard:

- Bug: The setup wizard must also need to write the miniflux part or rather the app need to use the default values if the field miniflux is missing
- Add a setup for openai key as well. When setup wizard is run, ask for llm model first and the ask for the api key. Update all the docs regarding openai key and write specific tests.
- The setup wizard should as for the miniflux api key and anthropic key last
- Set the permission of .env to 600 to prevent unauthorized access to sensitive information

- Also link the comments section of the article if there is one

- Do a analysis on how robust the code is and add try catch blocks where necessary to handle potential errors and edge cases, such as (you can do a websearch for api docs https://miniflux.app/docs/api.html#endpoint-get-entries and https://pydantic.dev/docs/ai/llms.txt):
  - Handling API errors and rate limits
  - Handling email sending errors
- do an security review of the codebase to identify and fix any potential security vulnerabilities, such as:
  - Handling sensitive information, such as API keys and email credentials, securely and not hardcoding them in the codebase
  - Implementing proper authentication and authorization mechanisms for accessing the tool and its features
  - Document in a security.md file with considerations

### Short-term:

- [ ] check how to optimize tokens. Fetch original content

### Long-term:

- Implement more LLM models provider
- Add additional filtering options, such as keywords, add more articles but as additional entries which only contain the title and link without the summary (or a one sentence summary) at the end.

### Out of scope for now but maybe in the future:

- more ai assistant features like:
  - quote of the day, favourite quote
  - weather forecast
  - personal goals and reminders
