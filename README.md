<h1 align="center">🎁 Ruby's Gifts</h1>

<p align="center"><b>Find the perfect gift by answering 8 slightly nosy questions about someone.</b></p>

<p align="center">
  <a href="https://rubysgifts.kks.im"><b>Live at rubysgifts.kks.im</b></a>
</p>

![Ruby's Gifts landing page](landing.png)

Stuck on what to gift someone? Ruby's Gifts turns "I genuinely have no idea what to get them" into three specific, thoughtful gift ideas. You answer eight quick questions about the person, including what they would absolutely hate and what they never stop complaining about, and the AI hands back real suggestions, each with a line for how to give it and the reaction to expect.

## Why it exists

Gift-guide listicles are generic and gift quizzes are boring. The genuinely hard part of gifting is not browsing, it is describing the actual human you are shopping for. So the whole app is built around making that description fun instead of tedious.

## The 8 questions

Every question comes with a searchable grid of 50+ tappable chips (each with an icon), so you can click to answer fast or type your own:

1. What do you call them? (nicknames, pet names)
2. What is your relationship?
3. What have you already gifted them?
4. What will they absolutely hate?
5. What do they keep complaining about?
6. How would you complain about them to a friend?
7. What is your budget?
8. Any other limitations? (allergies, eco-friendly, portable, and so on)

Questions 4 and 5 are the secret sauce. Knowing what someone dislikes narrows a gift down faster than knowing what they like.

## How it works

1. **Answer with chips or your own words.** Multi-select, searchable, mobile-friendly. Your selections sync into an editable text box so you can fine-tune.
2. **The AI reads all eight answers together** and reasons about who this person actually is.
3. **You get 3 gift ideas back,** each as a card with the idea, a starter for how to present it, and the reaction you can expect.

## What you get

- **8-question chip-based flow** that plays more like a game than a form
- **3 tailored gift ideas**, not a generic top-10 list
- **Relevant images** pulled in to illustrate each idea
- **Bright, playful design** (orange, rounded, lowercase, Playfair Display + Plus Jakarta Sans)

## Under the hood

Flask backend with an OpenAI-powered recommendation engine, a vanilla HTML / CSS / JS frontend, Phosphor Icons on the chips, and an image-search layer to picture each gift. Deployed on Vercel.

## Status

Live at [rubysgifts.kks.im](https://rubysgifts.kks.im). Try it on someone you know.
