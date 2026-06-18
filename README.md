# AnchorWorks

**Local evidence engine for trusted answers from provided data.**

AnchorWorks was built around one problem: **trust**.

Modern AI can sound confident while losing track of where an answer came from. In serious work — legal, medical, insurance, engineering, education, security, research — that is not good enough. An answer should be tied to the data that supports it, and the system should be able to say when the provided data is not enough.

AnchorWorks is designed to do the part a language model should not own:

* admit local data into a bounded dataset scope
* build dataset-local counts and lexical values
* map answers back to source coordinates
* select evidence before wording
* manage citations and provenance
* refuse unsupported answers
* keep reviewer/customer data out of lifetime memory unless explicitly promoted

A language model is optional. AnchorWorks can run without one. When a model is used, it is treated as a wording layer, not the authority.

## What it is

AnchorWorks is a small local system that turns provided data into a source-grounded evidence surface.

You provide the data. AnchorWorks builds the local structure. Questions are answered only from the admitted dataset, with receipts.

## What it is not

AnchorWorks is not a chatbot pretending to know everything.

It does not use public internet knowledge as hidden truth. It does not scrape third-party review data into permanent memory. It does not let a model invent citations.

## Why this matters

Most AI systems optimize for fluent answers. AnchorWorks optimizes for bounded answers:

**What data was provided?**
**Where did this answer come from?**
**What evidence supports it?**
**What should be refused?**
**What stays local?**

## Current demo focus

The public demo is intended for review and evaluation. Reviewers can run AnchorWorks against their own local data using dataset-local storage.

Generated outputs are facsimile review outputs, not legal, medical, financial, scientific, or evidentiary authority. Always verify against the cited source coordinates.

## Data boundary

RAG counts belong to the dataset.
Dataset lexical values belong to the dataset.
User lifetime memory is separate.
Nothing crosses scopes without explicit promotion.

## License

This repository is publicly visible for review and demonstration under a strict license.

Unauthorized commercial use, redistribution, hosted service use, model training, scraping, or derivative products are prohibited without written permission from Lee Mercey / Cortex Evolved Systems.
