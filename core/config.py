"""Configuration dependent on models."""
from copy import deepcopy
from django.conf import settings
from .models import (
    Profile,
    CourseEnrollment,
    ModuleAfterburnerActivity,
    ModuleFlightDeckActivity,
)
from .constants import (
    MODULE_STAGE_SEQUENCE,
    NOTEBOOK_LM_APP_URL,
    DEFAULT_LAUNCH_PAD_TASKS,
)

PROGRAM_LEVELS = [
    {
        "code": Profile.FluencyLevel.BEGINNER,
        "title": "Level 1 · Gather",
        "headline": "Start speaking comfortably with the people beside you.",
        "tagline": "Tiny conversation loops that turn neighbours into practice partners.",
        "details": [
            "Introduce yourself stories guided by community coaches",
            "Everyday phrases broken into listen · repeat · try steps",
            "Weekly check-ins that celebrate the first wins together",
        ],
    },
    {
        "code": Profile.FluencyLevel.ELEMENTARY,
        "title": "Level 2 · Build",
        "headline": "Use English to handle daily life without overthinking.",
        "tagline": "Role-play nights focused on home, work, and city errands.",
        "details": [
            "Scenario circles for shopping, transport, and appointments",
            "Community mentors answering cultural questions in real time",
            "Vocabulary cards you can screenshot and use the same day",
        ],
    },
    {
        "code": Profile.FluencyLevel.INTERMEDIATE,
        "title": "Level 3 · Share",
        "headline": "Explain your ideas clearly at work and in community spaces.",
        "tagline": "Project nights turn presentations into simple story arcs.",
        "details": [
            "Presentation circles with peer notes and applause moments",
            "Simplified grammar refreshers before each practice",
            "Co-created vocabulary banks for meetings and collaboration",
        ],
    },
    {
        "code": Profile.FluencyLevel.UPPER_INTERMEDIATE,
        "title": "Level 4 · Lead",
        "headline": "Guide conversations, facilitate meetings, and support others.",
        "tagline": "Leadership labs focused on facilitation, feedback, and coaching skills.",
        "details": [
            "Facilitation labs with rotating roles and shared agendas",
            "Feedback clinics that model encouraging, useful language",
            "Community mentoring sessions for newer speakers",
        ],
    },
    {
        "code": Profile.FluencyLevel.ADVANCED,
        "title": "Level 5 · Amplify",
        "headline": "Host events, teach others, and build cultural bridges.",
        "tagline": "Showcase sessions and storytelling residencies with community impact.",
        "details": [
            "Weekly community showcase with panels and Q&A",
            "Story studio to design talks, podcasts, or workshops",
            "Collaboration labs with local organisations and schools",
        ],
    },
    {
        "code": Profile.FluencyLevel.PROFICIENT,
        "title": "Level 6 · Legacy",
        "headline": "Grow the movement by mentoring new cohorts and sharing knowledge.",
        "tagline": "Mastery studios that document methods, resources, and collective wins.",
        "details": [
            "Mentor training for hosting neighbour circles",
            "Resource-building sprints for schools and workplaces",
            "Community archive projects capturing shared stories",
        ],
    },
]

PROGRAM_LOOKUP = {level["code"]: level for level in PROGRAM_LEVELS}

AFTERBURNER_CARD_LIBRARY = {
    Profile.FluencyLevel.BEGINNER: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Talk & Record Challenge",
            "description": "Press record. Say the model sentence slowly. Listen. Try again with clear sounds.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Read & Highlight",
            "description": "Read the short text out loud. Underline three new words and say them again.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Use today's phrase in real life. Ask a friend or mirror one easy question.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Snapshot",
            "description": "Watch the quick grammar clip. Write two present simple sentences about you.",
        },
    },
    Profile.FluencyLevel.ELEMENTARY: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Pronunciation Replay",
            "description": "Record yourself at natural speed. Compare stress with the sample and adjust endings.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Guided Reading Burst",
            "description": "Read the article aloud, pausing to note useful collocations and rhythm shifts.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Start a short chat using this week's pattern. Log one win in your NotebookLM notes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Booster",
            "description": "Review the focus tense and craft three personal example sentences with it.",
        },
    },
    Profile.FluencyLevel.INTERMEDIATE: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Voice Precision Lab",
            "description": "Record a 30-second response and analyze rhythm, intonation, and connected speech.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Insight Reading Loop",
            "description": "Annotate the text for tone shifts, then summarize the key evidence aloud.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Apply the scenario in a real or simulated conversation and capture feedback notes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Systems Review",
            "description": "Deconstruct the structure in context and rewrite complex sentences using it.",
        },
    },
    Profile.FluencyLevel.UPPER_INTERMEDIATE: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Delivery Masterclass",
            "description": "Capture a speaking sample focusing on stress, linking, and persuasive cadence.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Critical Reading Pulse",
            "description": "Dissect the article's argument, mark discourse markers, and brief it back.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Lead a live interaction mirroring the week's case study and reflect on outcomes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Structure Upgrade",
            "description": "Integrate the grammar focus into original paragraphs, highlighting register shifts.",
        },
    },
    Profile.FluencyLevel.ADVANCED: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Narrative Delivery Studio",
            "description": "Record a concise story, refine nuance and pacing, and evaluate audience impact.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Analytical Reading Exchange",
            "description": "Interrogate author intent, map advanced lexis, and present a critical response.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Strategy Challenge",
            "description": "Execute a mission-critical conversation and capture insights for a cohort debrief.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Refinement Clinic",
            "description": "Stress-test complex syntax by reshaping examples into formal and informal versions.",
        },
    },
    Profile.FluencyLevel.PROFICIENT: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Executive Delivery Audit",
            "description": "Produce a high-stakes delivery sample, calibrating executive presence and flow.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Scholarly Reading Sprint",
            "description": "Synthesize advanced texts, extract thesis frameworks, and articulate counterpoints.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Impact Challenge",
            "description": "Drive an authentic negotiation or leadership moment and document measured outcomes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Edge Lab",
            "description": "Manipulate nuanced structures across registers, ensuring precision under pressure.",
        },
    },
}

