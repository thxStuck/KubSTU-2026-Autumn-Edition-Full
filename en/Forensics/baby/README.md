# baby

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

We are given an image of a compromised Windows host. We need to reconstruct the course of the incident and assemble the flag.

## 🏁 Solution

The user followed a browser link to the file InvoiceViewer.exe and saved it in Downloads. At 09:16:02 UTC, execution traces point to this file being processed. Then an autostart item OneDriveUpdate.vbs was created in the user's profile, which documents a reference to an object with the masquerading name RuntimeBroker.exe outside the legitimate system directory. In a hidden state in ProgramData, a configuration remained with the endpoint 198.51.100.23:4444; this address belongs to the TEST-NET-2 range reserved for documentation and is not real infrastructure within this training case [1]. Finally, the Recycle Bin retained the deletion metadata of the masquerading object.

1. The user downloaded InvoiceViewer.exe from http://198.51.100[.]23:8080/InvoiceViewer.exe.
   - The evidence is artifact data: `C/Users/Alex/Downloads/InvoiceViewer.exe`; `C/Users/Alex/AppData/Local/Google/Chrome/User Data/Default/History`
2. The file was first launched/processed on 2026-06-11 09:16:02 UTC.
   - According to Windows optimization files: `C/Windows/Prefetch/INVOICEVIEWER.EXE-8B96A1D2.pf.txt`; `C/Users/Alex/AppData/Local/Temp/invoice_render.log`; `ConsoleHost_history.txt`
3. The persistence mechanism is the file OneDriveUpdate.vbs in the user's Startup directory. It references `%APPDATA%\Microsoft\OneDrive\RuntimeBroker.exe`.
   - The evidence is a common persistence tactic: `C/Users/Alex/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/OneDriveUpdate.vbs`
4. The name RuntimeBroker.exe masquerades as a regular component, but the object is located in the user profile, not in `C:\Windows\System32`.
   - `C/Users/Alex/AppData/Roaming/Microsoft/OneDrive/RuntimeBroker.exe`
5. The residual configuration trace recorded 198.51.100.23:4444.
   - `C/ProgramData/.cache/agent_state.dat`
6. The attempt to delete traces is shown by the Recycle Bin meta-artifact: the original path points to RuntimeBroker.exe, deletion time — 09:19:45 UTC.
   - `C/$Recycle.Bin/S-1-5-21-1961432191-301355982-4121230938-1001/$I8O5VA5.exe.txt`

As a result, we have this flag:

**Flag:** `KubSTU{InvoiceViewer.exe|198.51.100.23:4444|OneDriveUpdate.vbs}`
