"""
Metaprogram language pattern detection.

Each metaprogram has weighted keyword/phrase clusters.
Score text against both poles — the stronger signal wins.
Confidence = gap between the two scores. High gap = high confidence.

These patterns come from NLP metaprogram research and real-world
language analysis. They detect unconscious communication patterns
that people don't know they're broadcasting.
"""

# ═══════════════════════════════════════════════════════════════
# METAPROGRAM 1: MOTIVATION DIRECTION — Toward vs Away From
# ═══════════════════════════════════════════════════════════════

TOWARD_PATTERNS = {
    # Strong signals (weight 3)
    "strong": [
        "i want to", "i'm going to", "my goal is", "i'm building",
        "excited about", "looking forward", "can't wait to",
        "working toward", "aiming for", "going for",
        "dream of", "vision for", "plan to", "aspire",
        "achieve", "accomplish", "create", "build", "grow",
        "level up", "upgrade", "improve", "gain", "win",
        "opportunity", "potential", "possibilities",
        "let's go", "bring it on", "here we go",
        "next level", "crushing it", "killing it",
        "making moves", "on fire", "momentum",
    ],
    # Medium signals (weight 2)
    "medium": [
        "want", "hope", "wish for", "love to",
        "get better", "more of", "increase",
        "progress", "advance", "develop",
        "earn", "attract", "launch", "start",
        "new", "fresh", "begin", "open",
    ],
    # Weak signals (weight 1)
    "weak": [
        "good", "great", "awesome", "amazing",
        "yes", "let's", "ready", "can",
        "will", "gonna", "about to",
    ],
}

AWAY_FROM_PATTERNS = {
    "strong": [
        "i need to stop", "tired of", "sick of", "fed up",
        "i can't keep", "have to quit", "done with",
        "avoid", "prevent", "protect", "escape",
        "get rid of", "eliminate", "remove", "cut out",
        "never again", "no more", "enough of",
        "struggling with", "suffering from", "dealing with",
        "worried about", "afraid of", "scared of",
        "overwhelmed", "stressed", "burned out", "exhausted",
        "losing money", "wasting time", "falling behind",
        "can't afford", "running out", "drowning in",
        "fix this", "solve this", "get out of",
    ],
    "medium": [
        "stop", "quit", "end", "leave",
        "less", "reduce", "minimize", "limit",
        "problem", "issue", "pain", "struggle",
        "risk", "danger", "threat", "worry",
        "hate", "dislike", "annoying", "frustrating",
        "broken", "failing", "losing",
    ],
    "weak": [
        "don't want", "not great", "bad",
        "hard", "difficult", "tough",
        "unfortunately", "sadly",
    ],
}

# ═══════════════════════════════════════════════════════════════
# METAPROGRAM 2: FRAME OF REFERENCE — Internal vs External
# ═══════════════════════════════════════════════════════════════

INTERNAL_PATTERNS = {
    "strong": [
        "i decided", "i figured out", "i realized",
        "i believe", "i think", "in my opinion",
        "i know what's best", "i trust my gut",
        "my instinct", "my experience tells me",
        "i don't care what", "doesn't matter what others",
        "i'll do it my way", "i know myself",
        "i feel strongly", "i'm convinced",
        "makes sense to me", "i just know",
        "my philosophy", "my approach", "my method",
        "i've always", "personally i",
    ],
    "medium": [
        "i feel", "i sense", "i prefer",
        "my take", "my view", "my perspective",
        "for me", "in my case", "my choice",
        "independent", "self-taught", "figured it out",
        "own research", "my own", "myself",
    ],
    "weak": [
        "i", "me", "my", "mine",
        "decided", "chose", "picked",
    ],
}

EXTERNAL_PATTERNS = {
    "strong": [
        "what do you think", "what do you guys think",
        "any recommendations", "any suggestions",
        "has anyone tried", "what's everyone using",
        "what do people", "what does everyone",
        "according to", "studies show", "research says",
        "experts say", "they recommend", "best practices",
        "highly rated", "top reviewed", "award winning",
        "everyone's talking about", "trending",
        "my friend said", "someone told me",
        "is this normal", "am i the only one",
        "poll:", "vote:", "which one should i",
    ],
    "medium": [
        "recommend", "suggestion", "advice",
        "review", "rating", "testimonial",
        "popular", "trending", "viral",
        "people say", "they say", "word is",
        "compared to", "vs", "versus",
        "best", "top", "ranked",
    ],
    "weak": [
        "help", "thoughts", "opinions",
        "anyone", "everyone", "people",
    ],
}

# ═══════════════════════════════════════════════════════════════
# METAPROGRAM 3: WORK STYLE — Options vs Procedures
# ═══════════════════════════════════════════════════════════════

OPTIONS_PATTERNS = {
    "strong": [
        "what are my options", "alternatives",
        "different ways", "another approach",
        "flexibility", "it depends", "varies",
        "could go either way", "open to",
        "explore", "experiment", "try different",
        "mix it up", "variety", "diverse",
        "possibilities", "choices", "which one",
        "there's more than one way", "creative",
        "break the rules", "think outside",
        "improvise", "adapt", "pivot",
        "or maybe", "on the other hand",
    ],
    "medium": [
        "option", "choice", "alternative",
        "flexible", "adaptable", "versatile",
        "browse", "explore", "discover",
        "maybe", "perhaps", "possibly",
        "either", "or", "depends",
        "interesting", "curious", "wonder",
    ],
    "weak": [
        "pick", "choose", "select",
        "different", "another", "other",
    ],
}

