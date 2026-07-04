# The Box on My Desk, Rebuilt in Streamlit

There's always a box on my desk. Not for work — for the other stuff. It's been there since I was a kid: a container that only ever grows, gets quietly recycled sometimes, but never "cleaned up" without my sign-off. Most of what ends up in it is physics-adjacent — things tied to gravity, light, magnets, kinetic energy that's stored up and waiting, you never quite know when or how it'll release. I'll admit I lean a little spiritual about it too: to me, spirituality is just physics with more unknowns than answers.

A few weeks ago I finally decided to deal with it. Not clean it out in the boring way — digitize it. Simulate the pieces in code, give the physical ones away, and let the box itself finally shrink. That plan became **Kinetic Playground**, a Streamlit app that's still very much in progress. Here's everywhere it's gotten to so far.

## Page one: the spirograph that ate my afternoon

First build was a **Spirograph Studio** — animated gears drawing curves, with linked rotating objects, live pen-color changes mid-draw, and one-click JPG export. It started as "let me simulate one spirograph" and, predictably, spiraled (sorry) into multiple pieces, shapes, and color sets before I forced myself to stop and go finish the Jira ticket that was actually due that day.

## Page two: order out of chaos

Next morning, the first thing on my mind was the **Galton board** — that wall of pegs where dropped balls bounce randomly left or right and somehow still pile up into a clean bell curve. It's one of those things that's fascinated me forever: pure randomness at the ball level, pure order at the aggregate level. The page lets you adjust rows, bias, drop speed, and colors, and watches a live histogram converge in real time.

## Page three: the sand art I own two of, physically

The third page is my favorite because it replaces something I actually own — twice. **Sealed Sand Art** simulates those circular sand-art toys people use as fidget/therapy pieces: colored sand grains, a set amount of liquid and air, adjustable gravity, per-grain weight differences, bubble buoyancy, and a seeded random initial state so every session starts from a reproducible mess. I'd wanted to buy a few of these as gifts for people who deal with the same restlessness I do — now I can just send a link instead of a package.

## Page four: the Fourier obsession, twenty-some years running

This one goes back furthest. On my first computer — a Sinclair Spectrum, age 12 — I was obsessed with sin and cos: how two waves with different phase and frequency stack into something beautiful. University Fourier analysis was the payoff of that obsession, and it hasn't worn off. **Fourier Transform Lab** builds a random signal from a handful of hidden sine components, runs an FFT to recover their frequencies, amplitudes, and phases, and reconstructs the waveform so you can watch the pieces add back up into the whole.

## Page five: no object at all, just your hands

The newest page needed nothing from the box, because there was nothing physical to digitize — just a webcam and a hand. **Camera Games** turns your live camera feed into a real-time toy: point your index finger at the screen and a hand-tracking model reads the gesture, feeding your fingertip position into a small ripple simulation that distorts the video like water. Switch modes and the same feed gets mirrored into a spinning, symmetrical **kaleidoscope** instead. Snapshot button included, because some ripples are worth keeping. It's the first page where the "toy" is just you, moving in front of a camera — kinetic energy with no physical toy required.

## So did the box get any lighter?

Honestly — no, and I've made my peace with that. I started this thinking digitizing the collection would let me finally let go of it: fewer boxes, less clutter, a tidy desk. Five pages in, what actually happened is the opposite. Building each simulation made me pay closer attention to the real thing it came from — the actual weight of the sand, the actual click of the spirograph gears — and that made we want to keep the box, not empty it. I do give pieces away now, when I duplicate one in code first. But the box itself isn't going anywhere. It's still there, still growing, still not fully cleaned up without my sign-off.

*— Kinetic Playground is open source and still growing. Built with Streamlit, HTML5 canvas, MediaPipe hand-tracking, and numpy/FFT under the hood.*
