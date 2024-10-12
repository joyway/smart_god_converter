# Converts multiple Xbox 360 redump ISOs to GoD format and extract install discs

__author__ = 'Joyway'
__version__ = '1.0'


from subprocess import PIPE, Popen
import logging
import shutil
import re
import os
import sys
import csv


logging.basicConfig(
    filename="god.log",
    format="%(asctime)s %(levelname)s:%(message)s",
    encoding="utf-8",
    level=logging.INFO
    )

def prerequisiteCheck():
    """
    Checking all prerequisite files.
    """
    prerequisite = {
        "extract-xiso.exe": os.path.exists("lib\\extract-xiso.exe"),
        "iso2god-x86_64-windows.exe": os.path.exists("lib\\iso2god-x86_64-windows.exe"),
        "xextool.exe": os.path.exists("lib\\xextool.exe"),
        "xbox360_gamelist.csv": os.path.exists("lib\\xbox360_gamelist.csv")
        }
    if False in prerequisite.values():
        for k, v in prerequisite.items():
            if not v:
                print(f"# {k} is missing.")
        print("# Aborting, please check the README file for all the prerequisites.")
        sys.exit()

def get_xiso_directory():
    """
    Getting the directory of XISO from the user

    Returns:
        str: The diretcory of xiso files.
        list: A list of all xiso files.
    """
    xiso_list = []
    xiso_directory = ''
    while True:
        raw_path = input('# Enter the path of the XISOs source directory: ')
        if not os.path.exists(raw_path.strip()):
            print('# The path does NOT exist!')
            continue
        file_list = os.listdir(raw_path.strip())
        for file in file_list:
            if file[-4:] == '.iso':
                xiso_list.append(file)
        if not xiso_list:
            print('# The directory does NOT contain any ISO!')
            continue
        xiso_source = raw_path.strip()
        return xiso_source, xiso_list

def get_output_directory():
    """
    Getting the directory of XISO from the user.

    Returns:
        str: The output directory.
    """
    while True:
        raw_path = input('# Enter the path of the output directory: ')
        if not os.path.exists(raw_path.strip()):
            print('# The path does NOT exist!')
            continue
        output_directory = raw_path.strip()
        return output_directory

def _extract_content(
    xiso_source: str,
    xiso_file: str,
    output_directory: str,
    title_id: str
    ) -> tuple[str, str]:
    """
    Extract content from an XISO.

    Args:
        xiso_source (str): The diretcory of xiso files.
        xiso_file (str): The filename of the xiso file.
        output_directory (str): The output directory.
        title_id (str): The title ID of the disc.

    Returns:
        str: the path of the actually content(16 zero folder).
        str: the path of the extracted content.
    """
    xiso_path = os.path.join(xiso_source, xiso_file)
    folder_name = f"_temp_extract_{title_id}"
    extracted_path = os.path.join(output_directory, folder_name)
    xiso_extract_proc = Popen(
        ["lib\\extract-xiso.exe", "-s", "-d", extracted_path, xiso_path],
        stdout=PIPE,
        stderr=PIPE
        )
    outs, errs = xiso_extract_proc.communicate()
    extracted_files = os.listdir(extracted_path)
    content_path = ""
    for extracted_file in extracted_files:
        if extracted_file.lower() == "content":
            content_path = os.path.join(extracted_path, extracted_file, "0000000000000000")
            break
    return content_path, extracted_path

def _rebuild_xiso(
    xiso_source: str,
    xiso_file: str,
    extracted_path: str,
    output_directory: str,
    title_id: str
    ) -> str:
    """
    Rebuild an new samller XISO, get rid of all unused spaces and SystemUpdate folder.
    
    Args:
        xiso_source (str): The diretcory of xiso files.
        xiso_file (str): The filename of the xiso file.
        output_directory (str): The output directory.
        title_id (str): The title ID of the disc.

    Returns:
        str: the name of the rebuilt ISO, if rebuilt fail, return an empty string
    """
    rebuilt_xiso_path = extracted_path + '.rebuilt.iso'
    xiso_rebuild_proc = Popen(
        ["lib\\extract-xiso.exe", "-c", extracted_path, extracted_path + '.rebuilt.iso'],
        stdout=PIPE,
        stderr=PIPE
        )
    xiso_rebuild_proc.communicate()
    shutil.rmtree(extracted_path)
    if os.path.exists(rebuilt_xiso_path):
        return rebuilt_xiso_path
    else:
        # Rebuilding XISO from the extracted folder may fail for some image.
        # Involding the extract-xiso.exe built-in rewrite function to recreate the XISO
        # It doesn't get rid of the SystemUpdate folder but still better than redump
        logging.warning(f"{xiso_file}: ID_{title_id} - Rebuild from extracted: FAIL")
        logging.info(f"{xiso_file}: ID_{title_id} - Rebuilding using extract-xiso rewrite function")
        xiso_path = os.path.join(xiso_source, xiso_file)
        xiso_rebuild_proc = Popen(
            ["lib\\extract-xiso.exe", "-r", "-d", xiso_source, xiso_path],
            stdout=PIPE,
            stderr=PIPE
            )
        xiso_rebuild_proc.communicate()
        if os.path.exists(xiso_path):
            rebuilt_xiso_path = os.path.join(xiso_source, xiso_file + ".rebuilt.iso")
            os.rename(xiso_path, rebuilt_xiso_path)
            os.rename(xiso_path + ".old", xiso_path)
            return rebuilt_xiso_path
        else:
            return ""

