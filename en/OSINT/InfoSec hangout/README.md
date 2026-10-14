# InfoSec hangout

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn
> **Difficulty:** Medium

## 📌 Task

This summer our team again visited a well-known Russian InfoSec event. There are many photos from the trip, but not all the places stuck in memory. Help identify the venue in this shot and write the flag in the format `KubSTU{Name}`.

![task.jpg](../../../assets/OSINT/InfoSec%20hangout/task.jpg)

**Files:** [task.jpg](../../../assets/OSINT/InfoSec%20hangout/task.jpg)

## 🏁 Solution

1. In the photo we see a passport with a plane ticket. We can make the assumption that this is an airport.

2. We also see the date and time of the shot in the corner. By the date, in Russia we have only one major event — OFFZONE. We realize the photo was taken the day after Offzone, so it is a Moscow airport.

3. Then here and there we look through the flight schedules to Krasnodar and see delays at Vnukovo; it is not all obvious there, so you can also brute-force it.

4. All that is left is to look through photos of all the venues inside Vnukovo and find such a floor and red chairs.

![Venue interior](https://avatars.mds.yandex.net/get-altay/13604236/2a00000194ace6bcc4a8452a21012304cdc4/L_height)

**Flag:** `KubSTU{Шоколадница}`
