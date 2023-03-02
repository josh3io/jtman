# jtman

Author: WA6SM

works with wsjtx and lotw to alert you to new dx, state, and callsign contacts.

![](jtman.png)

Run: ``CONFIG=my_config.ini python3 main.py``

see the default config.ini for placeholder options.

### Install on Ubuntu 20.04
```bash
git clone https://github.com/josh3io/jtman.git
cd jtman
git submodule update --init --recursive
```
copy config.ini to my_config.ini and update as necessary, then run as above.

Ubuntu 20.04 does not have tkinter installed by default, and requires running
```bash
sudo apt install python3-tk
```
