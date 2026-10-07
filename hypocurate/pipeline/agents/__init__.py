"""The agents (PRD Sections 3, 4 and 6; build step 8).

Agents are language models that return text only. They never execute code and never receive
SQL, a database connection or a file path (CLAUDE.md rule 14): each call gets text built from an
access object that the trusted dispatcher bound to one invocation. Code decides; agents advise.

The model-call libraries (DSPy and litellm) are imported only through `libraries.load()`, which
sets their environment first (litellm otherwise reads a `.env` file when it is imported).
"""