PROCEDURES_PATTERNS = {
    "strong": [
        "step by step", "step 1", "step 2",
        "just tell me what to do", "give me the steps",
        "what's the right way", "the correct way",
        "follow the process", "the procedure is",
        "first you", "then you", "after that",
        "in order", "sequence", "systematic",
        "the proven method", "the formula",
        "checklist", "to-do list", "action items",
        "how-to", "tutorial", "guide",
        "follow the instructions", "as directed",
        "the proper way", "standard practice",
    ],
    "medium": [
        "step", "process", "method", "system",
        "plan", "schedule", "routine", "structure",
        "organize", "order", "sequence",
        "correct", "proper", "right way",
        "list", "checklist", "instructions",
        "follow", "complete", "finish",
    ],
    "weak": [
        "do", "done", "next", "then",
        "first", "last", "finally",
    ],
}

# ═══════════════════════════════════════════════════════════════
# METAPROGRAM 4 (BONUS): CHUNK SIZE — Big Picture vs Detail
# ═══════════════════════════════════════════════════════════════

BIG_PICTURE_PATTERNS = {
    "strong": [
        "big picture", "overall", "in general",
        "the vision", "the concept", "the idea",
        "essentially", "fundamentally", "at the end of the day",
        "the bottom line", "what matters is",
        "the whole thing", "the full picture",
        "strategy", "long-term", "endgame",
        "the point is", "the takeaway",
    ],
    "medium": [
        "overview", "summary", "tldr", "tl;dr",
        "basically", "simply", "in short",
        "main thing", "key point", "core",
        "framework", "model", "approach",
    ],
    "weak": [
        "about", "roughly", "around",
        "general", "broad", "high level",
    ],
}

DETAIL_PATTERNS = {
    "strong": [
        "specifically", "exactly", "precisely",
        "the details", "let me break it down",
        "here's the breakdown", "granular",
        "word for word", "line by line",
        "in particular", "more specifically",
        "the numbers are", "the data shows",
        "technically", "literally", "actually",
    ],
    "medium": [
        "detail", "specific", "exact",
        "number", "stat", "figure", "data",
        "metric", "measurement", "percentage",
        "analysis", "breakdown", "deep dive",
    ],
    "weak": [
        "how much", "how many", "what exactly",
        "which one", "when exactly",
    ],
}

# ═══════════════════════════════════════════════════════════════
# METAPROGRAM 5 (BONUS): ACTION — Proactive vs Reactive
# ═══════════════════════════════════════════════════════════════

PROACTIVE_PATTERNS = {
    "strong": [
        "i'm going to", "i just did", "already started",
        "took action", "made it happen", "just shipped",
        "launched", "built", "created", "started",
        "let's do this", "no waiting", "right now",
        "taking charge", "making moves", "getting ahead",
        "initiated", "pioneered", "first mover",
    ],
    "medium": [
        "starting", "beginning", "launching",
        "proactive", "initiative", "go-getter",
        "now", "today", "immediately",
        "doing", "making", "building",
    ],
    "weak": [
        "soon", "planning", "about to",
        "will", "going to", "shall",
    ],
}

REACTIVE_PATTERNS = {
    "strong": [
        "waiting for", "once they", "when it happens",
        "if they", "depends on", "need to see",
        "let's wait", "see what happens", "we'll see",
        "responding to", "reacting to", "dealing with",
        "came up", "happened to", "had to",
        "was forced to", "no choice but",
        "after they", "once i hear back",
    ],
    "medium": [
        "waiting", "pending", "hold on",
        "react", "respond", "adapt",
        "when", "if", "once",
        "might", "maybe", "could",
    ],
    "weak": [
        "later", "eventually", "sometime",
        "whenever", "whatever",
    ],
}


# ═══════════════════════════════════════════════════════════════
# ALL METAPROGRAMS REGISTRY
# ═══════════════════════════════════════════════════════════════

METAPROGRAMS = {
    "motivation": {
        "pole_a": {"name": "toward", "patterns": TOWARD_PATTERNS},
        "pole_b": {"name": "away_from", "patterns": AWAY_FROM_PATTERNS},
        "priority": 1,  # Most important — detect first
    },
    "reference": {
        "pole_a": {"name": "internal", "patterns": INTERNAL_PATTERNS},
        "pole_b": {"name": "external", "patterns": EXTERNAL_PATTERNS},
        "priority": 2,
    },
    "work_style": {
        "pole_a": {"name": "options", "patterns": OPTIONS_PATTERNS},
        "pole_b": {"name": "procedures", "patterns": PROCEDURES_PATTERNS},
        "priority": 3,
    },
    "chunk_size": {
        "pole_a": {"name": "big_picture", "patterns": BIG_PICTURE_PATTERNS},
        "pole_b": {"name": "detail", "patterns": DETAIL_PATTERNS},
        "priority": 4,
    },
    "action": {
        "pole_a": {"name": "proactive", "patterns": PROACTIVE_PATTERNS},
        "pole_b": {"name": "reactive", "patterns": REACTIVE_PATTERNS},
        "priority": 5,
    },
}
