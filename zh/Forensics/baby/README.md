# baby

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

我们拿到一台被入侵的 Windows 主机的镜像。需要重建事件过程并拼出 flag。

## 🏁 解答

用户在浏览器中点击了指向文件 InvoiceViewer.exe 的链接，并将其保存到 Downloads。在 09:16:02 UTC，执行痕迹表明该文件被处理过。随后在用户配置文件中创建了一个自启动项 OneDriveUpdate.vbs，它记录了一个指向伪装名称 RuntimeBroker.exe 的对象的引用，该对象位于合法系统目录之外。在 ProgramData 中以隐藏状态残留着一份配置，其端点为 198.51.100.23:4444；该地址属于保留用于文档的 TEST-NET-2 范围，在本教学案例中并非真实基础设施 [1]。最后，回收站中保留了该伪装对象的删除元数据。

1. 用户从 http://198.51.100[.]23:8080/InvoiceViewer.exe 下载了 InvoiceViewer.exe。
   - 证据是痕迹数据：`C/Users/Alex/Downloads/InvoiceViewer.exe`；`C/Users/Alex/AppData/Local/Google/Chrome/User Data/Default/History`
2. 该文件首次运行/处理于 2026-06-11 09:16:02 UTC。
   - 根据 Windows 优化文件：`C/Windows/Prefetch/INVOICEVIEWER.EXE-8B96A1D2.pf.txt`；`C/Users/Alex/AppData/Local/Temp/invoice_render.log`；`ConsoleHost_history.txt`
3. 持久化机制是用户 Startup 目录中的 OneDriveUpdate.vbs 文件。它引用了 `%APPDATA%\Microsoft\OneDrive\RuntimeBroker.exe`。
   - 证据是一种常见的持久化手法：`C/Users/Alex/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/OneDriveUpdate.vbs`
4. 名称 RuntimeBroker.exe 伪装成正规组件，但该对象位于用户配置文件中，而不在 `C:\Windows\System32`。
   - `C/Users/Alex/AppData/Roaming/Microsoft/OneDrive/RuntimeBroker.exe`
5. 残留的配置痕迹中记录了 198.51.100.23:4444。
   - `C/ProgramData/.cache/agent_state.dat`
6. 回收站的元痕迹显示了删除痕迹的尝试：原始路径指向 RuntimeBroker.exe，删除时间为 09:19:45 UTC。
   - `C/$Recycle.Bin/S-1-5-21-1961432191-301355982-4121230938-1001/$I8O5VA5.exe.txt`

最终，我们得到如下 flag：

**Flag：** `KubSTU{InvoiceViewer.exe|198.51.100.23:4444|OneDriveUpdate.vbs}`
