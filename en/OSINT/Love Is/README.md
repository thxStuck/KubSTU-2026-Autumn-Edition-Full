# Love Is

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

Love is when the shawarma guy lovingly takes the meat off the skewer and doesn't skimp on the filling at the kiosk near the university. And then you take it and... it smells of smoke and melts in your mouth. God, how good it is.
Find the shawarma kiosk where we always get it. In the flag, specify the phone number from the kiosk's facade.
Flag format — `KubSTU{+79xxxxxxxxx}`

## 🏁 Solution

### Step 1 — Determining the search area

The description itself doesn't narrow the search area much, but we can look at which buildings the university has.
https://kubstu.ru/s-28 — the list of all buildings.

![acad_buildings_list.png](../../../assets/OSINT/Love%20Is/acad_buildings_list.png)

Buildings A, B, V and G stand together on the park grounds, so we treat them as one building. Buildings K and S stand apart from the ones listed above — we consider them separately.
First we determine the purpose of each building (which programs can be found there). For this we turn to the page with their list, the maps and the [class schedule](https://elkaf.kubstu.ru/timetable/default/time-table-student).

![colledge.png](../../../assets/OSINT/Love%20Is/colledge.png)

![stroifak.png](../../../assets/OSINT/Love%20Is/stroifak.png)

![neftigaz.png](../../../assets/OSINT/Love%20Is/neftigaz.png)

From the sources above we conclude that buildings V (college), B (construction faculty) and S (oil and gas) are not relevant for InfoSec students. We can be found in buildings A (main), G (because of the lecture halls) and K (the building that houses the department).

---
### Step 2 — Exploring the vicinity of the buildings

Based on this, we should check all shawarma kiosks within a radius of 200–300 meters of the relevant buildings (Why exactly this distance? Because it is optimal. During a 30-minute break we manage to walk there at a leisurely pace, place an order, wait for it and, in the end, enjoy this creation of eastern cuisine).

Let's start by checking building K:

![k_shawarma_1.png](../../../assets/OSINT/Love%20Is/k_shawarma_1.png)

![k_shawarma_2.png](../../../assets/OSINT/Love%20Is/k_shawarma_2.png)

Here we have only 2 candidates and both are from the same chain.

![not_larek.webp](../../../assets/OSINT/Love%20Is/not_larek.webp)

![not_larek2.webp](../../../assets/OSINT/Love%20Is/not_larek2.webp)

These don't look much like kiosks, so we can forget about them.

Now let's move on to Moskovskaya St, where we already have 6 candidates:

![m_shwarma_1.png](../../../assets/OSINT/Love%20Is/m_shwarma_1.png)

![m_shwarma_2.png](../../../assets/OSINT/Love%20Is/m_shwarma_2.png)

![m_shwarma_3.png](../../../assets/OSINT/Love%20Is/m_shwarma_3.png)

![m_shwarma_4.png](../../../assets/OSINT/Love%20Is/m_shwarma_4.png)

![m_shwarma_5.png](../../../assets/OSINT/Love%20Is/m_shwarma_5.png)

![m_shwarma_6.png](../../../assets/OSINT/Love%20Is/m_shwarma_6.png)

![m_shwarma_7.png](../../../assets/OSINT/Love%20Is/m_shwarma_7.png)

There are more points here, we'll check them.

---
### Step 3 — The finale

From the previous step we ended up with quite a lot of points, however our search circle has narrowed as much as possible.

We check each one in turn.

![lavashok.webp](../../../assets/OSINT/Love%20Is/lavashok.webp)

This one is a miss — it doesn't look like a kiosk, and even if it were one, there's no number on the facade.

![kabul.webp](../../../assets/OSINT/Love%20Is/kabul.webp)

Also a miss — this is actually a chaikhana (teahouse).

![loveis.webp](../../../assets/OSINT/Love%20Is/loveis.webp)

Well, there's something here. There's a chimney, which means we can assume there's a grill inside, there's a number on the facade, and the name of the kiosk is suspiciously similar to the name of the task. For now let's set this point aside and check the rest.

![dolina.webp](../../../assets/OSINT/Love%20Is/dolina.webp)

This is a kiosk, but there's no grill and no number here — a miss.

![chilli.webp](../../../assets/OSINT/Love%20Is/chilli.webp)

Same as the previous point — a miss.

![prozharka.webp](../../../assets/OSINT/Love%20Is/prozharka.webp)

This isn't a kiosk at all — a miss.

![uni.webp](../../../assets/OSINT/Love%20Is/uni.webp)

Here we have a cafe, so we don't touch it.

From all the points listed above we can conclude that only one fits the description — Love Is. We return to it and take the phone from the facade — +79182524547.

Hooray, the flag is found — `KubSTU{+79182524547}`

**Flag:** `KubSTU{+79182524547}`
