# Smart XISO(Xbox 360) to GoD(Games on Demand) Converter
Converts Xbox 360 XISOs to GoD format in batch. When it detects the ISO is an install disc(such as Halo 4 disc 2, GTA V disc 1), it will extract the installation content automatically.

## Prerequisite
- Python 3.8+
- `extract-xiso.exe` from https://github.com/XboxDev/extract-xiso
- `iso2god-x86_64-windows.exe` from https://github.com/iliazeus/iso2god-rs
- `xextool.exe` from https://digiex.net/threads/xextool-6-3-download.9523/
- `xbox360_gamelist.csv` from https://github.com/IronRingX/xbox360-gamelist

Download the latest releases of `extract-xiso.exe`, `iso2god-x86_64-windows.exe`, `xextool.exe` as well as `xbox360_gamelist.csv` then put them under the `lib` folder.

## Initial Setup
1. Download and install Python
2. Download the project from Github and extract it
3. Download the latest releases of `extract-xiso.exe`, `iso2god-x86_64-windows.exe`, `xextool.exe` as well as `xbox360_gamelist.csv` then put them under the `lib` folder.

## How to use
1. Run the script in terminal: `python3 smart_god_converter` or `python smart_god_converter`, then follow the script instruction.
2. It you see a warning message says "Cannot locate the base game for following DLC discs", please check the "DLC" folder inside of your output directory, then copy the "00000002" folder of each discs to the correct base game directory, along with the "00007000" folder of the base game.

## How does it work
The script works based on following logic automatically:
### 1. Check disc type
1. Uses `extract-xiso.exe` to determine whether the disc contains the "Content\0000000000000000" content folder.
2. If not, **this is a play disc**.
3. If yes, get the title ID from the file name of the sub folder:
    1. If the title ID from the sub folder is FFED2000, **this is a DLC discs** such as many GOTY games disc 2.
    2. If the title ID from the sub folder matches the game title ID, **this is an install disc**(such as Halo 4 disc 2).
    3. If the title ID from the sub folder does NOT match the game title ID and is NOT FFED2000, **this is a play disc**. The content folder is for another game, for example Halo CE Anniversary contains some new maps for Halo Reach.

### 2. Handle play discs
Play discs will be converted to GamesOnDemand format by `iso2god-x86_64-windows.exe`.

### 3. Handle install discs
The script uses `extract-xiso.exe` to extract the content folder("Content\0000000000000000") from install discs.

### 3. Handle DLC discs
The script processes all DLC discs after all other types of discs have been processed.

All DLC discs use a generic title ID "FFED2000", so the script has to use some workaround to look up the real title ID of the base game.
1. Use `xextool.exe` to get the media ID from the DLC disc
2. Lookup the media ID in `xbox360_gamelist.csv` and try to locate the title ID of the base game
3. If the title ID of the base game could be found, and the base game is already in the output directory, the script will extract the content folder from the DLC disc, then put into the "00000002" folder inside of the base game directory, along with the "00007000" folder of the base game.
4. If the title ID of the base game could not be found, or the base game is not in the output directory, the script will extract the content folder into a "DLC" folder, then show up a warning message to the user.