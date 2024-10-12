# Smart XISO(Xbox 360) to GoD(Games on Demand) Converter

Converts multiple Xbox 360 XISOs to GoD format in batch. It will scan the content in each XISO and choose the appropriate way to handle it.

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
3. If yes:
    1. If the title ID from the content folder is FFED2000, **this is a DLC discs** such as many GOTY games disc 2.
    2. If the content folder size takes more than 50% of the disc size, **this is an install disc**, such as Halo 4 disc 2, GTA V disc 1 and many XBLA game discs.
    3. If the content folder size takes less than 50% of the disc size, this is **this is a play disc**. The content folder could be some installable content, for example:
        - Texture packs for the base game.
        - XBLA games that come with the base game, such as Doom 3 BFG version contains Doom 1 and 2 as XBLA games.
        - Content for another games, for example Halo CE Anniversary disc contains a few new maps for Halo Reach.

### 2. Handle play discs
1. Play discs will be extracted first(by `extract-xiso.exe`), to get rid of the `SystemUpdate` folder and unused space
2. Then the extracted content will be rebuilt into a new, smaller XISO
3. The rebuilt discs will be converted to GamesOnDemand format by `iso2god-x86_64-windows.exe`.
4. If the play disc also has a content folder, they will also be extracted.

### 3. Handle install discs(Including XBLA discs)
The script uses `extract-xiso.exe` to extract the content folder("Content\0000000000000000") from install discs.

### 3. Handle DLC discs
The script processes all DLC discs after all other types of discs have been processed.

All DLC discs use a generic title ID "FFED2000", so the script has to use some workaround to look up the real title ID of the base game.
1. Use `xextool.exe` to get the media ID from the DLC disc
2. Lookup the media ID in `xbox360_gamelist.csv` and try to locate the title ID of the base game
3. If the title ID of the base game could be found, and the base game is already in the output directory, the script will extract the content folder from the DLC disc, then put into the "00000002" folder inside of the base game directory, along with the "00007000" folder of the base game.
4. If the title ID of the base game could not be found, or the base game is not in the output directory, the script will extract the content folder into a "DLC" folder, then show up a warning message to the user.


## Known issues:
- `iso2god-x86_64-windows.exe` and `xextool.exe` may not be able to read some XISOs, such as Armored Core 4 (USA) and Destiny (World). Please use the GUI version of [iso2god](https://github.com/r4dius/Iso2God) to convert them manually.
- Some specific games will be partially of completely unplayable in GoD format, such as Watch Dogs(completely unplayable) and Batman Arkham City(DLC unplayable).
- Some specific install discs don't have the content folder, such as Wolfenstein New Order disc 1. You have to run the disc to install the content.
