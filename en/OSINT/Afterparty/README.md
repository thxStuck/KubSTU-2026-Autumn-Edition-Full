# Afterparty

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

After the spring KubSTU CTF ended, we went out to relax and wandered into a certain venue. It's really cool there — we had a great time playing Uno and, along the way, generated material for the autumn CTF.

I think we'll be back there more than once :)

![cocktail.jpg](../../../assets/OSINT/Afterparty/cocktail.jpg)

Find the venue where we hung out and name my cocktail.

Flag format: `KubSTU{VenueName_CocktailName}`

**Files:** [cocktail.jpg](../../../assets/OSINT/Afterparty/cocktail.jpg)

## 🏁 Solution

### Step 1. Breaking the photo down into clues

Right away we write down everything we can latch onto, not just the glass:
- **A tulip glass and a custom highball.** The shape is typical of signature cocktails, not of a standard bar/pub.
- **A flame in the reflection on the glass.** That means there is something fire-like behind (a fireplace or a TV).
- **A hookah bowl in the background.** A rounded vessel with liquid on a characteristic stand — the silhouette reads clearly. The venue is almost certainly a hookah lounge or a hookah bar.
- **A red leather object on the right.** Looks like a menu in a leather cover (confirmed later).
- **Light and background.** Warm low light, wooden bar furniture — a lounge format.

The city can be pinned down from context: KubSTU + Information Security = **Krasnodar**.

### Step 2. Narrowing the geography

We google "bar street in Krasnodar" / "restaurant street in Krasnodar". Consistently, **Krasnaya St** and the parallel **Rashpilevskaya** and **Krasnoarmeyskaya** in the center come up.

![bar_rest_mile.png](../../../assets/OSINT/Afterparty/bar_rest_mile.png)

There are 300+ venues in this zone — too many to brute-force, so we filter by the clues from Step 1.

### Step 3. Hard filtering

Out of all the venues in the center we keep only those that are simultaneously:
1. **Hookah lounges / bars with hookah** (the clue — the bowl in the background).
2. **Make signature cocktails.**
3. **Premium segment** (judging by the glass and the styling).

After this filter ~10–15 candidates remain. At this point you can go two ways:
- **Reverse image search**
- **Direct search** on 2GIS / Yandex Maps

### Step 4. Confirming the venue

We run the candidates through review photo galleries and official content, looking for detail matches with the original photo:

| Clue in the original photo | Confirmation in the venue's gallery |
|---|---|
| Hookah bowl, stand | The same type of hookah in other photos |
| Red leather object | Menu in a red leather cover |
| Wooden countertop | Bar furniture of the same style |
| Tiki / ceramic tableware | Visible in other photos from the venue |

The matches converge on one place: **DeepSmoke, Krasnoarmeyskaya St, 68.**

![cocktail_writeup.png](../../../assets/OSINT/Afterparty/cocktail_writeup.png)

### Step 5. Identifying the cocktail

We open the DeepSmoke cocktail menu (the menu from the Yandex Maps photos) and look for a non-alcoholic cocktail in a similar glass.

Match: **"Tanzania"** (non-alcoholic) — Japanese non-alcoholic gin, mango tonic, lime juice, coconut syrup.

![tanzania.webp](../../../assets/OSINT/Afterparty/tanzania.webp)

The glass shape and the garnish skewer match the original photo — this is it.

**Flag:** `KubSTU{DeepSmoke_Tanzania}` · `KubSTU{DeepSmoke_Танзания}`
