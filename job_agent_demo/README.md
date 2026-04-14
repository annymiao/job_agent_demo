# job_agent_demo

<p align="center">
  <img src="./assets/github-preview.svg" alt="job_agent_demo preview" width="1100">
</p>

<p align="center">
  <strong>A GitHub-safe showcase for a private job-search assistant.</strong><br>
  It demonstrates decision quality, not the hidden orchestration layer behind the full system.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-1f3a5f?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-local%20demo-8a5a2b?style=flat&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Data-synthetic-546a7b?style=flat" alt="Synthetic Data">
  <img src="https://img.shields.io/badge/LLM-optional-c8a267?style=flat" alt="Optional LLM">
</p>

`job_agent_demo` is a thin public layer for showing what the product feels like without publishing the parts that matter most internally.

It focuses on three visible outcomes:

- `Job Fit Snapshot`: how well a candidate matches a role
- `Offer Comparison`: which opportunities deserve attention first
- `Interview Prep Brief`: what to prepare before a serious interview

## Why This Exists

Most public demos of job agents either:

- expose too much internal structure
- look generic
- require private user data to make sense

This repo avoids all three.

It uses synthetic sample data, local deterministic logic, and a compact UI that is easy to run, easy to understand, and safe to publish.

## What You Can Show In 30 Seconds

1. Pick a sample candidate.
2. Pick a role.
3. Open the three tabs.
4. Show the fit score, the shortlist ranking, and the interview prep sheet.

That is enough to communicate the product direction without exposing private orchestration, prompts, scraping flows, or application automation.

## Demo Surface

### 1. Job Fit Snapshot

Shows:

- fit score
- strong matches
- primary risks
- positioning guidance
- a compact evidence grid

### 2. Offer Comparison

Shows:

- ranked shortlist
- suggested posture per role
- explicit tradeoff per job

### 3. Interview Prep Brief

Shows:

- likely questions
- strongest stories to tell
- prep focus
- due-diligence questions

## Public Boundary

This repo is intentionally not the full system.

It does **not** publish:

- browser automation
- job-board scraping
- application autofill
- long-term memory loops
- internal prompts or skill catalogs
- multi-agent orchestration

The point is to show visible value, not the private operating system behind it.

## Quick Start

```bash
cd job_agent_demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL, usually:

```text
http://localhost:8501
```

## Optional Live Narrative Polish

The app works without any API configuration.

If you want the optional `Polish This View With Live Model` button, create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Set:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key_here
JOB_AGENT_DEMO_MODEL=gpt-5.4
```

If these values are missing, the app stays in deterministic local mode.

## Repo Structure

```text
job_agent_demo/
├── README.md
├── app.py
├── requirements.txt
├── .env.example
├── assets/
│   ├── github-preview.svg
│   └── gif_storyboard.md
├── demo_core/
│   ├── analysis.py
│   ├── data.py
│   └── llm.py
├── examples/
│   ├── fit_snapshot_example.md
│   ├── offer_comparison_example.md
│   └── interview_prep_example.md
└── sample_data/
    ├── candidates.json
    └── jobs.json
```

## Sample Data

Everything in `sample_data/` is synthetic.

The default bundle includes:

- two fictional candidate profiles
- four fictional roles across applied ML, platform, NLP research, and data science

You can replace them with your own safe examples by editing:

- `sample_data/candidates.json`
- `sample_data/jobs.json`

## Example Outputs

Static examples are included for quick review:

- [Fit Snapshot](./examples/fit_snapshot_example.md)
- [Offer Comparison](./examples/offer_comparison_example.md)
- [Interview Prep Brief](./examples/interview_prep_example.md)

These are useful if you want someone to understand the demo before running it.

## GIF Plan

If you want to turn this into a social-ready GIF later, use the storyboard here:

- [GIF Storyboard](./assets/gif_storyboard.md)

The recommended capture flow is short on purpose:

1. Start on the hero and sidebar.
2. Open `Fit Snapshot`.
3. Switch to `Offer Comparison`.
4. End on `Interview Prep Brief`.

## Troubleshooting

### `streamlit: command not found`

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

### No live model polish

Check:

- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `JOB_AGENT_DEMO_MODEL`

### I only want a fully local demo

Do not create `.env`.

The app still runs with the bundled sample data and local scoring logic.