def _get_xiso_info(xiso_path: str) -> tuple[str, str, int, int, float]:
    """
    Get XISO information.

    Args:
        xiso_path (str): The full path of the XISO file
    Returns:
        str: Content ID
        str: Content type
        int: Content size
        int: Disc size
        float: The ratio of the content size to the disc size
    """
    xiso_content_proc = Popen(
        ["lib\\extract-xiso.exe", "-l", xiso_path],
        stdout=PIPE,
        stderr=PIPE
        )
    content_outs, errs = xiso_content_proc.communicate()
    xiso_contents = content_outs.decode("utf-8").splitlines()
    content_id = ""
    content_type = ""
    content_size = 0
    content_size_ratio = 0
    content_id_regex = re.compile(r"\\content\\0{16}\\([A-Z0-9]{8})\\.{0,} \((\d+) bytes\)", re.I)
    content_type_regex = re.compile(r"\\content\\0{16}\\[A-Z0-9]{8}\\([A-Z0-9]{8})\\ \(0 bytes\)", re.I)
    for content in xiso_contents:
        content_id_match = content_id_regex.match(content)
        content_type_match = content_type_regex.match(content)
        if content_id_match:
            content_id = content_id_match.groups()[0]
            content_size += int(content_id_match.groups()[1]) # Calculate the size of the content folder
        if content_type_match:
            content_type = content_type_match.groups()[0]
    content_id = content_id.upper()
    content_type = content_type.upper()
    # Get disc size
    disc_size_regex = re.compile(r"\.iso total (\d+) bytes$")
    disc_size = disc_size_regex.search(xiso_contents[-1].strip())
    if disc_size:
        disc_size = int(disc_size.groups()[0])
        content_size_ratio = content_size/disc_size
    return content_id, content_type, content_size, disc_size, content_size_ratio

def check_disc_type(xiso_path: str, output_directory: str) -> tuple[bool, str]:
    """
    Check whether the disc is a play disc or install disc(including DLC disc).

    Args:
        xiso (str): The full path of the XISO file that needs to be checked.
        output_directory (str): The output directory.

    Returns:
        bool: is it an install disc?
        str: the title id of the XISO.
    """
    content_id, content_type, content_size, disc_size, content_size_ratio = _get_xiso_info(xiso_path)
    # Get title ID from iso2god
    title_id = ""
    title_id_regex = re.compile(r"Title ID: ([a-zA-Z0-9]{8})", re.I)
    god_title_proc = Popen(
        ["lib\\iso2god-x86_64-windows.exe", "--dry-run", xiso_path, output_directory],
        stdout=PIPE,
        stderr=PIPE
        )
    title_outs, title_errs = god_title_proc.communicate()
    for line in title_outs.decode("utf-8").splitlines():
        title_id_match = title_id_regex.match(line)
        if title_id_match:
            title_id = title_id_match.groups()[0]
            break
    title_id = title_id.upper()

    # It is a install disc only when:
    # - the content type is not demo(00080000)
    # - content folder takes more than 50% of the disc size
    # This includes some of redump discs of XBLA games such as Minecraft, The Walking Dead, etc.
    logging.info(f"{xiso_path}: ID_{title_id} - Content takes {(content_size_ratio * 100):.2f}% of disc size")
    is_install_disc = False
    if all([
        content_type != "00080000",
        content_size_ratio >= 0.5
        ]):
            is_install_disc = True
    content_id = title_id
    return is_install_disc, content_id

