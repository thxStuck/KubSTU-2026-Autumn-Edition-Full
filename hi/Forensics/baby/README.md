# baby

> **श्रेणी:** Forensics · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

हमें एक समझौता (compromise) किए गए Windows होस्ट की इमेज दी गई है। घटना (incident) का क्रम पुनर्निर्मित करके फ़्लैग जोड़ना है।

## 🏁 समाधान

उपयोगकर्ता ने ब्राउज़र में InvoiceViewer.exe फ़ाइल के लिंक पर क्लिक किया और उसे Downloads में सहेजा। 09:16:02 UTC पर निष्पादन (execution) के निशान इस फ़ाइल के संसाधित होने की ओर इशारा करते हैं। फिर उपयोगकर्ता की प्रोफ़ाइल में एक ऑटोस्टार्ट तत्व OneDriveUpdate.vbs बनाया गया, जो वैध सिस्टम निर्देशिका के बाहर, मास्किंग नाम RuntimeBroker.exe वाले एक ऑब्जेक्ट के संदर्भ को दर्ज करता है। ProgramData में छिपी अवस्था में एंडपॉइंट 198.51.100.23:4444 वाला एक कॉन्फ़िगरेशन बचा रहा; यह पता दस्तावेज़ीकरण के लिए आरक्षित TEST-NET-2 रेंज का है और इस प्रशिक्षण केस में वास्तविक इंफ़्रास्ट्रक्चर नहीं है [1]। अंत में, रीसायकल बिन में मास्किंग ऑब्जेक्ट के विलोपन का मेटाडेटा सहेजा गया है।

1. उपयोगकर्ता ने InvoiceViewer.exe को http://198.51.100[.]23:8080/InvoiceViewer.exe से डाउनलोड किया।
   - प्रमाण — आर्टिफ़ैक्ट डेटा: `C/Users/Alex/Downloads/InvoiceViewer.exe`; `C/Users/Alex/AppData/Local/Google/Chrome/User Data/Default/History`
2. फ़ाइल पहली बार 2026-06-11 09:16:02 UTC पर चलाई/संसाधित की गई।
   - Windows ऑप्टिमाइज़ेशन फ़ाइलों के अनुसार: `C/Windows/Prefetch/INVOICEVIEWER.EXE-8B96A1D2.pf.txt`; `C/Users/Alex/AppData/Local/Temp/invoice_render.log`; `ConsoleHost_history.txt`
3. दृढ़ीकरण (persistence) तंत्र — उपयोगकर्ता की Startup निर्देशिका में OneDriveUpdate.vbs फ़ाइल। यह `%APPDATA%\Microsoft\OneDrive\RuntimeBroker.exe` का संदर्भ देती है।
   - प्रमाण — एक सामान्य दृढ़ीकरण रणनीति: `C/Users/Alex/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/OneDriveUpdate.vbs`
4. नाम RuntimeBroker.exe एक नियमित घटक के रूप में छद्म रूप धारण करता है, पर ऑब्जेक्ट उपयोगकर्ता प्रोफ़ाइल में स्थित है, न कि `C:\Windows\System32` में।
   - `C/Users/Alex/AppData/Roaming/Microsoft/OneDrive/RuntimeBroker.exe`
5. अवशिष्ट कॉन्फ़िगरेशन निशान में 198.51.100.23:4444 दर्ज है।
   - `C/ProgramData/.cache/agent_state.dat`
6. निशान मिटाने का प्रयास रीसायकल बिन के मेटा-आर्टिफ़ैक्ट से पता चलता है: मूल पथ RuntimeBroker.exe की ओर इशारा करता है, विलोपन समय — 09:19:45 UTC।
   - `C/$Recycle.Bin/S-1-5-21-1961432191-301355982-4121230938-1001/$I8O5VA5.exe.txt`

परिणामस्वरूप, हमें यह फ़्लैग मिलता है:

**फ़्लैग:** `KubSTU{InvoiceViewer.exe|198.51.100.23:4444|OneDriveUpdate.vbs}`
