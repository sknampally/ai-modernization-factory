# Configuration

```toml
[evidence.language]
enabled = false

[evidence.language.providers]
auto_detect = true
fail_fast = false
precedence = [
  "language.python.core",
  "language.java.core",
  "language.javascript.core",
]

[evidence.language.python]
enabled = true

[evidence.language.java]
enabled = true

[evidence.language.javascript]
enabled = true
```

The pipeline remains disabled by default. Architecture rules continue through
the legacy compatibility path unless explicitly enabled.
