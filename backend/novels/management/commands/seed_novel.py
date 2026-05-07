"""Seed the educational visual novel 'City Moves: A Fresh Start'.

Usage:
    python manage.py seed_novel

Creates:
  - All core Achievement records
  - The novel 'City Moves: A Fresh Start' with scenario JSON
  - 20 VocabularyWord entries linked to the novel
  - A Chapter 1 Quiz with 8 questions
  - Cover image placeholder URL stored in description meta

Safe to re-run: existing records are updated, not duplicated.
"""

from __future__ import annotations

import json

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from novels.models import (
    Achievement,
    Novel,
    Quiz,
    QuizChoice,
    QuizQuestion,
    VocabularyWord,
)

NOVEL_TITLE = "City Moves: A Fresh Start"

# ---------------------------------------------------------------------------
# Scenario builder helpers
# ---------------------------------------------------------------------------

def _say(id_, char, text, bg=None, next_=None, pos="center", music=None):
    n = {"id": id_, "type": "say", "text": text}
    if char:
        n["character"] = char
    if bg:
        n["background"] = bg
    if next_:
        n["next"] = next_
    if pos != "center":
        n["position"] = pos
    if music:
        n["music"] = music
    return n


def _set(id_, vars_dict, next_):
    return {"id": id_, "type": "set", "vars": vars_dict, "next": next_}


def _jump(id_, next_):
    return {"id": id_, "type": "jump", "next": next_}


def _if(id_, var, equals, then_, else_):
    return {"id": id_, "type": "if", "var": var, "equals": equals, "then": then_, "else": else_}


def _choice(id_, prompt, choices, bg=None):
    n = {"id": id_, "type": "choice", "prompt": prompt, "choices": choices}
    if bg:
        n["background"] = bg
    return n


def _end(id_):
    return {"id": id_, "type": "end"}


def _ch(text, next_, set_=None):
    c = {"text": text, "next": next_}
    if set_:
        c["set"] = set_
    return c


# ---------------------------------------------------------------------------
# Scenario definition
# ---------------------------------------------------------------------------

