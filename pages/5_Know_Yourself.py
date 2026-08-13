import random

import streamlit as st


st.set_page_config(
    page_title="Know Yourself",
    page_icon="🪞",
    layout="wide",
)


QUESTIONS = [
    {
        "trait": "Social energy",
        "question": "After a long, demanding week, what actually recharges you?",
        "left": ("A loud night out with a big group", "You draw energy from crowds, noise, and new faces."),
        "middle": ("A dinner with one or two close friends", "You recharge through connection, but in small, chosen doses."),
        "right": ("A quiet evening completely alone", "Solitude is where your energy comes back, not people."),
    },
    {
        "trait": "Planning style",
        "question": "You're handed a free Saturday with no obligations. What happens?",
        "left": ("You plan the whole day, hour by hour", "Structure and a clear plan is what makes free time feel good."),
        "middle": ("You have a rough idea, but stay flexible", "You like a loose shape, with room to change your mind."),
        "right": ("You wake up and decide as you go", "Spontaneity feels freer to you than any plan could."),
    },
    {
        "trait": "Conflict style",
        "question": "Someone close to you says something that genuinely upsets you. What's your first move?",
        "left": ("Say exactly how you feel, right away", "You'd rather have friction now than silence later."),
        "middle": ("Sit with it, then bring it up calmly later", "You need a beat to think before you speak, but you do speak up."),
        "right": ("Let it go and hope it resolves itself", "Keeping the peace usually feels safer than confrontation."),
    },
    {
        "trait": "Risk & change",
        "question": "A new opportunity shows up that means leaving something stable behind. What's your instinct?",
        "left": ("Jump in — the upside is worth the risk", "Uncertainty excites you more than it scares you."),
        "middle": ("Weigh it carefully before deciding either way", "You want real evidence before you'll trade stability for potential."),
        "right": ("Stay put — the known is worth more than the maybe", "Stability isn't boring to you, it's the thing you protect."),
    },
    {
        "trait": "Self-view under pressure",
        "question": "A project you led just failed publicly. What's the loudest voice in your head?",
        "left": ("\"This wasn't really my fault\"", "Under pressure, you look outward first for the cause."),
        "middle": ("\"Some of this was me, some wasn't\"", "You can usually separate what you controlled from what you didn't."),
        "right": ("\"I should have seen this coming\"", "Under pressure, you look inward first, sometimes harder than you should."),
    },
    {
        "trait": "Emotional expression",
        "question": "You're having the best day you've had in months. How does it show?",
        "left": ("Everyone around you knows it immediately", "Your feelings are visible almost as soon as you have them."),
        "middle": ("Close people can tell, most others can't", "You show emotion selectively, mostly to people you trust."),
        "right": ("You keep it mostly to yourself", "You feel things fully on the inside without needing to display them."),
    },
    {
        "trait": "Decision-making",
        "question": "You have to make a hard call with incomplete information. What guides you?",
        "left": ("Gut feeling — it's rarely steered you wrong", "You trust intuition built from experience over a spreadsheet."),
        "middle": ("A mix of gut feeling and a quick pros/cons check", "You want both a feeling and a reason before committing."),
        "right": ("Data and logic, even if it takes longer", "You trust a clear argument more than a feeling, however strong."),
    },
    {
        "trait": "Relationship to routine",
        "question": "Your daily routine gets disrupted for a week. How do you feel about it?",
        "left": ("Relieved — routine was starting to feel like a cage", "Novelty feels like oxygen; sameness feels like weight."),
        "middle": ("Mildly annoyed, but you adapt quickly", "You like rhythm, but you're not thrown by losing it briefly."),
        "right": ("Unsettled — you need your routine back", "Predictability is load-bearing for your sense of calm."),
    },
    {
        "trait": "View of feedback",
        "question": "A mentor gives you blunt, critical feedback on something you're proud of. What's your honest reaction?",
        "left": ("Defensive first, curious second", "Criticism lands as an attack before it lands as information."),
        "middle": ("Stings for a moment, then useful", "You feel it, but you can usually get past the sting to the substance."),
        "right": ("Genuinely grateful, almost immediately", "You've trained yourself to hear feedback as a gift, not a verdict."),
    },
    {
        "trait": "Locus of identity",
        "question": "When you imagine your best possible future, whose approval matters most in that picture?",
        "left": ("Mine — I just want to be proud of myself", "Your compass points inward; outside validation is secondary."),
        "middle": ("A small circle of people I deeply respect", "You care about approval, but only from a few carefully chosen judges."),
        "right": ("The people around me and what they think", "External validation is a real and active part of how you measure a good life."),
    },
    {
        "trait": "Trust in others",
        "question": "You meet someone new. What's your default starting point?",
        "left": ("Open and trusting until they give me a reason not to be", "You extend trust first and treat betrayal as the exception, not the rule."),
        "middle": ("Friendly, but I watch how they act before I trust them", "Trust is earned gradually, through consistent behavior over time."),
        "right": ("Guarded until they've clearly proven themselves", "You protect yourself first; trust has to be won, not assumed."),
    },
    {
        "trait": "Ambition",
        "question": "What does 'a good life' mean to you, honestly?",
        "left": ("Building something big that outlasts me", "Ambition and legacy are core to how you measure a life well lived."),
        "middle": ("Steady growth and real satisfaction in ordinary days", "You want progress, but contentment matters just as much as achievement."),
        "right": ("Peace, simplicity, and time with people I love", "A quiet, connected life outweighs status or accomplishment for you."),
    },
    {
        "trait": "Perfectionism",
        "question": "You finish a piece of work you're moderately happy with, but it's due now. What do you do?",
        "left": ("Keep refining it even past the deadline", "'Good enough' rarely feels acceptable to you."),
        "middle": ("Do one more pass, then let it go", "You push for quality but know when to stop."),
        "right": ("Ship it — done is better than perfect", "You'd rather move forward imperfectly than stall chasing polish."),
    },
    {
        "trait": "Empathy in practice",
        "question": "A friend vents to you about a problem you think they're partly causing themselves. What do you actually say?",
        "left": ("Just listen and support them, no matter what", "In the moment, being there matters more to you than being right."),
        "middle": ("Listen first, then gently offer my honest take", "You balance comfort with honesty, timed carefully."),
        "right": ("Tell them the hard truth, even if it stings", "You'd rather be useful than comfortable, even with people you love."),
    },
    {
        "trait": "Time orientation",
        "question": "Where does your mind wander most often when it's idle?",
        "left": ("Replaying moments from the past", "You process life largely by looking backward and making sense of it."),
        "middle": ("Whatever's happening right now", "You tend to stay anchored in the present more than most."),
        "right": ("Planning or imagining what's ahead", "Your attention naturally leans toward what's coming next."),
    },
    {
        "trait": "Attitude toward money",
        "question": "You unexpectedly receive a meaningful amount of money. What's your first instinct?",
        "left": ("Save or invest almost all of it", "Security and long-term safety matter more to you than the moment."),
        "middle": ("Save most, spend a bit on something meaningful now", "You balance future security with present enjoyment."),
        "right": ("Spend it on an experience or people you care about", "Money is for living now, not just protecting later."),
    },
    {
        "trait": "Independence",
        "question": "You're struggling with something hard. What's more natural for you?",
        "left": ("Figuring it out completely on my own", "Asking for help feels like a last resort, not a first step."),
        "middle": ("Trying myself first, then asking if I'm stuck", "You value self-reliance but aren't too proud to reach out."),
        "right": ("Asking for help early rather than struggling alone", "You see reaching out as efficient and healthy, not weak."),
    },
    {
        "trait": "Outlook",
        "question": "A plan you were excited about just fell through. What's your honest first reaction?",
        "left": ("\"Of course it did — things like this always happen\"", "Setbacks tend to confirm a more guarded view of how things go."),
        "middle": ("Disappointed, but I figure something else will work out", "You feel the loss but don't extrapolate it into a pattern."),
        "right": ("\"Something better is probably coming\"", "You default to believing things tend to work out, even before evidence arrives."),
    },
    {
        "trait": "Boundaries",
        "question": "Someone asks you for a favor at a genuinely bad time. What do you do?",
        "left": ("Say yes anyway — I don't like disappointing people", "Other people's needs tend to outrank your own limits, even at a cost."),
        "middle": ("Offer a smaller version of what they're asking for", "You look for a compromise that respects both sides."),
        "right": ("Say no clearly, without much guilt", "Protecting your own time and energy comes naturally to you."),
    },
    {
        "trait": "Creativity vs practicality",
        "question": "You're given a problem with a proven, boring solution and a risky, original one. Which pulls at you?",
        "left": ("The original idea, even if it might fail", "Novelty and self-expression matter more to you than certainty."),
        "middle": ("A blend — a proven base with your own twist", "You want originality, but grounded in something that reliably works."),
        "right": ("The proven solution — it works, why risk it", "Reliability wins out over originality for you, most of the time."),
    },
    {
        "trait": "Competitiveness",
        "question": "You're playing a casual game with friends and you're losing badly. How do you feel?",
        "left": ("Genuinely bothered — I want to win", "Competition activates something real in you, even in low-stakes settings."),
        "middle": ("A little annoyed, but mostly still having fun", "You'd like to win, but the fun isn't conditional on it."),
        "right": ("Totally indifferent — it's just a game", "Winning or losing barely registers for you outside of real stakes."),
    },
    {
        "trait": "Forgiveness",
        "question": "Someone who hurt you apologizes sincerely, months later. What's true for you?",
        "left": ("I forgive quickly once I understand why", "You let go relatively fast once you have the full picture."),
        "middle": ("I forgive, but it takes real time to feel it", "Forgiveness comes, but on its own schedule, not on request."),
        "right": ("The apology helps, but the wall stays partly up", "Some part of the guard you built rarely comes all the way down."),
    },
    {
        "trait": "Changing your mind",
        "question": "You're presented with solid evidence against a belief you've held for years. What happens?",
        "left": ("I update relatively easily", "You treat your beliefs as provisional, not identity."),
        "middle": ("I resist at first, then come around", "You need a little friction before a belief actually shifts."),
        "right": ("I hold on unless it's completely undeniable", "Long-held beliefs feel like part of who you are, not just opinions."),
    },
    {
        "trait": "Vulnerability",
        "question": "How easily do you let people see you when you're struggling, not just when you're fine?",
        "left": ("Very easily — I don't hide much", "Openness about struggle feels natural, even with people you don't know well."),
        "middle": ("With people I trust, eventually", "Vulnerability takes a track record of safety with someone first."),
        "right": ("Rarely, if ever", "You keep your struggles mostly private, even from people close to you."),
    },
    {
        "trait": "Work ethic",
        "question": "It's late, the task isn't due tomorrow, and you're tired. What actually happens?",
        "left": ("I keep going until it's properly done", "Stopping with something unfinished is harder for you than pushing through fatigue."),
        "middle": ("I do a bit more, then stop at a reasonable point", "You push somewhat past comfort, but you know your limit."),
        "right": ("I stop and pick it up tomorrow", "Rest wins over finishing when the deadline isn't real."),
    },
    {
        "trait": "Use of humor",
        "question": "Things get tense or sad in a group. What do you reach for?",
        "left": ("A joke to lighten the mood", "Humor is your instinctive tool for managing hard moments."),
        "middle": ("It depends on the room and the moment", "You read the situation before deciding whether humor helps or hurts."),
        "right": ("I stay serious and let the moment be what it is", "You let heaviness exist rather than trying to dissolve it."),
    },
    {
        "trait": "Need for control",
        "question": "You're part of a group project and someone else is steering it in a direction you wouldn't choose. What do you do?",
        "left": ("Step in and take the lead myself", "Letting outcomes ride on someone else's judgment is uncomfortable for you."),
        "middle": ("Voice my concerns, then let the group decide", "You want influence, but you're okay not having the final say."),
        "right": ("Let them lead — it's not worth the friction", "You're genuinely comfortable ceding control if it keeps things smooth."),
    },
    {
        "trait": "Comfort with uncertainty",
        "question": "You're waiting on news that could go either way, with no way to speed it up. How do you spend that time?",
        "left": ("Distracted and anxious until I know", "Not knowing is one of the harder states for you to sit in."),
        "middle": ("Mostly okay, with occasional worry creeping in", "You manage the uncertainty, though it doesn't leave you untouched."),
        "right": ("Genuinely at peace — I'll deal with it when it comes", "You can set down what you can't control with real ease."),
    },
    {
        "trait": "Self-criticism",
        "question": "You make a small, forgettable mistake in front of others. How long does it actually stay with you?",
        "left": ("It replays in my head for way longer than it should", "Your inner critic tends to hold onto small moments longer than they deserve."),
        "middle": ("It bothers me for a bit, then fades", "You feel it, but you don't let it overstay its welcome."),
        "right": ("Barely at all — everyone messes up sometimes", "Small mistakes roll off you without much residue."),
    },
    {
        "trait": "Generosity",
        "question": "You have something valuable — time, money, or skill — and someone in need asks for it. What's your instinct?",
        "left": ("Give generously, even if it costs me something real", "Giving comes before calculating what it costs you."),
        "middle": ("Give what feels sustainable for me", "You're generous within limits you've set to protect yourself too."),
        "right": ("Make sure I'm not being taken advantage of first", "You check the situation carefully before extending yourself."),
    },
    {
        "trait": "Patience",
        "question": "You're teaching or explaining something and the other person just isn't getting it. What's happening inside you?",
        "left": ("Genuine patience — I'll explain it as many times as it takes", "Slow understanding in others doesn't wear on you much."),
        "middle": ("Patience, with some effort to keep it up", "You stay patient, but it does take conscious effort."),
        "right": ("Frustration creeps in fairly fast", "Repetition and slow progress test your patience quickly."),
    },
    {
        "trait": "Honesty under pressure",
        "question": "Telling the full truth right now would hurt someone you care about, but a small omission would spare them. What do you do?",
        "left": ("Tell the whole truth — they deserve to know", "Honesty outranks comfort for you, even when it's painful."),
        "middle": ("Tell most of it, softened where I can", "You look for the version that's honest but kind."),
        "right": ("Leave out the part that would hurt", "Sparing someone's feelings can outweigh full disclosure for you."),
    },
    {
        "trait": "Need for recognition",
        "question": "You do something genuinely good and nobody notices. How does that actually sit with you?",
        "left": ("It really bothers me — I wanted it to be seen", "Being recognized is a real part of what makes effort feel worthwhile."),
        "middle": ("A little disappointing, but I know it mattered", "You'd like acknowledgment, but its absence doesn't undo the value for you."),
        "right": ("It doesn't matter — I didn't do it to be seen", "The act itself is the whole point; an audience isn't necessary."),
    },
    {
        "trait": "Coping with loss",
        "question": "When you lose something or someone important, what does your process usually look like?",
        "left": ("I need to talk it through with people", "Processing out loud, with others, is how grief moves through you."),
        "middle": ("A mix of talking and working through it alone", "You need both company and solitude at different points in the process."),
        "right": ("I need space and quiet to process alone", "Grief is something you move through privately, on your own terms."),
    },
    {
        "trait": "Learning style",
        "question": "You want to get good at something new. What's your first move?",
        "left": ("Just start doing it and learn from mistakes", "Hands-on trial and error is how things actually click for you."),
        "middle": ("A bit of study, then start practicing", "You want a foundation first, but you don't over-prepare."),
        "right": ("Study it thoroughly before I even begin", "You want to understand it well before risking a real attempt."),
    },
    {
        "trait": "Leadership style",
        "question": "You're put in charge of a group. What does your leadership actually look like?",
        "left": ("Hands-on — I set direction and stay closely involved", "You lead by staying close to the details and the decisions."),
        "middle": ("I set direction, then check in periodically", "You lead by balancing trust with regular oversight."),
        "right": ("I set the goal, then step back and let people run", "You lead by giving people room and trusting them to fill it."),
    },
    {
        "trait": "View on rules",
        "question": "You disagree with a rule that doesn't seem to make sense in your situation. What do you do?",
        "left": ("Follow it anyway — rules exist for a reason", "Structure and order matter to you more than your own exceptions."),
        "middle": ("Follow it, but push to have it reconsidered", "You respect the system while still trying to improve it."),
        "right": ("Bend or ignore it if it doesn't serve the actual goal", "Purpose matters more to you than the letter of a rule."),
    },
    {
        "trait": "Handling boredom",
        "question": "You have an unstructured hour with genuinely nothing to do. What happens?",
        "left": ("I get restless fast and need to find something", "Idle time feels uncomfortable to you almost immediately."),
        "middle": ("I enjoy it for a while, then start looking for something", "Some stillness is fine, but it has a natural limit for you."),
        "right": ("I could sit with it comfortably for a long time", "Doing nothing doesn't unsettle you the way it does most people."),
    },
    {
        "trait": "Receiving compliments",
        "question": "Someone genuinely compliments something about you. What's your internal reaction?",
        "left": ("I deflect or downplay it", "Praise tends to feel uncomfortable to fully accept."),
        "middle": ("I say thanks, but I don't fully believe it", "You accept it outwardly while quietly questioning it inside."),
        "right": ("I take it in and actually believe it", "You can receive praise without immediately arguing with it internally."),
    },
    {
        "trait": "Being wrong",
        "question": "You realize, mid-argument, that you're actually wrong. What happens next?",
        "left": ("I find it hard to admit in the moment", "Conceding in real time feels harder than it should, even when you know you're wrong."),
        "middle": ("I admit it, a little reluctantly", "You get there, though not always gracefully or instantly."),
        "right": ("I say so immediately, no issue", "Admitting a mistake doesn't threaten anything in you."),
    },
    {
        "trait": "Need for closure",
        "question": "A situation ends ambiguously, with no clear resolution or explanation. How does that sit with you?",
        "left": ("It really nags at me until I understand it", "Unresolved things occupy real space in your mind."),
        "middle": ("It bothers me for a while, then I let it go", "You'd like closure, but you can live without it eventually."),
        "right": ("I can leave it unresolved without much trouble", "Ambiguity doesn't demand resolution from you the way it does others."),
    },
    {
        "trait": "Attitude toward tradition",
        "question": "A family or cultural tradition doesn't really fit how you actually live. What do you do?",
        "left": ("Keep doing it — tradition matters on its own", "Continuity with the past holds real value for you, separate from utility."),
        "middle": ("Keep the parts that still mean something, drop the rest", "You treat tradition as something to selectively honor, not follow wholesale."),
        "right": ("Let it go if it doesn't serve me anymore", "Relevance to your actual life outweighs inherited obligation."),
    },
    {
        "trait": "Emotional recovery speed",
        "question": "Something upsets you significantly. How long before you're functionally back to normal?",
        "left": ("Pretty quickly — I process fast and move on", "Your emotional reset time is genuinely short."),
        "middle": ("A day or so, then it fades", "You need some time, but not an extended amount."),
        "right": ("It can linger for a long while", "Emotional weather tends to stay with you well after the event has passed."),
    },
    {
        "trait": "View of failure",
        "question": "You fail at something you genuinely tried hard at. What's the story you tell yourself?",
        "left": ("\"I'm just not good at this\"", "Failure tends to get read as information about your ability."),
        "middle": ("\"That attempt didn't work, but I'll adjust\"", "You separate the outcome from your worth fairly well."),
        "right": ("\"That's just data — try again differently\"", "Failure reads to you as neutral feedback, nothing more."),
    },
    {
        "trait": "Sense of purpose",
        "question": "What actually makes a day feel like it mattered, to you?",
        "left": ("Making measurable progress on something big", "Purpose, for you, is tied to forward motion toward something large."),
        "middle": ("A mix of small wins and moments with people", "Meaning shows up for you in a blend of progress and connection."),
        "right": ("A moment of real connection with someone", "For you, a day is meaningful because of who you shared it with."),
    },
    {
        "trait": "Handling jealousy",
        "question": "Someone close to you achieves something you've quietly wanted for yourself. What's your honest first feeling?",
        "left": ("A real pang of envy before anything else", "Comparison hits fast and honestly, before other feelings catch up."),
        "middle": ("A mix of happy for them and a little envious", "Both feelings arrive together, and you let them coexist."),
        "right": ("Genuinely happy for them, without much else", "Their success doesn't get filtered through your own scoreboard."),
    },
    {
        "trait": "Validation from work",
        "question": "You do excellent work but no one at work ever explicitly acknowledges it. How much does that cost you?",
        "left": ("A lot — I need to know my work is valued", "External acknowledgment is a real ingredient in your motivation."),
        "middle": ("Some — I'd like it, but I keep going regardless", "You'd welcome recognition, but you're not dependent on it."),
        "right": ("Very little — my own sense of doing it well is enough", "Your motivation runs almost entirely on internal standards."),
    },
    {
        "trait": "Adaptability",
        "question": "Plans change on you at the last minute, again. What's your real reaction?",
        "left": ("Frustration — I'd already committed to the original plan", "Sudden change costs you something real, not just an inconvenience."),
        "middle": ("A brief reset, then I adjust without much drama", "You absorb change with a short pause, not a spiral."),
        "right": ("Barely a blip — I go with whatever comes next", "New circumstances roll off you almost as fast as they arrive."),
    },
    {
        "trait": "Self-disclosure pace",
        "question": "With someone you're just getting to know, how fast do the real, personal topics come up?",
        "left": ("Pretty fast — I don't do much small talk", "You move toward depth quickly, sometimes before trust is fully built."),
        "middle": ("Gradually, as trust builds over time", "Depth follows a natural pace matched to how well you know someone."),
        "right": ("Very slowly — surface level for a long while first", "You keep real disclosure guarded until a relationship has proven itself."),
    },
]