def get_base_game_ids(xex_path: str) -> list:
    """
    Check against the xbox360_gamelist.csv file to find the base game ID for DLC discs.

    Args:
        xex_path (str): The path of the xex excutable of the game.

    Returns:
        list: The base game IDs
    """
    media_id = ""
    base_game_ids = []
    xex_proc = Popen(
        ["lib\\xextool.exe", "-l", xex_path],
        stdout=PIPE,
        stderr=PIPE
        )
    outs, errs = xex_proc.communicate()
    for line in outs.decode('utf-8').splitlines():
        if 'Media Id:' in line:
            media_id = line.split(":")[1].strip()
            break
    media_id = media_id.upper()
    if not media_id:
        return base_game_ids
    with open("lib\\xbox360_gamelist.csv") as gamelist_file:
        gamelist_reader = csv.reader(gamelist_file)
        for row in gamelist_reader:
            row_media_id = row[6].strip().upper()
            if row_media_id == media_id:
                base_game_ids.append(row[1].strip().upper())
    return base_game_ids

def extract_dlc_disc(
    xiso_source: str,
    xiso_file: str,
    output_directory: str,
    user_msg: str =""
    ) -> bool:
    """
    Extract DLC discs.
    If the GoD format of the base game could be located, the DLC content will be merged into it.
    Otherwise, the content will be put into a "DLC" folder and needs to be handle manually.

    Args:
        xiso_source (str): The diretcory of xiso files.
        xiso_file (str): The filename of the xiso file.
        output_directory (str): The output directory.
        user_msg (str, optional): The print out messages. Defaults to "".

    Returns:
        bool: Whether the base game could be found.
    """
    base_game_id = ""
    content_path, extracted_path = _extract_content(xiso_source, xiso_file, output_directory, "FFED2000")
    xex_path = os.path.join(extracted_path, "default.xex")
    base_game_ids = get_base_game_ids(xex_path) # Get title ID of the actual game
    content_path = os.path.join(content_path, "FFED2000", "FFFFFFFF")
    base_game_found = False
    if base_game_ids:
        all_games = os.listdir(output_directory)
        for base_game_id in base_game_ids: # A DLC disc could have multiple base game versions:
            if base_game_id in all_games:
                base_game_directory = os.path.join(output_directory, base_game_id, "00000002")
                base_game_found = True
                if not os.path.exists(base_game_directory):
                    os.makedirs(base_game_directory)
                logging.info(f"{xiso_file}: ID_FFED2000 - DLC DISC - Base game ID {base_game_id}")
                shutil.copytree(content_path, base_game_directory, dirs_exist_ok=True)
    
    if not base_game_found:
        # Unable to find the base game ID
        # Putting into a DLC folder for user manual operation
        output_directory = os.path.join(output_directory, "DLC", xiso_file, "00000002")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        print("\r" + f"{user_msg} Base game not found!", end="")
        logging.info(f"{xiso_file}: ID_FFED2000 - DLC DISC - No base game found")
        shutil.copytree(content_path, output_directory, dirs_exist_ok=True)
    shutil.rmtree(extracted_path)
    return base_game_found

def extract_install_disc(
    xiso_source: str,
    xiso_file: str,
    output_directory: str,
    title_id: str,
    user_msg: str = ""
    ):
    """
    Extract isntall discs.

    Args:
        Args:
        xiso_source (str): The diretcory of xiso files.
        xiso_file (str): The filename of the xiso file.
        output_directory (str): The output directory.
        title_id (str): The title ID of the disc.
        user_msg (str, optional): The print out messages. Defaults to "".
    """
    content_path, extracted_path = _extract_content(xiso_source, xiso_file, output_directory, title_id)
    shutil.copytree(content_path, output_directory, dirs_exist_ok=True)
    shutil.rmtree(extracted_path)
    print("\r" + f"{user_msg} Done")

