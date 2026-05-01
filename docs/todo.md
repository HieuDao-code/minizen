# Implementation TODOs

#### Improvements

- restructure: instead of getting unread entries, get the last 24h entries, and use that. So that i can still use the rss feed reader and read it.
- Also add more links then N articles, but only show the top N articles with summaries, and the rest as a list of links at the end. This way you can still use the rss feed reader and read it, but also have the option to see more articles in the digest if you want to.
- Show the comments link after the title and the estimated reading time of miniflux api after the title. Both in a smaller font size
- Better how-it-works diagram, make it top to bottom instead of left to right, and make it more visually appealing
- Keep the article summary in the language the article is in

#### lower priority

- Do a analysis on how robust the code is and add try catch blocks where necessary to handle potential errors and edge cases, such as (you can do a websearch for api docs https://miniflux.app/docs/api.html#endpoint-get-entries and https://pydantic.dev/docs/ai/llms.txt):
  - Handling API errors and rate limits
  - Handling email sending errors
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
