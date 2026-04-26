# Implementation TODOs

#### Documentation:

- Add docs on how to setup credential manually with rc file and env vars
- Add module and function docstrings to the codebase, to explain the purpose and usage of each module and function
- Analyze code and optimize it, e.g. default config entries can be colleted into one central place

#### Improvements

- Also link the comments section of the article if there is one

#### lower priority

- Do a analysis on how robust the code is and add try catch blocks where necessary to handle potential errors and edge cases, such as (you can do a websearch for api docs https://miniflux.app/docs/api.html#endpoint-get-entries and https://pydantic.dev/docs/ai/llms.txt):
  - Handling API errors and rate limits
  - Handling email sending errors
- do an security review of the codebase to identify and fix any potential security vulnerabilities, such as:
  - Handling sensitive information, such as API keys and email credentials, securely and not hardcoding them in the codebase
  - Implementing proper authentication and authorization mechanisms for accessing the tool and its features
  - Document in a security.md file with considerations
- UX: try out different color palettes

### Short-term:

- [ ] check how to optimize tokens. Fetch original content

### Long-term:

- Implement more LLM models provider
- Add additional filtering options, such as keywords, add more articles but as additional entries which only contain the title and link without the summary (or a one sentence summary) at the end.
- Some type of critera and rules for articles to be set to read if they got not picked in the digest, so next time they will excluded

### Out of scope for now but maybe in the future:

- more ai assistant features like:
  - quote of the day, favourite quote
  - weather forecast
  - personal goals and reminders