def build_scenario():
    # Nodes reference backgrounds by key; assets.backgrounds maps keys to image URLs
    BG = {k: k for k in ["city", "apt", "cafe", "tube", "nexus", "rest", "night"]}
    EMMA_IMG  = "https://api.dicebear.com/7.x/avataaars/png?seed=EmmaWalsh&size=512&backgroundColor=b6e3f4"
    JAKE_IMG  = "https://api.dicebear.com/7.x/avataaars/png?seed=JakeOliver&size=512&backgroundColor=c0aede"
    PRIYA_IMG = "https://api.dicebear.com/7.x/avataaars/png?seed=PriyaSingh&size=512&backgroundColor=d1f4d1"

    nodes = [
        # ----------------------------------------------------------------
        # ACT 1 — ARRIVAL & APARTMENT
        # ----------------------------------------------------------------
        _say("n_intro", "narrator",
             "The train pulls into Liverpool Street Station and London swallows you whole. "
             "Noise, people, the sharp smell of coffee and rain. You've been dreaming of this moment for three years.",
             BG["city"], "n_intro2"),

        _say("n_intro2", "narrator",
             "You graduated last summer and spent months sending out applications. "
             "Then, out of nowhere, an email arrived: Nexus Tech, a fast-growing startup in Shoreditch, "
             "wanted to meet you. That was three weeks ago. Today is your interview.",
             BG["city"], "n_defaults"),

        _set("n_defaults",
             {"_int_style": "standard", "_lunch": "none", "_asked": "silent", "_dinner": "none"},
             "n_phone_ring"),

        _say("n_phone_ring", "narrator",
             "Your phone buzzes as you drag your suitcase out of the station.",
             BG["city"], "n_emma_call"),

        _say("n_emma_call", "emma",
             "Hi — is this Alex? This is Emma Walsh, HR Manager at Nexus. I'm calling to confirm "
             "your interview tomorrow at 10 AM. Does that still work for you?",
             BG["city"], "n_c1_phone"),

        # CHOICE 1 ─ how you respond to Emma
        _choice("n_c1_phone",
                "How do you respond?",
                [
                    _ch("\"Absolutely. I'll be there at 10 sharp. Thank you for confirming.\"",
                        "n_s1_formal", {"_int_style": "formal"}),
                    _ch("\"Yes! Thanks so much — really looking forward to it.\"",
                        "n_s1_casual", {"_int_style": "casual"}),
                    _ch("\"Actually, would it be possible to come in at 10:30 instead?\"",
                        "n_s1_rescheduled", {"_int_style": "formal"}),
                ],
                BG["city"]),

        _say("n_s1_formal", "emma",
             "Wonderful. Please check in at reception when you arrive. Looking forward to meeting you.",
             BG["city"], "n_apt_arrive"),

        _say("n_s1_casual", "emma",
             "Great! We're really looking forward to it too. See you tomorrow at 10!",
             BG["city"], "n_apt_arrive"),

        _say("n_s1_rescheduled", "emma",
             "Of course — 10:30 it is. Flexibility is something we value here. See you then!",
             BG["city"], "n_apt_arrive"),

        _say("n_apt_arrive", "narrator",
             "You hang up and find your way to the studio flat you rented online. "
             "The estate agent called it 'bijou'. It is, in fact, the size of a large wardrobe. "
             "But it has a window that looks out onto a brick wall, and it's yours.",
             BG["apt"], "n_apt_level_if"),

        # Level-adaptive node: how Alex processes the moment
        _if("n_apt_level_if", "_level", "B1", "n_apt_b1", "n_apt_b2_check"),
        _if("n_apt_b2_check", "_level", "C1", "n_apt_c1", "n_apt_b2"),

        _say("n_apt_b1", "narrator",
             "You need to prepare for tomorrow. You open your laptop and search for information about Nexus. "
             "You want to know what the company does and what questions they might ask.",
             BG["apt"], "n_apt_settle"),

        _say("n_apt_b2", "narrator",
             "Time to do some research. You ought to brush up on Nexus's recent projects, "
             "get familiar with their product, and think through the likely interview questions. "
             "You settle cross-legged on the bed with your laptop.",
             BG["apt"], "n_apt_settle"),

        _say("n_apt_c1", "narrator",
             "The prudent course of action would be to thoroughly acquaint yourself with Nexus's "
             "recent commercial ventures, anticipate the full gamut of interview questions, "
             "and mentally rehearse responses that strike the ideal balance between self-assurance and humility.",
             BG["apt"], "n_apt_settle"),

        _say("n_apt_settle", "narrator",
             "You prepare until midnight, then force yourself to sleep. Tomorrow matters.",
             BG["apt"], "n_cp1"),

        # ----------------------------------------------------------------
        # CHECKPOINT 1 — Interview morning
        # ----------------------------------------------------------------
        _set("n_cp1", {"_chapter": "interview"}, "n_morning"),

        _say("n_morning", "narrator",
             "7:30 AM. The alarm cuts through the silence. Interview day.",
             BG["apt"], "n_outfit"),

        _say("n_outfit", "narrator",
             "You shower, press your shirt, and spend ten minutes debating whether your shoes are "
             "'professional' or 'trying too hard'. You go with the shoes. You leave an hour early.",
             BG["apt"], "n_cafe_arrive"),

        _say("n_cafe_arrive", "narrator",
             "There's a coffee shop near Old Street tube — Fix 126, a small independent place. "
             "The kind of café that has handwritten menus and smells aggressively of good espresso. "
             "You push open the door.",
             BG["cafe"], "n_c2_cafe"),

        # CHOICE 2 ─ coffee order
        _choice("n_c2_cafe",
                "What do you order?",
                [
                    _ch("\"A flat white, please.\"",   "n_s2_coffee", {"_drink": "coffee"}),
                    _ch("\"English breakfast tea, please.\"", "n_s2_tea", {"_drink": "tea"}),
                ],
                BG["cafe"]),

        _say("n_s2_coffee", "narrator",
             "The barista nods approvingly. Your flat white arrives in a small ceramic cup. "
             "You wrap your hands around it and run through your talking points one last time.",
             BG["cafe"], "n_tube_commute"),

        _say("n_s2_tea", "narrator",
             "The barista smiles. 'Sensible choice.' Your tea arrives in a proper pot with a tiny jug of milk. "
             "Very London. You sip it slowly and go over your notes.",
             BG["cafe"], "n_tube_commute"),

        _say("n_tube_commute", "narrator",
             "The Central line is heaving, but you find a spot near the door. "
             "People scroll phones, read free newspapers, stare at the middle distance. "
             "Classic London. You put in one earbud and breathe.",
             BG["tube"], "n_arrive_nexus"),

        _say("n_arrive_nexus", "narrator",
             "Old Street. You step out into crisp morning sunshine. Nexus occupies a converted warehouse — "
             "exposed brick, enormous windows, a discreet sign by the door that reads 'NEXUS' in sans-serif. "
             "It looks like every startup ever photographed for a magazine cover.",
             BG["nexus"], "n_reception_greet"),

        _say("n_reception_greet", "emma",
             "Alex! Welcome — I'm Emma. Great to finally put a face to the name. "
             "How was your journey over? The Central line can be brutal in the mornings.",
             BG["nexus"], "n_small_talk"),

        _say("n_small_talk", "narrator",
             "You chat briefly about the commute. Emma is warm and efficient — she offers you water, "
             "points out the toilets, and guides you to a glass-walled meeting room with a whiteboard "
             "that still has someone else's diagram on it.",
             BG["nexus"], "n_emma_q1"),

        # ----------------------------------------------------------------
        # THE INTERVIEW
        # ----------------------------------------------------------------
        _say("n_emma_q1", "emma",
             "So — tell me about yourself and what drew you to Nexus specifically. "
             "And don't just read from your CV; I've already read that.",
             BG["nexus"], "n_c3_interview"),

        # CHOICE 3 ─ interview approach
        _choice("n_c3_interview",
                "How do you structure your answer?",
                [
                    _ch("\"I graduated in 2023 with a degree in Computer Science. "
                        "In the past year I've gained experience in backend development and...\"",
                        "n_s3_formal", {"_int_style": "formal"}),
                    _ch("\"Honestly, what really excited me about Nexus was reading about your "
                        "user-centred approach. Most companies say that — you actually seem to do it.\"",
                        "n_s3_story", {"_int_style": "story"}),
                ],
                BG["nexus"]),

        _say("n_s3_formal", "emma",
             "Good. Solid foundations are important. We're a small team, so everyone wears multiple hats. "
             "Let me ask you something more specific.",
             BG["nexus"], "n_emma_q2_level"),

        _say("n_s3_story", "emma",
             "I appreciate that. We do try to practise what we preach. "
             "It's refreshing to hear someone who's actually done their research. "
             "Tell me more — how did you come across us?",
             BG["nexus"], "n_emma_q2_level"),

        # Level-adaptive follow-up question
        _if("n_emma_q2_level", "_level", "B1", "n_q2_b1", "n_q2_b2_check"),
        _if("n_q2_b2_check", "_level", "C1", "n_q2_c1", "n_q2_b2"),

        _say("n_q2_b1", "emma",
             "Can you give me an example of a difficult problem you solved?",
             BG["nexus"], "n_alex_answer"),

        _say("n_q2_b2", "emma",
             "Could you walk me through how you handle pressure — particularly tight deadlines "
             "or situations where requirements keep changing?",
             BG["nexus"], "n_alex_answer"),

        _say("n_q2_c1", "emma",
             "I'd be curious to hear how you've navigated high-stakes situations where you had "
             "to exercise both technical judgment and interpersonal tact simultaneously — "
             "particularly where the goalposts were moving.",
             BG["nexus"], "n_alex_answer"),

        _say("n_alex_answer", "narrator",
             "You take a beat before answering — not from uncertainty, but to collect your thoughts. "
             "You give a concrete example: a project where the brief changed mid-build, "
             "and how you communicated proactively with your client to adjust expectations. "
             "Emma listens without interrupting, which you take as a good sign.",
             BG["nexus"], "n_int_result_if"),

        _if("n_int_result_if", "_int_style", "story", "n_strong_offer", "n_standard_offer"),

        _say("n_strong_offer", "emma",
             "That was genuinely compelling, Alex. You clearly understand how to communicate under pressure. "
             "I'm confident we can put together a strong offer. I'll be in touch by end of week. "
             "Do you have any questions for us?",
             BG["nexus"], "n_alex_question"),

        _say("n_standard_offer", "emma",
             "Thank you, Alex. You have a solid background and I think you'd be a great fit. "
             "We'll discuss internally and come back to you. Any questions for us?",
             BG["nexus"], "n_alex_question"),

        _say("n_alex_question", "narrator",
             "You ask about team culture and day-to-day workflow. Emma's face lights up.",
             BG["nexus"], "n_emma_culture"),

        _say("n_emma_culture", "emma",
             "Oh, it's brilliant here — very flat structure, no pointless hierarchy. "
             "Your potential team lead Jake runs things collaboratively. People genuinely like working here, "
             "which I know everyone says, but our retention rate is 94%, so.",
             BG["nexus"], "n_cp2"),

        # ----------------------------------------------------------------
        # CHECKPOINT 2 — First day
        # ----------------------------------------------------------------
        _set("n_cp2", {"_chapter": "first_day"}, "n_first_day"),

        _say("n_first_day", "narrator",
             "Three days later. You got the job. Today is your first official day. "
             "You arrive at 9:55, five minutes early, which feels precisely right.",
             BG["nexus"], "n_meet_jake"),

        _say("n_meet_jake", "jake",
             "Alex! Welcome to the team! I'm Jake — your team lead. "
             "Don't worry, we don't bite. Well — I might, before my morning coffee.",
             BG["nexus"], "n_meet_priya"),

        _say("n_meet_priya", "priya",
             "Hi Alex! I'm Priya — I sit right across from you. "
             "If you need anything at all, just ask. Also, ignore whatever Jake just said.",
             BG["nexus"], "n_morning_work"),

        _say("n_morning_work", "narrator",
             "The morning is a blur of onboarding documents, system access, and introductions. "
             "Everyone seems genuinely pleased to have you. By noon, you've learned six new faces "
             "and forgotten most of their names.",
             BG["nexus"], "n_lunch_invite"),

        _say("n_lunch_invite", "priya",
             "Hey Alex — we're heading to a little Italian place just down the road. "
             "Best pasta in Shoreditch, I promise. Want to join us?",
             BG["nexus"], "n_c4_lunch"),

        # CHOICE 4 ─ lunch decision
        _choice("n_c4_lunch",
                "What do you decide?",
                [
                    _ch("\"Absolutely — I'd love that.\"",
                        "n_s4_join", {"_lunch": "joined"}),
                    _ch("\"Thanks, but I want to finish setting up my workspace first.\"",
                        "n_s4_work", {"_lunch": "working"}),
                ],
                BG["nexus"]),

        _say("n_s4_join", "narrator",
             "You grab your jacket and follow the small group out into the afternoon sun. "
             "The restaurant is tucked between a vintage clothes shop and a coffee roastery. "
             "It smells incredible.",
             BG["rest"], "n_lunch_priya_story"),

        _say("n_lunch_priya_story", "priya",
             "So — what made you move to London? I came from Birmingham two years ago. "
             "Best decision I ever made, even if the rent is borderline criminal.",
             BG["rest"], "n_lunch_jake_tip"),

        _say("n_lunch_jake_tip", "jake",
             "Word of advice: never use the printer on the third floor. "
             "We call it 'The Beast'. It jams if you look at it wrong. "
             "People have cried.",
             BG["rest"], "n_join_afternoon"),

        _jump("n_join_afternoon", "n_afternoon"),

        _say("n_s4_work", "narrator",
             "You stay at your desk and make solid progress on your onboarding tasks. "
             "The office is quieter without everyone, but productive.",
             BG["nexus"], "n_work_note"),

        _say("n_work_note", "narrator",
             "When the others return from lunch, you catch the tail end of a story Priya is telling. "
             "Everyone laughs. You smile and make a mental note to join next time.",
             BG["nexus"], "n_afternoon"),

        # ----------------------------------------------------------------
        # AFTERNOON — British slang moment
        # ----------------------------------------------------------------
        _say("n_afternoon", "jake",
             "Hey Alex — could you get the ball rolling on the onboarding documentation? "
             "Just get familiar with our workflow first. No rush, but sooner is better.",
             BG["nexus"], "n_c5_slang"),

        # CHOICE 5 ─ do you know the idiom?
        _choice("n_c5_slang",
                "Jake used a British expression. What do you do?",
                [
                    _ch("\"Sure thing — I'll get started on it now.\" [You know the expression]",
                        "n_s5_knew"),
                    _ch("\"Sorry Jake — I'm not sure what 'get the ball rolling' means?\"",
                        "n_s5_ask", {"_asked": "asked"}),
                ],
                BG["nexus"]),

        _say("n_s5_knew", "narrator",
             "You open the workflow documentation and start working through it systematically. "
             "Jake nods approvingly.",
             BG["nexus"], "n_afternoon_cont"),

        _say("n_s5_ask", "jake",
             "Ha! Good call — always better to ask than to nod along. "
             "'Get the ball rolling' just means get started, initiate something. "
             "Very British. I use it without thinking.",
             BG["nexus"], "n_afternoon_cont"),

        _say("n_afternoon_cont", "narrator",
             "The afternoon is productive. By 5 PM you've completed your onboarding documentation "
             "and started getting to grips with the team's workflow. Your brain hurts, but in a good way.",
             BG["nexus"], "n_end_of_day"),

        _say("n_end_of_day", "priya",
             "Hey — a few of us are going to Flat Iron for dinner tonight. "
             "It's sort of a tradition for new starters. You should definitely come.",
             BG["nexus"], "n_c6_dinner"),

        # CHOICE 6 ─ dinner decision
        _choice("n_c6_dinner",
                "It's been a long day. What do you decide?",
                [
                    _ch("\"I'd love to! Just let me grab my coat.\"",
                        "n_s6_join", {"_dinner": "joined"}),
                    _ch("\"Thank you — but I'm absolutely shattered. Rain check?\"",
                        "n_s6_skip", {"_dinner": "skipped"}),
                ],
                BG["nexus"]),

        # Dinner branch
        _say("n_s6_join", "narrator",
             "The restaurant is warm and bustling. The conversation flows from work gossip "
             "to weekend plans to increasingly elaborate stories about 'The Beast'.",
             BG["rest"], "n_jake_toast"),

        _say("n_jake_toast", "jake",
             "Welcome to Nexus, Alex. You've genuinely hit the ground running today — "
             "the team is really glad to have you on board.",
             BG["rest"], "n_priya_dinner"),

        _say("n_priya_dinner", "priya",
             "We've been trying to fill your role for months. "
             "I honestly think you're going to do brilliantly here.",
             BG["rest"], "n_dinner_end"),

        _jump("n_dinner_end", "n_ending_check"),

        # Skip branch
        _say("n_s6_skip", "narrator",
             "You head home through the evening streets of Shoreditch. "
             "The city glitters and hums around you. You're exhausted but quietly elated.",
             BG["night"], "n_skip_reflection"),

        _say("n_skip_reflection", "narrator",
             "You make yourself a cup of tea and sit on the floor of your tiny flat — "
             "because you still haven't bought a chair — and let the day settle.",
             BG["night"], "n_ending_check"),

        # ----------------------------------------------------------------
        # ENDINGS (3 paths)
        # ----------------------------------------------------------------
        _if("n_ending_check", "_dinner", "joined", "n_end_great_check", "n_end_good_check"),

        # Great ending path: joined dinner + joined lunch
        _if("n_end_great_check", "_lunch", "joined", "n_ending_great", "n_ending_good"),

        # Good ending path: skipped dinner, but asked the question (self-aware)
        _if("n_end_good_check", "_asked", "asked", "n_ending_good", "n_ending_okay"),

        _say("n_ending_great", "narrator",
             "Two weeks in and it already feels like home. You know everyone's coffee order, "
             "you've been invited to three after-work events, and Jake told Emma you're 'the real deal'. "
             "The city that seemed so overwhelming on day one has begun, quietly, to make sense.",
             BG["night"], "n_end_great"),

        _say("n_ending_good", "narrator",
             "The first two weeks are demanding — there's a lot to learn and the city takes adjustment. "
             "But you're getting there. Priya has become a genuine ally, and Jake told you last Friday "
             "that your work on the documentation was 'exactly what we needed'. "
             "A solid start. London is beginning to feel like yours.",
             BG["night"], "n_end_good"),

        _say("n_ending_okay", "narrator",
             "The first fortnight is challenging. You put in long hours and stay focused on the work, "
             "but the social side of things hasn't quite clicked yet. "
             "You know it takes time. London is a marathon, not a sprint. "
             "You're still finding your feet — but you're finding them.",
             BG["night"], "n_end_okay"),

        _end("n_end_great"),
        _end("n_end_good"),
        _end("n_end_okay"),
    ]

    return {
        "version": "1.0",
        "meta": {
            "title": NOVEL_TITLE,
            "language": "en",
            "level": "B2",
            "description": "A story about navigating a new city, a job interview, and the first day at a startup."
        },
        "assets": {
            "characters": {
                "narrator": {"name": ""},
                "emma":     {"name": "Emma",  "image": EMMA_IMG,  "role": "HR Manager"},
                "jake":     {"name": "Jake",  "image": JAKE_IMG,  "role": "Team Lead",   "position": "left"},
                "priya":    {"name": "Priya", "image": PRIYA_IMG, "role": "Colleague",   "position": "right"},
            },
            "backgrounds": {
                "city":  {"image": "https://picsum.photos/seed/london_street/1920/1080"},
                "apt":   {"image": "https://picsum.photos/seed/studio_apartment/1920/1080"},
                "cafe":  {"image": "https://picsum.photos/seed/coffee_shop_morning/1920/1080"},
                "tube":  {"image": "https://picsum.photos/seed/underground_london/1920/1080"},
                "nexus": {"image": "https://picsum.photos/seed/modern_startup_office/1920/1080"},
                "rest":  {"image": "https://picsum.photos/seed/italian_restaurant_warm/1920/1080"},
                "night": {"image": "https://picsum.photos/seed/london_night_bridges/1920/1080"},
            },
            "music": {},
        },
        "start": "n_intro",
        "nodes": nodes,
    }


