# LDS RAG Tool — Overview

## Goal

Add a RAG (Retrieval-Augmented Generation) module to the existing hymns-generator FastAPI app.
The tool lives at `lds.tommasolopiparo.com` alongside the hymns API.

## What it does

A multi-purpose tool for LDS members:

- **Q&A**: Ask a question in natural language → get an answer grounded in LDS sources with citations
- **Search**: Semantic search across scriptures, talks, magazines, and handbook
- **Generate**: Generate content (talks, lesson outlines, etc.) informed by LDS sources

## Audience

Multilingual — Italian and English speakers. The LDS church publishes content in both languages
at `churchofjesuschrist.org/ita/` and `churchofjesuschrist.org/eng/`.

## Sources

| Source | Content | Language priority |
|---|---|---|
| Scriptures (Bible, BoM, D&C, PoGP) | Full canon | Italian + English |
| General Conference talks | Semi-annual conference sessions | Italian + English |
| Liahona magazine | Church magazine articles | Italian + English |
| General Handbook | Leadership manual (all sections) | Italian + English |

## Scope decision

This is a **new module inside the existing repo**, not a separate project.
Reuses existing auth, database infrastructure, deployment, and static page patterns.
