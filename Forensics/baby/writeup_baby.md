Baby

Пользователь перешёл в браузере по ссылке на файл InvoiceViewer.exe и сохранил его в Downloads. В 09:16:02 UTC следы запуска указывают на обработку этого файла. Затем в профиле пользователя был создан элемент автозапуска OneDriveUpdate.vbs, который документирует ссылку на объект с маскирующим именем RuntimeBroker.exe вне легитимного системного каталога. В скрытом состоянии ProgramData осталась конфигурация с конечной точкой 198.51.100.23:4444; этот адрес относится к выделенному для документации диапазону TEST-NET-2 и не является действительной инфраструктурой в рамках учебного кейса [1]. Наконец, в корзине сохранены метаданные удаления маскирующегося объекта.

1	Пользователь загрузил InvoiceViewer.exe с http://198.51.100[.]23:8080/InvoiceViewer.exe.	
 Доказательством являются данные артефактов: 
 C/Users/Alex/Downloads/InvoiceViewer.exe; 
 C/Users/Alex/AppData/Local/Google/Chrome/User Data/Default/History
2	Впервые файл был запущен/обработан 2026-06-11 09:16:02 UTC.	
Согласно файлам оптимизации Windows: 
C/Windows/Prefetch/INVOICEVIEWER.EXE-8B96A1D2.pf.txt; 
C/Users/Alex/AppData/Local/Temp/invoice_render.log; 
ConsoleHost_history.txt
3	Механизм закрепления — файл OneDriveUpdate.vbs в пользовательском каталоге Startup. Он ссылается на %APPDATA%\Microsoft\OneDrive\RuntimeBroker.exe.	
Доказательством является распространненая тактика закрепления:
C/Users/Alex/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/OneDriveUpdate.vbs
4	Имя RuntimeBroker.exe маскируется под штатный компонент, но объект расположен в пользовательском профиле, а не в C:\Windows\System32.
C/Users/Alex/AppData/Roaming/Microsoft/OneDrive/RuntimeBroker.exe
5	В остаточном конфигурационном следе зафиксировано 198.51.100.23:4444.	
C/ProgramData/.cache/agent_state.dat
6	Попытку удалить следы показывает метаартефакт корзины: исходный путь указывает на RuntimeBroker.exe, время удаления — 09:19:45 UTC.
	C/$Recycle.Bin/S-1-5-21-1961432191-301355982-4121230938-1001/$I8O5VA5.exe.txt
В итоге мы имеем данный флаг:
KubSTU{InvoiceViewer.exe|198.51.100.23:4444|OneDriveUpdate.vbs}
