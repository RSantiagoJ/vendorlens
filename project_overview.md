# VendorLens — AI-Powered Vendor Proposal Analyzer

## Context: Who is building this and why

The developer is Ricardo Santiago, a Full Stack Software Developer and DevOps
Engineer at the UMass President's Office (UMPO) in Westfield, MA. He has strong
professional experience in Node.js, TypeScript, React, Next.js, Python, Java,
CI/CD pipelines, REST APIs, PostgreSQL, and RPA automation using UiPath.

This project is built during an innovation sprint with two goals:

1. Demo to university leadership that solves a real, recognized pain point
2. Portfolio project strong enough to support a career pivot into AI dev roles

Ricardo is new to agentic AI. He understands prompting and MD-driven workflows
but has not yet built multi-agent systems, RAG pipelines, or MCP integrations.
Explain what you are building and why as you go. Suggest improvements openly.
Do not silently deviate from the plan — flag better approaches and explain why.

---

## What VendorLens does

VendorLens automates the vendor proposal evaluation process for the UMass
President's Office. It is grounded in a real procurement the office ran:
the 2025-2026 Enterprise Social Media Posting and Listening Platform RFP
(issued November 6, 2025, proposals due December 1, 2025).

A staff member uploads 2-3 vendor proposal PDFs. VendorLens:

1. Extracts structured contract data from each proposal
2. Flags risks against real UMPO security and procurement policy (SVM-01)
   and the standard UMass Contract for Services terms
3. Scores each vendor against the actual RFP evaluation criteria
4. Writes a professional recommendation memo

The demo uses fictional vendor responses to the real RFP. Leadership will
recognize the RFP immediately — it is their procurement. The tool feels
like something they could use tomorrow, because it is.

---

## Why this is the right demo

The Social Media Platform RFP is the perfect demo anchor because:

- Leadership issued it — they know the criteria, the pain points, the vendors
- It involved multiple campuses and complex evaluation criteria
- The committee used manual scorecards and lengthy review meetings
- VendorLens shows what that process looks like with AI doing the first pass

Demo narrative:
"This is the RFP your committee issued in November 2025. These are three
fictional vendor responses. Watch VendorLens evaluate them against your
actual criteria and policy in 15 seconds."

That is not a hypothetical. That is their work.

---

## Resume description

"Built VendorLens, a multi-agent RAG application using LangGraph and LlamaIndex
with a FastAPI backend, integrating Claude and Gemini Pro across specialized
agents with MCP tool calling, automated rubric scoring grounded in real
procurement policy, and LangSmith observability. Deployed on Railway."

## Keywords covered

- LLM integrations — Claude (Anthropic) + Gemini Pro across agents
- RAG pipeline — LlamaIndex + ChromaDB semantic retrieval
- Agents and agentic workflows — LangGraph multi-agent orchestration
- Tool / function calling — MCP servers
- Prompt strategies — per-agent structured output prompts
- Evals — automated rubric scoring agent
- Observability — LangSmith tracing
- API development — FastAPI
- Deployment — Railway + Vercel, public URLs on resume

---

## Tech stack

- Backend: Python 3.11+ / FastAPI
- Agent orchestration: LangGraph
- RAG: LlamaIndex + ChromaDB
- Models: Claude Sonnet 4.6 (Anthropic) + Gemini Pro (Google)
- Tool protocol: MCP (Model Context Protocol)
- Observability: LangSmith
- Frontend: Next.js + TypeScript + Tailwind CSS
- Deployment: Railway (backend) + Vercel (frontend)

## What success looks like

Demo: Upload 3 dummy vendor PDFs live in front of leadership. Watch the
pipeline run. See three proposal cards with scores and risk flags. Read
the recommendation memo. Someone in the room says "can we use this for real?"

Resume: Public GitHub repo, live Railway URL, bullet point hitting every
AI developer keyword.
