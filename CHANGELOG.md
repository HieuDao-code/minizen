## 0.6.2 (2026-08-21)

### Fix

- **deps**: upgrade pydantic-ai to 2.33.0 for anthropic 1.0 (#32)

## 0.6.1 (2026-08-14)

### Fix

- shorter digest (#31)

## 0.6.0 (2026-07-25)

### Feat

- **ai**: same-event story clustering in the digest (#29)
- **deps**: update all deps

### Fix

- **setup**: secure env file

## 0.5.0 (2026-05-12)

### Feat

- align more to read list (#24)

## 0.4.0 (2026-05-07)

### Feat

- add preferred_categories to AI config for category-based article ranking (#23)
- retry on transient failure with exponential backoff (#22)
- add interest profile for AI article curation (#20)
- structured error handling with MinizenError hierarchy (#18)

### Fix

- add some security checks (#19)

## 0.3.0 (2026-05-05)

### Feat

- add max_words_per_article to limit token usage (#14)
- query last 24h articles, do no set them to read status (#12)

### Fix

- **deps**: update all dependencies (#13)

### Refactor

- add all the ruff rules! (#9)

## 0.2.0 (2026-04-28)

### Feat

- better ux (#8)

### Refactor

- docs improvement (#7)

## 0.1.0 (2026-04-26)

### Feat

- add first version of minizen (#3)

### Fix

- bug with config file and default values (#4)
