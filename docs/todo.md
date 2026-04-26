# Implementation TODOs

- Add more Documentation:
  - Fill out the Homepage with more details about the tool, its features, and how it can be used
  - Add more examples of how to use the library
  - Go over the documentation at improve it:
    - of which model we support, what keys you need (e.g. OpenAI, Anthropic)
    - be more concise about the email setup, it doesnt have to be gmail, just an SMTP server, but we can provide instructions for Gmail as its the most common one
  - Will out the How it works section with a diagram and more details about the architecture of the tool. For that you can use mermaid.js to create a diagram and embed it in the documentation. Make sure the zensical plugin is enabled and workinghttps://mermaid.ai/docs/
  - Add a FAQ section to the documentation to answer common questions and troubleshoot common issues
  - Add an AI Disclaimer to the documentation, to inform that this tool is powered by AI and developed with the help of AI (Claude Code)
  - Add a develop section to the documentation, which just have the packages we use and a brief description of it with a link to their documentation

- [ ] minizen as third party package allow, `from minizen import ...` for all the main functions and classes, so that it can be easily imported and used in other projects, such as a terminal script or a web app
- [ ] document it for it
- Add module and function docstrings to the codebase, to explain the purpose and usage of each module and function

- UI framework to test with a mock response from the LLM, to test the UI without having to make actual API calls
- Print the result in digest fetch and digest preview or pipe it into stdout, so that it can be used in a terminal or in a script
- Also link the comments section of the article if there is one
- Do a analysis on how robust the code is and add try catch blocks where necessary to handle potential errors and edge cases, such as (you can do a websearch for api docs https://miniflux.app/docs/api.html#endpoint-get-entries and https://pydantic.dev/docs/ai/llms.txt):
  - Handling API errors and rate limits
  - Handling email sending errors
  - Handling invalid input from the user

### Short-term:

- [ ] check how to optimize tokens. Fetch original content

### Long-term:

- Implement more LLM models provider
- Add additional filtering options, such as keywords, add more articles but as additional entries which only contain the title and link without the summary (or a one sentece summary) at the end.

### Out of scope for now but maybe in the future:

- more ai assistant features like:
  - quote of the day, favourite quote
  - weather forecast
  - personal goals and reminders
