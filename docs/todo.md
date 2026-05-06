# Implementation TODOs

#### lower priority

- do an security review of the codebase to identify and fix any potential security vulnerabilities, such as:
  - Handling sensitive information, such as API keys and email credentials, securely and not hardcoding them in the codebase
  - Implementing proper authentication and authorization mechanisms for accessing the tool and its features
  - Document in a security.md file with considerations

### Short-term:

- [ ] Check how to optimize tokens. Fetch original content?
- [ ] Build a ranking + filtering system

### Long-term:

- Implement more LLM models provider
- Add additional filtering options, such as keywords, add more articles but as additional entries which only contain the title and link without the summary (or a one sentence summary) at the end.
- Some type of critera and rules for articles to be set to read if they got not picked in the digest, so next time they will excluded

### Out of scope for now but maybe in the future:

- more ai assistant features like:
  - quote of the day, favourite quote
  - weather forecast
  - personal goals and reminders
