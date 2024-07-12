# | filename: script.py
# | code-line-numbers: true

import os
import sys
from pathlib import Path
import shutil
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)



def build_dataset(base_directory:str) -> None:
    dataset_parts_path = Path(base_directory) / "dataset_parts"
    # dataset_parts_path = base_directory + "/dataset_parts"
    complete_dataset_path = Path(base_directory) / "dataset_agg"
    # complete_dataset_path = base_directory + "/dataset_agg"

    logger.info(complete_dataset_path)
    logger.info(os.listdir(dataset_parts_path))

    
    # get dataset parts
    dataset_parts = __get_folders_in_directory(dataset_parts_path)
    logger.info('__get_folders_in_directory done')
    logger.info(dataset_parts)
    
    # build folder structure, compatible with yolov5 standard
    __build_folder_structure(complete_dataset_path)
    logger.info('__build_folder_structure done')

    # distribute images and labels in their respective folders
    __build_dataset(dataset_parts, base_directory, complete_dataset_path)
    logger.info('__build_dataset() done')
    logger.info(os.listdir(f"{complete_dataset_path}/train"))
    
    

def __get_folders_in_directory(dir_path)->list:
    """
    Get a list of folders in the specified directory.
    
    Args:
    - dir_path (str): Path to the directory.
    
    Returns:
    - list: List of folders in the directory.
    """
    folders = []
    # Check if the directory exists
    if os.path.exists(dir_path):
        # Iterate over items in the directory
        for item in os.listdir(dir_path):
            # Create the full path of the item
            item_path = os.path.join(dir_path, item)
            # Check if the item is a directory
            if os.path.isdir(item_path):
                # Add the directory to the list of folders
                folders.append(item)
    return folders


def __build_folder_structure(complete_dataset_path:Path) -> None:
    # Define subdirectories
    subdirectories = ["test", "train", "valid"]

    # Define sub-subdirectories
    subsubdirectories = ["images", "labels"]

    # Create the root directory if it doesn't exist
    if not os.path.exists(complete_dataset_path):
        os.mkdir(complete_dataset_path)

    # Create subdirectories and sub-subdirectories
    for subdirectory in subdirectories:
        subdir_path = os.path.join(complete_dataset_path, subdirectory)
        if not os.path.exists(subdir_path):
            os.mkdir(subdir_path)
        
        # Create sub-subdirectories
        for subsubdirectory in subsubdirectories:
            subsubdir_path = os.path.join(subdir_path, subsubdirectory)
            if not os.path.exists(subsubdir_path):
                os.mkdir(subsubdir_path)




def __build_dataset(dataset_parts:list, base_directory:str, complete_dataset_path:Path) -> None:
    dataset_parts_path = Path(base_directory) / "dataset_parts"
    for dataset in dataset_parts:
        for set_type in ['train', 'test', 'valid']:
            for element in ['images', 'labels']:
                for file_name in os.listdir(dataset_parts_path / dataset / set_type / element):
                    shutil.copyfile(
                        dataset_parts_path / dataset / set_type / element / file_name,
                        complete_dataset_path / set_type / element / file_name
                        )
            

if __name__ == "__main__":
    build_dataset(base_directory="/opt/ml/processing/input/data")
    logger.info('build_dataset() done')
