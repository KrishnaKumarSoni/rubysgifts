<h1 align="center">Ruby's Gifts</h1>

<p align="center"><b>Find the perfect gift by answering 8 slightly nosy questions about someone.</b></p>

<p align="center">
  <code>● Live</code> &nbsp;·&nbsp; <a href="https://rubysgifts.vercel.app"><b>rubysgifts.vercel.app</b></a> &nbsp;·&nbsp; Flask · OpenAI
</p>

![Ruby's Gifts landing page](landing.png)

> The trick: it asks what they would *hate* and what they *complain about*. Knowing someone's dislikes narrows a gift down faster than knowing their likes.

Stuck on what to gift someone? Answer eight quick questions about the person and the AI hands back three specific, thoughtful gift ideas, each with a line for how to give it and the reaction to expect.

## Why it exists

Gift-guide listicles are generic and gift quizzes are boring. The genuinely hard part of gifting is describing the actual human you are shopping for. So the whole app is built to make that description fast and fun.

## How it works

```
Answer 8 questions (tap chips)  →  AI reads them together  →  3 gift cards back
```

| Step | What happens |
|------|--------------|
| **1. Answer** | Each question has a searchable grid of 50+ tappable chips. Multi-select or type your own; selections sync to an editable box. |
| **2. Reason** | The AI reads all eight answers together to model who this person actually is. |
| **3. Reveal** | Three gift ideas come back, each with the idea, a starter for how to present it, and the reaction to expect. |

## The 8 questions

| # | Question |
|---|----------|
| 1 | What do you call them? (nicknames, pet names) |
| 2 | What is your relationship? |
| 3 | What have you already gifted them? |
| 4 | **What will they absolutely hate?** |
| 5 | **What do they keep complaining about?** |
| 6 | How would you complain about them to a friend? |
| 7 | What is your budget? |
| 8 | Any other limitations? (allergies, eco-friendly, portable) |

## Under the hood

Flask · OpenAI recommendation engine · vanilla HTML/CSS/JS · Phosphor Icons on the chips · an image-search layer to picture each gift · deployed on Vercel. Design is bright and playful: orange, rounded, lowercase, Playfair Display + Plus Jakarta Sans.