AFTERBURNER_SLOT_SEQUENCE = [
    ModuleAfterburnerActivity.Slot.TALK_RECORD,
    ModuleAfterburnerActivity.Slot.READING,
    ModuleAfterburnerActivity.Slot.REAL_WORLD,
    ModuleAfterburnerActivity.Slot.GRAMMAR,
    ModuleAfterburnerActivity.Slot.GAME,
]

FLIGHT_DECK_SLOT_SEQUENCE = [
    ModuleFlightDeckActivity.Slot.SCHEDULER,
    ModuleFlightDeckActivity.Slot.NOTEBOOK,
    ModuleFlightDeckActivity.Slot.RECORDER,
]

ALLOWED_ENROLLMENT_STATUSES = {
    CourseEnrollment.EnrollmentStatus.ACTIVE,
    CourseEnrollment.EnrollmentStatus.COMPLETED,
}

STAGE_EXTENSION_MAP = {
    "launch-pad": {
        "description": "Warm-Up Circle opens the room. We reconnect, share wins, and learn one clear phrase that anchors the session.",
        "highlights": [
            "Community check-in prompts that spark conversation instantly",
            "Pronunciation and rhythm cues demonstrated by peers and coaches",
            "Visual cards everyone can screenshot and reuse later",
        ],
        "promise": "You always know what we’re focusing on and how it connects to everyday life.",
    },
    "flight-deck": {
        "description": "Practice Room is where we experiment. Partners rotate, prompts shift, and you get real-time feedback without pressure.",
        "highlights": [
            "Paired conversations with live coaching moments",
            "Group reflections capturing what felt easy or tough",
            "Simple grammar and vocabulary nudges woven into dialogue",
        ],
        "promise": "Speaking becomes natural because it happens with friends, not in isolation.",
    },
    "afterburner": {
        "description": "Everyday Replay turns practice into action. We capture clips, outline one real-world step, and celebrate together.",
        "highlights": [
            "Short recordings you can replay or share with family",
            "Community accountability threads for real-world wins",
            "Mini challenges that keep the lesson alive between sessions",
        ],
        "promise": "You leave with a clear next action and people who will cheer when you use it.",
    },
}

LAUNCH_PAD_DEFAULT_TASKS = deepcopy(DEFAULT_LAUNCH_PAD_TASKS)

MEETING_ASSISTANT_URL = getattr(
    settings,
    "MEETING_ASSISTANT_URL",
    "mailto:missioncontrol@foreign.club?subject=Live%20mission%20assist",
)

FLIGHT_DECK_TASKS = [
    {
        "slot": ModuleFlightDeckActivity.Slot.SCHEDULER,
        "title": "Schedule your live mission",
        "subtitle": "Lock your Friday studio slot directly from this page.",
    },
    {
        "slot": ModuleFlightDeckActivity.Slot.NOTEBOOK,
        "title": "Prep your NotebookLM workspace",
        "subtitle": "Spin up a fresh set of notes for this week's mission. Capture vocabulary, new expressions, and personal takeaways inside NotebookLM so you can revisit them later.",
        "url": NOTEBOOK_LM_APP_URL,
        "link_label": "NotebookLM Notes",
    },
    {
        "slot": ModuleFlightDeckActivity.Slot.RECORDER,
        "title": "Get your recorder ready",
        "subtitle": "Capture your live mission for reflection and evidence uploads",
    },
]

PROGRAM_STAGE_DETAILS = [
    {
        **stage,
        **STAGE_EXTENSION_MAP.get(stage["key"], {}),
    }
    for stage in MODULE_STAGE_SEQUENCE
]
