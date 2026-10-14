# You got nostalgic

> **Category:** Misc / Stego · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

> What a wonderful place, but how did I get here?

![The image](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/the-image.png)

## 🏁 Solution

### Initial analysis

We are given a PNG image. Let's run it through the usual steganography and metadata tools. I'm using [Aperi'Solve](https://github.com/Zeecka/AperiSolve) and [ExifTool](https://exiftool.org/):

![AperiSolve](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/aperisolve.png)

Filters, LSB and alpha channels don't reveal anything useful, so it's worth taking a closer look at the metadata and readable strings. Most of the metadata looks ordinary (dates, GPS coordinates of KubSTU and the White House), but among them there are some odd fields with seemingly meaningless content that look like parts of a single string. Each fragment starts with a digit — its sequence number:

```
1 FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G
2 (SKe^*=*0EMpMdpGijJd81A
3 @HkdoY?I9D=6ii,'#f
4 ]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

Drop the numbers and concatenate the fragments in order:

```
FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G(SKe^*=*0EMpMdpGijJd81A@HkdoY?I9D=6ii,'#f]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

### Decoding the string

The string looks like the output of some encoding. We try different options in CyberChef: ROT13, Base32, Base64 and so on. Base92 gives us meaningful text — a Google Drive link:

![CyberChef](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cyberchef.png)

```
https://drive.google.com/file/d/1s2sqWhknYnbWEhgggjvBzkrP90OU4x-j/view?usp=sharing
```

### The Minecraft instance

The link leads to an archive called `CL0S3.zip`. After downloading and extracting it, we see the folder structure of a Minecraft instance — `mods`, `coremods`, `resourcepacks`, `saves`, etc.:

![CL0S3 folder](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cl0s3-folder.png)

We don't know the game version, so we go back to the image metadata once more — the `Comment` field contains `version 1.12.2`:

![Hidden version](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/hidden-version.png)

Launch version 1.12.2 in any launcher, setting the extracted folder as the game directory (if there are mods in `mods`, you'll need Forge for 1.12.2). In the Singleplayer menu we see several saves:

![Saves](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/saves.png)

The world `here?` (folder `4lm0st_th3r3`) is the only one with a different name and preview. Let's join it:

![Uncompleted flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/uncompleted-flag.png)

We're greeted by a 10×5 grid of item frames, two of which already contain maps, and a book with some text:

![Book](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/book.png)

```
hello whoever got to
this point.
I hope you enjoy this
challenge.
Finish this grid if you
want a flag.
```

### Filling the grid

To figure out what the grid should be filled with, we take the item out of one of the filled frames — it's a map. It shows a fragment of the original image, meaning the picture from the challenge description has been cut up into maps.

Let's find out how custom images end up on maps in Minecraft in the first place:

![Google search](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/google-search.png)

*(Search query: "how to put your own photo on Minecraft maps". The AI overview explains that custom images are converted into map data files and placed in the world's `data` folder, then obtained in-game with the `/give` command.)*

This gives us two hints:

1. Map data is stored in `.minecraft/saves/<World_name>/data` in files named `map_<number>.dat`. In our case that's `saves/4lm0st_th3r3/data`.
2. Any map can be given to yourself by its number with the command:

```
/give @p filled_map 1 <map_number>
```

This syntax works specifically in 1.12.2 (the map number is passed as the data value). Starting with 1.13 the command looks different: `/give @p filled_map{map:<number>}` — one more reason why finding the correct version mattered.

The `data` folder contains 65 maps (`map_0.dat` … `map_64.dat`), while the grid has only 50 frames. So some of the maps are decoys. For example, one of them is the KubSTU logo:

![KubSTU logo](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/kubstu-logo.png)

From here, there are two ways to go.

**Option 1 (the intended one).** Give yourself the maps one by one and place them in the frames. The image is assembled from maps numbered 0–49.

**Option 2 (no manual placement).** Each `map_N.dat` is a gzip-compressed NBT file whose `data.colors` field holds an array of 128×128 bytes — indices into the Minecraft map color palette. You can read the files with a script (e.g. Python + `nbtlib`), convert the indices to RGB using the 1.12 palette, and stitch the maps into a single image outside the game.

## Flag

Once maps 0–49 are placed correctly in the frames, the flag appears in the picture:

![Flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/flag.png)

**Flag:** `KubSTU{n0st4lg14_1s_h3r3}`
