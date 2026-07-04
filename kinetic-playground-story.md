# The Box on My Desk, Rebuilt in Streamlit

I've kept a box on my desk since I was a kid. Not work stuff — the other stuff. It only grows. Sometimes I recycle a piece, but nobody touches it without my say-so.

Most of what's in there is physics-flavored. Gravity, light, magnets, things that store up energy and let it go on their own schedule. I'll admit I get a little spiritual about that. To me spirituality is just physics with more unknowns.

A few weeks ago I decided to finally deal with the box. Digitize the pieces, give the real ones away, let the box actually shrink for once. That's how **Kinetic Playground** started. Still a work in progress. Here's what's in it so far.

## Spirograph Studio

First page. Animated gears drawing curves, rotating objects linked together, pen color you can change mid-draw, export to JPG. I meant to build one spirograph. Instead I got shapes, colors, multiple linked pieces — and had to force myself to stop and go finish a Jira ticket that was due that day.

## Galton Board Works

Next morning I couldn't stop thinking about the Galton board. Balls drop through a wall of pegs, bounce randomly left or right, and somehow still pile up into a clean bell curve every time. Random at the ball level, ordered at the pile level. This page lets you tune rows, bias, speed, colors, and watch the histogram settle in real time.

## Sealed Sand Art

This one's personal — I own two of the real thing. Sand, liquid, air, and gravity settling into a new pattern every time you flip it. The app lets you set sand types, weight, bubbles, gravity, and a seed so a session can be reproduced exactly. I used to want to buy these as gifts for people who deal with the same restlessness I do. Now I just send a link.

## Fourier Transform Lab

The oldest one. I was 12, on a Sinclair Spectrum, obsessed with how sin and cos waves stack into something new. Fourier analysis in university was the payoff of that obsession, and it never wore off. This page builds a random signal from hidden sine waves, runs an FFT to pull the frequencies back out, and shows the pieces adding back up into the whole.

## Camera Games

The newest page didn't need anything from the box, because there was nothing to digitize — just a camera and a hand. Point your index finger at the screen, a hand-tracking model reads it, and your fingertip makes ripples across the video feed like it's water. Switch modes and the same feed spins into a kaleidoscope instead. There's a snapshot button too. First page where the toy is just you.

## So, is the box any lighter?

No. I started this to get rid of it. Instead, building each simulation made me pay more attention to the real object it came from — the actual weight of the sand, the actual click of spirograph gears. That made me want to keep the box more, not less. I do give pieces away now, once I've copied them into code. But the box itself isn't going anywhere.

*— Kinetic Playground is open source and still growing. Built with Streamlit, HTML5 canvas, MediaPipe hand-tracking, and numpy/FFT.*

**P.S.** — this app keeps changing shape, so whatever's written above may already be a step behind. For the current version: [kinetic-playground.streamlit.app](https://kinetic-playground.streamlit.app/).
