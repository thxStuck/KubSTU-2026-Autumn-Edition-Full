# How to make a local happy

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

To make a Krasnodar local happy, so little is needed — just close one street. They used to do it every weekend, but now only on special occasions. Find this street and the dates when it was closed for the last time.

Flag format: `KubSTU{StreetName_dd.mm-dd.mm}`
Example: `KubSTU{Severnaya_31.12-07.01}`

## 🏁 Solution

### Step 1. Finding the street

"Close a street so that people are happy" means making it pedestrian. We search:

```
пешеходная улица Краснодар
```

![promenade_st.png](../../../assets/OSINT/How%20to%20make%20a%20local%20happy/promenade_st.png)

The very first results point to **Krasnaya St** — the central street of the city. For many years its stretch from Pushkinskaya Square to Dlinnaya was closed on weekends, and the residents loved it very much.

In 2020, because of the pandemic, the practice was suspended, and in 2022 the anti-terrorism commission banned the closures for good. Since then Krasnaya is closed only for individual events. It is precisely this "only on special occasions" that is meant in the task.

> Chapaeva St (the "Krasnodar Arbat") is also pedestrian on weekends, but it is still closed every week. That is why it does not fit the task.

### Step 2. Looking for the last closure

```
улица Красная перекрыта
```

![marathon.png](../../../assets/OSINT/How%20to%20make%20a%20local%20happy/marathon.png)

Fresh news (BFM Kuban, 93.ru): for City Day a run was held on Krasnaya, and traffic on the stretch from Postovaya to Kalinina was closed **from 22:00 on September 26 to 14:00 on September 27**.

### Step 3. Assembling the flag

```
KubSTU{Krasnaya_26.09-27.09}
```

The Cyrillic variant is also accepted: `KubSTU{Красная_26.09-27.09}`.

**Flag:** `KubSTU{Krasnaya_26.09-27.09}` · `KubSTU{Красная_26.09-27.09}`