if "know_yourself_queue" not in st.session_state:
    st.session_state.know_yourself_queue = []
if "know_yourself_answer" not in st.session_state:
    st.session_state.know_yourself_answer = None
if "know_yourself_history" not in st.session_state:
    st.session_state.know_yourself_history = []
if "know_yourself_round" not in st.session_state:
    st.session_state.know_yourself_round = 0


def new_question() -> None:
    if not st.session_state.know_yourself_queue:
        pool = list(range(len(QUESTIONS)))
        random.shuffle(pool)
        previous = st.session_state.get("know_yourself_index")
        if previous is not None and len(pool) > 1 and pool[0] == previous:
            pool[0], pool[1] = pool[1], pool[0]
        st.session_state.know_yourself_queue = pool
        st.session_state.know_yourself_round += 1

    st.session_state.know_yourself_index = st.session_state.know_yourself_queue.pop(0)
    st.session_state.know_yourself_answer = None


if "know_yourself_index" not in st.session_state:
    new_question()


st.title("Know Yourself")
st.write(
    "One question at a time. Each has three answers — two opposite extremes and a middle "
    "ground — meant to help you notice where you actually sit, not where you think you should."
)

seen_this_round = len(QUESTIONS) - len(st.session_state.know_yourself_queue)
st.caption(
    f"Round {st.session_state.know_yourself_round} · question {seen_this_round} of {len(QUESTIONS)} "
    "· every question appears once before any repeat"
)

st.divider()

current = QUESTIONS[st.session_state.know_yourself_index]

st.caption(f"Exploring: **{current['trait']}**")
st.subheader(current["question"])

left_col, middle_col, right_col = st.columns(3)
options = [("left", left_col), ("middle", middle_col), ("right", right_col)]

for key, col in options:
    label, _ = current[key]
    with col:
        if st.button(label, key=f"answer_{key}_{st.session_state.know_yourself_index}", width="stretch"):
            st.session_state.know_yourself_answer = key
            st.session_state.know_yourself_history.append(
                {
                    "trait": current["trait"],
                    "question": current["question"],
                    "choice": label,
                }
            )

if st.session_state.know_yourself_answer:
    chosen = current[st.session_state.know_yourself_answer]
    st.success(f"**{chosen[0]}** — {chosen[1]}")

st.button("Next question", on_click=new_question)

if st.session_state.know_yourself_history:
    st.divider()
    with st.expander(f"Your answers so far ({len(st.session_state.know_yourself_history)})"):
        for entry in reversed(st.session_state.know_yourself_history):
            st.markdown(f"- **{entry['trait']}**: {entry['question']} → *{entry['choice']}*")