def convert_to_god(
    xiso_source: str,
    xiso_file: str,
    output_directory: str,
    title_id: str,
    user_msg: str = ""
    ):
    """
    Convert an XISO to GamesOnDemand format

    Args:
        xiso_source (str): The diretcory of xiso files.
        xiso_file (str): The filename of the xiso file.
        output_directory (str): The output directory.
        user_msg (str, optional): The print out messages. Defaults to "".
    """
    xiso_path = os.path.join(xiso_source, xiso_file)
    print("\r" + f"{user_msg}, extracting...", end="")
    content_path, extracted_path = _extract_content(xiso_source, xiso_file, output_directory, title_id)
    # Extract installable content from play disc, such as HD texture pack
    if content_path:
        shutil.copytree(content_path, output_directory, dirs_exist_ok=True)
        logging.info(f"{xiso_file}: ID_{title_id} - Extracted installable content.")
    
    print("\r" + f"{user_msg}, rebuilding ISO...", end="")
    rebuilt_xiso_path = _rebuild_xiso(xiso_source, xiso_file, extracted_path, output_directory, title_id)
    if rebuilt_xiso_path:
        print("\r" + f"{user_msg}, rebuilding ISO... Done", end="")
        logging.info(f"{xiso_file}: ID_{title_id} - Rebuild SUCCEDED")
        xiso_path = rebuilt_xiso_path
    else:
        print("\r" + f"{user_msg}, rebuilding ISO... Fail, using the orginal ISO", end="")
        logging.info(f"{xiso_file}: ID_{title_id} - Rebuild FAILED")
    progress = 0
    writing_part_regex = re.compile(r"writing part +(\d+) of (\d+)")
    print("\33[2K", end="\r")
    print("\r" + f"{user_msg}, converting... {progress}%", end="")
    with Popen(
        ["lib\\iso2god-x86_64-windows.exe", "--trim", xiso_path, output_directory],
        stdout=PIPE,
        stderr=PIPE
        ) as god_convert_proc:
        for line in god_convert_proc.stdout:
            line = line.decode("utf-8")
            writing_part_match = writing_part_regex.match(line)
            if writing_part_match:
                progress = int(int(writing_part_match.groups()[0]) / int(writing_part_match.groups()[1]) * 100)
            print("\r" + f"{user_msg}, converting... {progress}%", end="")
    print("\33[2K", end="\r")
    print("\r" + f"{user_msg}, converting... 100%")
    # Deleting the rebuilt xiso after conversion
    if rebuilt_xiso_path:
        os.remove(rebuilt_xiso_path)

def main():
    print('# Welcome!')
    prerequisiteCheck()
    xiso_source, xiso_list = get_xiso_directory()
    output_directory = get_output_directory()
    total_count = len(xiso_list)
    padding = len(str(total_count))
    dlc_discs = []
    orphan_dlcs = [] # Stores all the DLC discs that cannot find the base game
    i = 1
    for xiso_file in xiso_list:
        xiso_path = os.path.join(xiso_source, xiso_file)
        is_install_disc, title_id = check_disc_type(xiso_path, output_directory)
        if not title_id:
            user_msg = f"# ({i:0{padding}}/{len(xiso_list)}) {xiso_file} "
            user_msg += f"({title_id}) is INVALID, skipping... "
            logging.warning(f"{xiso_file}: ID_{title_id} - INVALID DISC")
            print("\r" + user_msg)
            continue
        if is_install_disc :
            if title_id == "FFED2000":
                # General DLC discs such as GOTY disc 2 uses FFED2000 as the title ID instead of the real game ID 
                # DLC discs should the last discs to handle
                dlc_discs.append(xiso_file)
            else:
                user_msg = f"# ({i:0{padding}}/{len(xiso_list)}) {xiso_file} "
                user_msg += f"({title_id}) is an install disc, extracting... "
                logging.info(f"{xiso_file}: ID_{title_id} - INSTALL DISC")
                print("\r" + user_msg, end="")
                i += 1
                extract_install_disc(xiso_source, xiso_file, output_directory, title_id, user_msg)
        else:
            user_msg = f"# ({i:0{padding}}/{len(xiso_list)}) {xiso_file} "
            user_msg += f"({title_id}) is an play disc"
            print("\r" + user_msg, end="")
            logging.info(f"{xiso_file}: ID_{title_id} - PLAY DISC")
            i += 1  
            convert_to_god(xiso_source, xiso_file, output_directory, title_id, user_msg) 
    
    # Handle DLC discs after all other discs are processed.
    for xiso_file in dlc_discs:
        user_msg = f"# ({i:0{padding}}/{len(xiso_list)}) {xiso_file} "
        user_msg += "(FFED2000) is a DLC disc, extracting... "
        print("\r" + user_msg, end="")
        extract_result = extract_dlc_disc(xiso_source, xiso_file, output_directory, user_msg)
        print("\r" + user_msg + ' Done')
        if not extract_result:
            orphan_dlcs.append(xiso_file)
        i += 1
    if orphan_dlcs:
        print("\n# Cannot locate the base game for following DLC discs:")
        print("    - " + "\n    - ".join(orphan_dlcs))
        print("# The extracted DLC content has been put under the \"DLC\" folder, please check them manually.")
if __name__ == '__main__':
    main()