# ---------------------------------------------------------------------------
# Vocabulary (20 words, B1/B2/C1 tagged)
# ---------------------------------------------------------------------------

VOCABULARY = [
    # B1
    {
        "word": "commute",
        "translation": "ездить на работу (регулярно)",
        "transcription": "kəˈmjuːt",
        "definition": "To travel regularly between home and work.",
        "example": "She commutes to the office by tube every morning.",
        "level": "B1",
    },
    {
        "word": "schedule",
        "translation": "расписание; планировать",
        "transcription": "ˈʃedjuːl",
        "definition": "A plan of activities or events and when they will happen.",
        "example": "Can we schedule the meeting for Thursday afternoon?",
        "level": "B1",
    },
    {
        "word": "confirm",
        "translation": "подтверждать",
        "transcription": "kənˈfɜːm",
        "definition": "To state or show that something is definitely true or will happen.",
        "example": "Please confirm your attendance by Friday.",
        "level": "B1",
    },
    {
        "word": "colleague",
        "translation": "коллега",
        "transcription": "ˈkɒliːɡ",
        "definition": "A person you work with, especially in a professional setting.",
        "example": "I went to lunch with my new colleagues on the first day.",
        "level": "B1",
    },
    {
        "word": "flexible",
        "translation": "гибкий",
        "transcription": "ˈfleksɪbl",
        "definition": "Able to adapt easily to changing situations.",
        "example": "We offer flexible working hours at this company.",
        "level": "B1",
    },
    # B2
    {
        "word": "retain",
        "translation": "удерживать, сохранять",
        "transcription": "rɪˈteɪn",
        "definition": "To keep something or to continue to have something.",
        "example": "The company has a high staff retention rate.",
        "level": "B2",
    },
    {
        "word": "proactive",
        "translation": "проактивный, инициативный",
        "transcription": "ˌprəʊˈæktɪv",
        "definition": "Taking action to deal with problems or opportunities before they occur.",
        "example": "She was proactive about communicating changes to her client.",
        "level": "B2",
    },
    {
        "word": "deadline",
        "translation": "дедлайн, крайний срок",
        "transcription": "ˈdedlaɪn",
        "definition": "A point in time by which something must be finished.",
        "example": "We need to meet the deadline by the end of the week.",
        "level": "B2",
    },
    {
        "word": "collaborate",
        "translation": "сотрудничать",
        "transcription": "kəˈlæbəreɪt",
        "definition": "To work together with others to achieve a goal.",
        "example": "The two teams collaborated on the new product launch.",
        "level": "B2",
    },
    {
        "word": "networking",
        "translation": "нетворкинг, профессиональные связи",
        "transcription": "ˈnetwɜːkɪŋ",
        "definition": "Building relationships with people who could be useful to your career.",
        "example": "Attending industry events is great for networking.",
        "level": "B2",
    },
    {
        "word": "hierarchy",
        "translation": "иерархия",
        "transcription": "ˈhaɪərɑːki",
        "definition": "A system in which people or things are ranked according to importance.",
        "example": "Nexus has a flat hierarchy — no one has a separate office.",
        "level": "B2",
    },
    {
        "word": "onboarding",
        "translation": "адаптация нового сотрудника",
        "transcription": "ˈɒnbɔːdɪŋ",
        "definition": "The process of integrating a new employee into a company.",
        "example": "The onboarding programme lasts two weeks.",
        "level": "B2",
    },
    {
        "word": "initiative",
        "translation": "инициатива",
        "transcription": "ɪˈnɪʃətɪv",
        "definition": "The ability to act and make decisions without waiting to be told.",
        "example": "She took the initiative and reorganised the filing system.",
        "level": "B2",
    },
    # C1 — phrasal verbs and idioms
    {
        "word": "get the ball rolling",
        "translation": "начать что-то, дать старт",
        "transcription": "ɡet ðə bɔːl ˈrəʊlɪŋ",
        "definition": "Phrasal verb: to start an activity or process.",
        "example": "Jake asked Alex to get the ball rolling on the documentation.",
        "level": "C1",
    },
    {
        "word": "hit the ground running",
        "translation": "сразу взяться за дело, начать активно",
        "transcription": "hɪt ðə ɡraʊnd ˈrʌnɪŋ",
        "definition": "Idiom: to start something enthusiastically and energetically from the beginning.",
        "example": "She hit the ground running on her first day — impressive.",
        "level": "C1",
    },
    {
        "word": "wear multiple hats",
        "translation": "совмещать несколько ролей",
        "transcription": "weər ˈmʌltɪpl hæts",
        "definition": "Idiom: to have several different roles or responsibilities at once.",
        "example": "In a small startup, you often wear multiple hats.",
        "level": "C1",
    },
    {
        "word": "brush up on",
        "translation": "освежить знания по (чему-то)",
        "transcription": "brʌʃ ʌp ɒn",
        "definition": "Phrasal verb: to improve or refresh knowledge or a skill.",
        "example": "I need to brush up on my Python before the technical interview.",
        "level": "C1",
    },
    {
        "word": "put a face to the name",
        "translation": "наконец-то увидеть человека после общения заочно",
        "transcription": "pʊt ə feɪs tə ðə neɪm",
        "definition": "Idiom: to finally meet someone in person after communicating remotely.",
        "example": "Emma said it was great to finally put a face to the name.",
        "level": "C1",
    },
    {
        "word": "flat white",
        "translation": "флэт уайт (кофейный напиток)",
        "transcription": "flæt waɪt",
        "definition": "A coffee drink made with espresso and steamed milk, popular in the UK and Australia.",
        "example": "She ordered a flat white at the café near Old Street.",
        "level": "B2",
    },
    {
        "word": "acumen",
        "translation": "проницательность, деловая хватка",
        "transcription": "ˈækjʊmən",
        "definition": "The ability to make good judgements and quick decisions in a business context.",
        "example": "Her business acumen was evident from the first interview.",
        "level": "C1",
    },
]


