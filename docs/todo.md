# Implementation TODOs

- Add more Documentation:
  - Fill out the Homepage with more details about the tool, its features, and how it can be used
  - Add more examples of how to use the library
  - Go over the documentation at improve it:
    - of which model we support, what keys you need (e.g. OpenAI, Anthropic)
    - be more concise about the email setup, it doesnt have to be gmail, just an SMTP server, but we can provide instructions for Gmail as its the most common one
  - Will out the How it works section with a diagram and more details about the architecture of the tool
  - Add a FAQ section to the documentation to answer common questions and troubleshoot common issues

- improve UX of the mail. I don't like the colors, I like the Claude, niri wm colors
- UI framework to test with a mock response from the LLM, to test the UI without having to make actual API calls
- print the result in digest fetch and digest preview or pipe it into stdout, so that it can be used in a terminal or in a script
- Also link the comments section of the article if there is one
- Create a test with a real response from the RSS feed, to make sure everything works as expected
- Create a test with a real response from the LLM, to make sure everything works as expected
- Create a test with a real email, to make sure everything works as expected

- Long-term:
  - Do a research of what the best model is to use with API key and free tier, or a cheap
  - Implement more LLM models provider
