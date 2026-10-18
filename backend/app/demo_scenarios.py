"""Deterministic, presentation-ready fixtures used only in LOCAL_DEMO_MODE."""
from __future__ import annotations


DEMO_SCENARIOS = {
    ("learn gen ai", "beginner"): {
        "title": "Learn Gen AI",
        "lessons": [
            ("Generative AI foundations", "Understand what generative models do and where they are useful."),
            ("How neural networks learn", "Build intuition for the technology behind modern generative models."),
            ("From concepts to use cases", "Identify realistic Gen AI opportunities and responsible next steps."),
        ],
        "videos": [
            {"video_id": "G2fqAlgmoPo", "title": "Introduction to Generative AI", "channel": "Google Cloud Tech", "thumbnail": "https://i.ytimg.com/vi/G2fqAlgmoPo/mqdefault.jpg", "duration": "PT22M", "url": "https://www.youtube.com/watch?v=G2fqAlgmoPo"},
            {"video_id": "aircAruvnKk", "title": "But what is a neural network?", "channel": "3Blue1Brown", "thumbnail": "https://i.ytimg.com/vi/aircAruvnKk/mqdefault.jpg", "duration": "PT19M", "url": "https://www.youtube.com/watch?v=aircAruvnKk"},
            {"video_id": "dDD3sUHAcm0", "title": "Google Cloud's approach to generative AI", "channel": "Google Cloud Tech", "thumbnail": "https://i.ytimg.com/vi/dDD3sUHAcm0/mqdefault.jpg", "duration": "PT11M", "url": "https://www.youtube.com/watch?v=dDD3sUHAcm0"},
        ],
    },
    ("learn guitar", "intermediate"): {
        "title": "Learn Guitar",
        "lessons": [
            ("Audit your intermediate foundation", "Identify the technique and theory skills to strengthen first."),
            ("Scale fluency and phrasing", "Turn scale knowledge into expressive, musical phrases."),
            ("A practice system that compounds", "Design a consistent practice loop with measurable progress."),
        ],
        "videos": [
            {"video_id": "r8S0sNavJC4", "title": "Intermediate Method — Foundation Revision", "channel": "JustinGuitar", "thumbnail": "https://i.ytimg.com/vi/r8S0sNavJC4/mqdefault.jpg", "duration": "PT14M", "url": "https://www.youtube.com/watch?v=r8S0sNavJC4"},
            {"video_id": "Sk0Ck5v55x4", "title": "Are You a Beginner or Intermediate Guitar Player?", "channel": "Marty Music", "thumbnail": "https://i.ytimg.com/vi/Sk0Ck5v55x4/mqdefault.jpg", "duration": "PT18M", "url": "https://www.youtube.com/watch?v=Sk0Ck5v55x4"},
            {"video_id": "r8S0sNavJC4", "title": "Intermediate Method — Foundation Revision", "channel": "JustinGuitar", "thumbnail": "https://i.ytimg.com/vi/r8S0sNavJC4/mqdefault.jpg", "duration": "PT14M", "url": "https://www.youtube.com/watch?v=r8S0sNavJC4"},
        ],
    },
    ("learn sfmc", "advanced"): {
        "title": "Learn SFMC",
        "lessons": [
            ("Personalization architecture", "Connect profiles, segmentation, and catalog data into a practical architecture."),
            ("Real-time decisioning", "Design campaigns that use behavioral signals for one-to-one experiences."),
            ("Measurement and optimization", "Use reporting and experiments to improve personalization outcomes."),
        ],
        "videos": [
            {"video_id": "pBip4txgqBw", "title": "Navigate the Platform | Marketing Cloud Personalization", "channel": "Salesforce Support", "thumbnail": "https://i.ytimg.com/vi/pBip4txgqBw/mqdefault.jpg", "duration": "PT13M", "url": "https://www.youtube.com/watch?v=pBip4txgqBw"},
            {"video_id": "gAOxXN-oJVo", "title": "Salesforce Marketing Cloud Personalization Demo", "channel": "Salesforce Product Center", "thumbnail": "https://i.ytimg.com/vi/gAOxXN-oJVo/mqdefault.jpg", "duration": "PT14M", "url": "https://www.youtube.com/watch?v=gAOxXN-oJVo"},
            {"video_id": "pBip4txgqBw", "title": "Navigate the Platform | Marketing Cloud Personalization", "channel": "Salesforce Support", "thumbnail": "https://i.ytimg.com/vi/pBip4txgqBw/mqdefault.jpg", "duration": "PT13M", "url": "https://www.youtube.com/watch?v=pBip4txgqBw"},
        ],
    },
}


def scenario_for(topic: str, level: str) -> dict | None:
    return DEMO_SCENARIOS.get((" ".join(topic.lower().split()), level.lower()))