# ---------------------------------------------------------------------------
# Quiz definition
# ---------------------------------------------------------------------------

QUIZ_DATA = {
    "chapter_node_id": "n_cp2",
    "title": "Chapter 1 Quiz: City Moves",
    "pass_threshold": 0.6,
    "questions": [
        {
            "text": "What is Alex's main reason for moving to London?",
            "type": "single",
            "hint": "Think about the story's opening. What event triggered the move?",
            "choices": [
                {"text": "To study at a London university", "correct": False,
                 "explanation": "Alex has already graduated — this is about a job."},
                {"text": "To attend a job interview at a startup called Nexus Tech", "correct": True,
                 "explanation": "Correct! Alex received an email from Nexus Tech and moved for the interview."},
                {"text": "To visit family who live in London", "correct": False,
                 "explanation": "There's no mention of family in the story."},
                {"text": "To escape a difficult situation in another city", "correct": False,
                 "explanation": "The story is about opportunity, not escape."},
            ],
        },
        {
            "text": "What does the idiom 'hit the ground running' mean?",
            "type": "single",
            "hint": "Jake uses this phrase when complimenting Alex at the dinner.",
            "choices": [
                {"text": "To stumble at the start of a project", "correct": False,
                 "explanation": "It's the opposite — it means starting strongly, not stumbling."},
                {"text": "To start something enthusiastically and effectively from the beginning", "correct": True,
                 "explanation": "Exactly right. 'Hit the ground running' means to begin with full energy and purpose."},
                {"text": "To run away from a difficult situation", "correct": False,
                 "explanation": "This phrase has nothing to do with running away."},
                {"text": "To begin a project by researching it first", "correct": False,
                 "explanation": "While preparation is implied, the phrase specifically means starting actively and energetically."},
            ],
        },
        {
            "text": "What does 'get the ball rolling' mean in British English?",
            "type": "single",
            "hint": "Jake says this when asking Alex to start a task.",
            "choices": [
                {"text": "To complete a task", "correct": False,
                 "explanation": "It means to start something, not to finish it."},
                {"text": "To pass work to a colleague", "correct": False,
                 "explanation": "It's about initiating, not delegating."},
                {"text": "To get started on something; to initiate an activity", "correct": True,
                 "explanation": "Correct! 'Get the ball rolling' means to begin or initiate a process."},
                {"text": "To play a team sport together", "correct": False,
                 "explanation": "This is an idiom about starting something, not literal ball games."},
            ],
        },
        {
            "text": "What does 'onboarding' refer to in a workplace context?",
            "type": "single",
            "hint": "Alex completes onboarding tasks on the first day at Nexus.",
            "choices": [
                {"text": "A type of software used in offices", "correct": False,
                 "explanation": "Onboarding is a process, not a software tool."},
                {"text": "The process of integrating a new employee into a company", "correct": True,
                 "explanation": "Correct! Onboarding includes orientation, documentation, and meeting the team."},
                {"text": "A meeting to discuss project requirements", "correct": False,
                 "explanation": "That would be a briefing or kickoff meeting."},
                {"text": "The practice of remote working", "correct": False,
                 "explanation": "Remote work and onboarding are separate concepts."},
            ],
        },
        {
            "text": "What does it mean for a company to have a 'flat structure' or 'flat hierarchy'?",
            "type": "single",
            "hint": "Emma describes Nexus as having this kind of structure.",
            "choices": [
                {"text": "The office is on one floor only", "correct": False,
                 "explanation": "It's a metaphor about management levels, not the physical building."},
                {"text": "There are few or no management layers between staff and leadership", "correct": True,
                 "explanation": "Correct! A flat hierarchy means decisions are decentralised and everyone has more direct access to leadership."},
                {"text": "All employees earn the same salary", "correct": False,
                 "explanation": "Flat hierarchy refers to management structure, not pay equality."},
                {"text": "The company has recently downsized", "correct": False,
                 "explanation": "Downsizing and flat structure are unrelated concepts."},
            ],
        },
        {
            "text": "In the café, what is a 'flat white'?",
            "type": "single",
            "hint": "Alex orders this popular British/Australian coffee drink.",
            "choices": [
                {"text": "A large black coffee with no milk", "correct": False,
                 "explanation": "A flat white contains steamed milk — it's not a black coffee."},
                {"text": "A coffee drink made with espresso and steamed milk", "correct": True,
                 "explanation": "Correct! A flat white is espresso topped with velvety steamed milk. Very popular in the UK."},
                {"text": "A type of tea with milk", "correct": False,
                 "explanation": "A flat white is a coffee-based drink, not tea."},
                {"text": "A cold brew coffee from Australia", "correct": False,
                 "explanation": "Flat whites are served hot and originated in Australia/New Zealand."},
            ],
        },
        {
            "text": "What does 'proactive' mean?",
            "type": "single",
            "hint": "Alex is described as proactive when answering the interview question.",
            "choices": [
                {"text": "Reacting quickly after a problem has already occurred", "correct": False,
                 "explanation": "That would be 'reactive'. Proactive is the opposite."},
                {"text": "Taking action to deal with situations before they become problems", "correct": True,
                 "explanation": "Exactly right. Proactive means anticipating needs and acting in advance."},
                {"text": "Being very professional in formal situations", "correct": False,
                 "explanation": "Professional and proactive are related but different qualities."},
                {"text": "Asking many questions to understand a task", "correct": False,
                 "explanation": "Asking questions is good, but proactive specifically means acting in anticipation."},
            ],
        },
        {
            "text": "Which phrase means 'to refresh or improve knowledge you already have'?",
            "type": "single",
            "hint": "Alex uses this phrasal verb when preparing for the interview at home.",
            "choices": [
                {"text": "Get the ball rolling", "correct": False,
                 "explanation": "This means to start something, not to revise knowledge."},
                {"text": "Wear multiple hats", "correct": False,
                 "explanation": "This means to have many roles, not to review existing knowledge."},
                {"text": "Brush up on", "correct": True,
                 "explanation": "Correct! 'Brush up on' means to review or improve a skill or knowledge area you've previously learned."},
                {"text": "Hit the ground running", "correct": False,
                 "explanation": "This means to start enthusiastically, not to revise."},
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

ACHIEVEMENTS = [
    {
        "code": "first_novel",
        "title": "City Explorer",
        "description": "Complete your first visual novel from start to finish.",
        "icon": "🗺️",
        "points": 50,
    },
    {
        "code": "five_novels",
        "title": "Bookworm",
        "description": "Complete five visual novels.",
        "icon": "📚",
        "points": 100,
    },
    {
        "code": "first_choice",
        "title": "Decision Maker",
        "description": "Make your first story choice — every path begins with a decision.",
        "icon": "🔀",
        "points": 15,
    },
    {
        "code": "vocab_5",
        "title": "Word Collector",
        "description": "Add 5 words to your personal vocabulary list.",
        "icon": "📖",
        "points": 20,
    },
    {
        "code": "vocab_10",
        "title": "Vocabulary Builder",
        "description": "Learn 10 vocabulary words across all novels.",
        "icon": "🧩",
        "points": 35,
    },
    {
        "code": "vocab_50",
        "title": "Word Master",
        "description": "Collect 50 vocabulary words — your English is growing fast.",
        "icon": "🏆",
        "points": 100,
    },
    {
        "code": "first_quiz",
        "title": "Quiz Taker",
        "description": "Submit your first chapter quiz.",
        "icon": "📝",
        "points": 25,
    },
    {
        "code": "quiz_master",
        "title": "Quiz Champion",
        "description": "Pass 10 quizzes with a passing score.",
        "icon": "🎯",
        "points": 75,
    },
]


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed the educational visual novel 'City Moves: A Fresh Start'."

    def handle(self, *args, **options):
        self._seed_achievements()
        novel = self._seed_novel()
        self._seed_vocabulary(novel)
        self._seed_quiz(novel)
        self.stdout.write(self.style.SUCCESS(
            f"Novel '{NOVEL_TITLE}' (id={novel.id}) seeded successfully."
        ))

    # -----------------------------------------------------------------------

    def _seed_achievements(self):
        count = 0
        for data in ACHIEVEMENTS:
            _, created = Achievement.objects.update_or_create(
                code=data["code"],
                defaults={
                    "title": data["title"],
                    "description": data["description"],
                    "icon": data["icon"],
                    "points": data["points"],
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  Achievements: {count} created / {len(ACHIEVEMENTS) - count} updated")

    def _seed_novel(self) -> Novel:
        scenario = build_scenario()
        payload = json.dumps(scenario, ensure_ascii=False, indent=2).encode("utf-8")
        filename = "city_moves_a_fresh_start.json"

        novel, created = Novel.objects.get_or_create(
            title=NOVEL_TITLE,
            defaults={
                "description": (
                    "A branching story about navigating a job interview and first day "
                    "at a London startup. Features adaptive content for B1, B2, and C1 levels, "
                    "British idioms, workplace vocabulary, and three possible endings."
                ),
                "language_level": "B2",
                "genre": "Slice of Life",
                "estimated_minutes": 25,
                "is_published": True,
            },
        )

        # Always refresh scenario file so changes take effect on re-runs
        novel.scenario_file.save(filename, ContentFile(payload), save=False)
        novel.language_level = "B2"
        novel.genre = "Slice of Life"
        novel.estimated_minutes = 25
        novel.is_published = True
        novel.save()

        action = "Created" if created else "Updated"
        self.stdout.write(f"  Novel: {action} id={novel.id}")
        return novel

    def _seed_vocabulary(self, novel: Novel):
        count = 0
        for data in VOCABULARY:
            _, created = VocabularyWord.objects.update_or_create(
                novel=novel,
                word=data["word"],
                defaults={
                    "translation": data["translation"],
                    "transcription": data["transcription"],
                    "definition": data["definition"],
                    "example": data["example"],
                    "level": data["level"],
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  Vocabulary: {count} created / {len(VOCABULARY) - count} updated")

    def _seed_quiz(self, novel: Novel):
        qd = QUIZ_DATA
        quiz, created = Quiz.objects.update_or_create(
            novel=novel,
            chapter_node_id=qd["chapter_node_id"],
            defaults={
                "title": qd["title"],
                "pass_threshold": qd["pass_threshold"],
            },
        )
        q_count = 0
        for order, qdata in enumerate(qd["questions"]):
            question, q_created = QuizQuestion.objects.update_or_create(
                quiz=quiz,
                order=order,
                defaults={
                    "text": qdata["text"],
                    "question_type": qdata["type"],
                    "hint": qdata.get("hint", ""),
                },
            )
            if q_created:
                q_count += 1
            for cdata in qdata["choices"]:
                QuizChoice.objects.update_or_create(
                    question=question,
                    text=cdata["text"],
                    defaults={
                        "is_correct": cdata["correct"],
                        "explanation": cdata.get("explanation", ""),
                    },
                )
        action = "Created" if created else "Updated"
        self.stdout.write(
            f"  Quiz: {action} '{quiz.title}' with {q_count} new questions"
        )
