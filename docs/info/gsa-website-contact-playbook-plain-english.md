# GSA Website Contact — Plain-English Playbook

> **For the owner. No jargon. This is the "what can we actually do" answer.**
> Technical companion (for agents) lives at:
> `docs/info/gsa-website-contact-technical-reference.md`

---

## 🏆 WE TESTED IT FOR REAL — IT WORKS (2026-06-13)

This isn't theory anymore. We ran the whole thing through the actual GSA software:
built a spreadsheet of 3 businesses, imported it, wrote one message with blanks,
and hit send. GSA filled in Joe's Plumbing's real name, what they were missing,
their review count, and their custom link — then **actually submitted it to a live
form**, which received it word-for-word. GSA even says it in its own screen:
*"You can also use any headers from CSV files that you import."* **Done. Confirmed. Working.**

---

## The Bottom Line (read this first)

**Your plan works. The agent who told you "you can only use one placeholder" was wrong.**

You CAN send a different, fully customized message to every single business, using
the data you scraped about them. That is exactly what GSA Website Contact is built
to do. I verified it against GSA's own official documentation — not opinion, not a
guess. Your friend who said "you can make up your own columns" was right.

So: **the whole project is NOT bombed. It's fully alive.**

---

## How It Actually Works (the simple version)

Think of it like a mail merge — the same thing that lets you send "Dear [First Name]"
letters, except it posts through each website's "Contact Us" form instead of email.

1. You make a **spreadsheet**. Each row = one business you're targeting.
2. The columns are whatever facts you want: the business name, their website, what
   they're missing, their review count, the link to the preview site you built them, etc.
   **You name the columns whatever you want.** There's no limit on how many.
3. You write **one message template** with blanks in it, like:
   > Hi **{business name}**, I noticed you're missing **{missing thing}**.
   > I built you a free preview: **{preview link}**
4. GSA fills in each blank from that row's spreadsheet data and submits it through
   the business's contact form.
5. Every business gets a message that's truly about *them*. That's what makes them
   open it and go "wait, how do they know all this about me?" — your original idea, intact.

The "blanks" are just your column names wrapped in percent signs. A column called
`business_name` becomes `%business_name%` in the message. That's the entire trick.

---

## What We CAN Do ✅

- ✅ Send a **unique, personalized message to every business** based on your scraped data.
- ✅ Use **as many custom fields as we want** (name, city, missing citations,
  competitors, review count, the preview-site link, your audit reasons — all of it).
- ✅ Put the **link to their preview landing page** in the message, personalized per business.
- ✅ **Spin** the wording so no two messages look identical (helps avoid spam filters).
- ✅ Let GSA **solve CAPTCHAs** automatically (with the Captcha Breaker + XEvil add-ons),
  so most forms with a CAPTCHA are still reachable.
- ✅ Pre-screen sites first so we only send to forms GSA can actually deliver to,
  and shove the rest into a cold-email pile.

## What We CANNOT Do ❌

- ❌ **No fancy formatting.** Contact forms only take plain text. No bold, no colors,
  no images, no "Click Here" buttons.
- ❌ **The link can't be a dressed-up button.** It goes in as the plain web address
  (like `https://previews.site/joes-plumbing`). That's fine — people can still click
  or copy it — it just won't be a styled link. **Keep the links short and clean** so
  they look good as plain text.
- ❌ **Can't send to a site with no real form**, or one hidden behind a heavy
  security wall, or one using an embedded third-party form (those get filtered out
  and sent to the cold-email list instead).
- ❌ **No read-receipts or click-tracking inside the form text.** If we want to know
  who clicked, we bake a unique link into each business's preview URL (which we
  already do), not into the message formatting.

---

## The Two Big Gotchas (so we don't waste a day)

1. **Every value in the spreadsheet must be wrapped in quotation marks.**
   `"Joe's Plumbing"`, not `Joe's Plumbing`. If you save a normal CSV out of Excel,
   it does NOT add the quotes, and GSA silently ignores your custom data. Our scripts
   will save it correctly (with quotes) automatically — but if you ever hand-make a
   file in Excel, this is the #1 thing that breaks it.

2. **After you import, you won't SEE the extra columns in GSA's list. That's normal —
   not a bug.** The data is still there. To check it, **hover your mouse over a URL**
   and a little pop-up shows the data attached to it. Don't panic when the columns
   "disappear" — they're hiding on the hover tooltip on purpose.

---

## The 10-Minute Proof (before any big send)

We can prove the whole thing works in ten minutes, with zero risk:

1. Make a tiny 3-row test spreadsheet (business name + a fake "missing thing" + a
   special test web address that records whatever it receives).
2. Write the message with the blanks in it.
3. Run it.
4. Look at what the test address received — you'll see three *different* messages,
   each filled in with its own row's data.

When that shows three correctly-personalized messages, we're locked and can scale up.

---

## Why You Kept Getting Half-Right Answers

The confusion came from there being **two ways** to load targets into GSA:

- A **basic list** (just web addresses, no extra data) — simple, but generic.
- A **smart spreadsheet** (web address PLUS all your custom columns) — this is ours.

The earlier agent only knew about the basic list and assumed that's all there was.
The smart-spreadsheet method is the documented, intended way to do exactly what you
wanted. We use the smart spreadsheet. Case closed.

---

*Verified against GSA's official documentation, June 13, 2026. If anyone ever tells
you again that custom personalization isn't possible, point them here and to the
technical reference — the GSA docs themselves spell out the `%ColumnName%` method.*
