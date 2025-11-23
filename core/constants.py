"""Shared constants for stage configuration."""
from datetime import timedelta

NOTEBOOK_LM_APP_URL = "https://notebooklm.google.com/app"

DEFAULT_LAUNCH_PAD_TASKS = [
    {
        "title": "NotebookLM briefing: theme overview",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
    {
        "title": "Vocabulary pack with pronunciation clips",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
    {
        "title": "Speaking drill: record a 30-second practice",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
    {
        "title": "Micro-quiz to check comprehension",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
    {
        "title": "Cultural insight drop",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
    {
        "title": "Mission reflection prompt",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": NOTEBOOK_LM_APP_URL,
    },
]

MODULE_STAGE_SEQUENCE = [
    {
        "key": "launch-pad",
        "label": "Warm-Up Circle",
        "tagline": "Arrive & Connect",
        "summary": "Open with greetings, check-ins, and one simple phrase we’ll reuse all session long.",
    },
    {
        "key": "flight-deck",
        "label": "Practice Room",
        "tagline": "Try It Together",
        "summary": "Pair up, rotate, and repeat short conversations that mirror everyday life.",
    },
    {
        "key": "afterburner",
        "label": "Everyday Replay",
        "tagline": "Use It Today",
        "summary": "Document key phrases, record a quick reflection, and set a simple real-world action.",
    },
]

for idx, stage in enumerate(MODULE_STAGE_SEQUENCE, start=1):
    stage["order"] = idx

MODULE_STAGE_LOOKUP = {stage["key"]: stage for stage in MODULE_STAGE_SEQUENCE}

PRE_SESSION_TASKS = [task["title"] for task in DEFAULT_LAUNCH_PAD_TASKS]

POST_SESSION_TASKS = [
    "NotebookLM game mission",
    "Spaced repetition review (48h)",
    "Peer feedback exchange",
    "Mini challenge unlocked via app",
    "Signal reminder: next live cue",
    "Evidence upload checkpoint",
]

AFTERBURNER_GAME = {
    "key": "mission-remix",
    "title": "Didactic Game · Mission Remix",
    "description": "A collaborative remix where squads reimagine the week’s mission with new stakes, vocabulary, and constraints.",
}

FLASHCARD_SRS_INTERVALS = [
    timedelta(minutes=1),
    timedelta(minutes=10),
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(days=1),
    timedelta(days=3),
    timedelta(days=7),
    timedelta(days=14),
]
