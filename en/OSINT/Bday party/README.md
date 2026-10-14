# Bday party

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · tg: [@kunstl3r](https://t.me/kunstl3r) · Source: https://ctftime.org/writeup/41124 (community writeup from CTFtime)

## 📌 Task

We are given a photo. By its metadata it was taken during the day, when the sun is at its zenith. The task description notes that the mountains are within arm's reach.

## 🏁 Solution

From the terrain we can say unambiguously that this is a suburb — since the task authors are from Krasnodar, it is the area around the city. And since the description says the mountains are within arm's reach, we build the following list of candidate settlements: the stanitsas of Smolenskaya, Krepostnaya, Grigoryevskaya, Stavropolskaya, and Kaluzhskaya.

The stanitsas of Krepostnaya, Stavropolskaya and Grigoryevskaya are ruled out by the landscape (they lie in the lowlands).

We start examining the maps of the stanitsas of Smolenskaya and Kaluzhskaya in satellite mode (the main anchors from the attached photo are: power lines, a pool, three houses with red tile roofs and one house with a grey roof next to them).

Sooner or later we stumble upon "Sanatoriy dlya dushi" ("Sanatorium for the Soul") on Yesenina street.

**Flag:** `KubSTU{44.7822, 38.7781}`
