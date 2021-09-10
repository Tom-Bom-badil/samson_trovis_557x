Settings file (xslx):

Thanks to user ClearY / ClearEyetem) from the Haustechnikdialog forum for providing this:
https://www.haustechnikdialog.de/Forum/t/226142/Neue-Fernwaermeanlage-How-to-start
The file helps you to note all settings of your Trovis. 


Sniffers / .py files:

Use these tools with caution - they were made quick&dirty and are highly experimental.
The tools check one by one if a register/coil is readable.
If yes, the value is displayed - if no, an error is shown.
At the end, all found blocks are shown, and a 'quick read-out' by using validated blocks
instead of single registers/coils is done.

The tools require that you can communicate with your Trovis, so a stable interface is a MUST.

The following points need to be validated / changed in case of need:
- Interface: Default in code is /dev/ttytrovis, may need to be changed to /dev/trovis or such
- Unit no.: Default in code is 247, may need to be changed as set in trovis menu

A 'block' the sniffers checks for readable registers/coils should not exceed 120
(recommended: 100 in order to keep it easy and to be on safe side).

Pretty much on top of the code, you can add search blocks by adding new lines as follows
(add as many lines/search blocks as you like):
suchbereiche.append([0,99])          # Check first block of 100 registers (0-99)
suchbereiche.append([100,199])       # Check second block of 100 registers (100-199)
suchbereiche.append([765,798])       # Check third block of 100 registers (765-798)

Usage:
- check/validate above points
- amend registers as needed in source code
- run a shell:
> cd /usr/local/smarthome/plugins/trovis_557x/tools  # or wherever shNG resides
> python3 register_sniffer.py
> python3 coils_sniffer.py

Note: When seaching for many registers/coils, it may take hours to finish!
