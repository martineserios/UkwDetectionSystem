import os
import random
import shutil

random.seed(42)
from multiprocessing import Pool

############
# variables
ORIGINAL_DATASET_PATH = '/home/martin/Projects/ongoing/ukw/data/base/full/total'
SET_TYPES = ["test", "train", "valid"] 
SET_TYPES_RATIOS = [0.7, 0.25, 0.05]
ELEMENTS = ["images", "labels"]

PARTITIONED_DATASET_PATH = '/home/martin/Projects/ongoing/ukw/data/base/incipiente_full_tres'
N_PARTS = 3
############


import os
import random
import shutil
from multiprocessing import Pool
from pathlib import Path

from loguru import logger


def build_dataset_structure(parts: int, set_types: list, elements: list, structure_order=['parts', 'set_types', 'elements']) -> dict:
    """
    Create a nested dictionary structure to represent dataset partitions.

    Args:
        parts (int): Number of parts to divide the dataset into.
        set_types (list): List of dataset types (e.g., train, val, test).
        elements (list): List of elements (e.g., images, labels).
        structure_order (list): Order in which to nest the structure.

    Returns:
        dict: Nested dictionary representing the dataset structure.
    """
    assert sum([parts, len(set_types), len(elements)]) > 0, "Input lists must not be empty."

    logger.info("Building dataset structure with parts: {}, set_types: {}, elements: {}", parts, set_types, elements)

    structure_order_map = {
        'parts': [str(part) for part in range(1, parts + 1)],
        'set_types': set_types,
        'elements': elements
    }
    return {l1: {l2: {l3: [] for l3 in structure_order_map[structure_order[2]]} for l2 in structure_order_map[structure_order[1]]} for l1 in structure_order_map[structure_order[0]]}

def build_dataset_structure_on_disk(new_dataset_path: Path, n: int):
    """
    Create directory structure on disk for the dataset.

    Args:
        new_dataset_path (Path): Path where the new dataset structure will be created.
        n (int): Number of parts to divide the dataset into.
    """
    logger.info("Creating directory structure on disk at {}", new_dataset_path)
    new_dataset_path.mkdir(parents=True, exist_ok=True)

    for part in range(1, n + 1):
        part_path = new_dataset_path / str(part)
        part_path.mkdir(exist_ok=True)
        for set_type in SET_TYPES:
            set_type_path = part_path / set_type
            set_type_path.mkdir(exist_ok=True)
            for element in ELEMENTS:
                element_path = set_type_path / element
                element_path.mkdir(exist_ok=True)

def get_dataset_paths_by_elements(original_dataset_path: Path) -> dict:
    """
    Retrieve file paths for each element in the dataset.

    Args:
        original_dataset_path (Path): Path to the original dataset.

    Returns:
        dict: Dictionary of paths categorized by element (image, label).
    """
    logger.info("Retrieving dataset paths by elements from {}", original_dataset_path)
    dataset_paths_by_elements = {set_type: {element: [] for element in ELEMENTS} for set_type in SET_TYPES}

    for set_type in SET_TYPES:
        for element in ELEMENTS:
            element_dir = original_dataset_path / set_type / element
            if element_dir.exists():
                dataset_paths_by_elements[set_type][element] = sorted([str(file) for file in element_dir.iterdir() if file.is_file()])

    return dataset_paths_by_elements

def get_images_labels(original_dataset_path: Path) -> dict:
    """
    Retrieve image and label paths from the dataset.

    Args:
        original_dataset_path (Path): Path to the original dataset.

    Returns:
        dict: Dictionary containing lists of image and label paths.
    """
    logger.info("Retrieving image and label paths from {}", original_dataset_path)
    data = {element: [] for element in ELEMENTS}
    dataset = get_dataset_paths_by_elements(original_dataset_path)
    
    for set_type in SET_TYPES:
        for element in ELEMENTS:
            data[element] += dataset[set_type][element]

    # assert len(data[ELEMENTS[0]]) == len(data[ELEMENTS[1]]), "Mismatch in number of images and labels."

    return data

def turn_parts_into_ratios(parts: int, precision=4) -> list:
    """
    Turn number of parts into a list of ratios.

    Args:
        parts (int): Number of parts to divide into.
        precision (int): Precision of the ratios.

    Returns:
        list: List of ratios.
    """
    assert parts > 0, "Number of parts must be greater than zero."
    logger.info("Turning {} parts into ratios with precision {}", parts, precision)
    return [round(1 / parts, precision) for _ in range(parts)]

def get_sublists_from_ratios(original: list, ratios: list, shuffle=True) -> list:
    """
    Divide the original list according to the given ratios.

    Args:
        original (list): The original list to be divided.
        ratios (list): Ratios to divide the list by.
        shuffle (bool): Whether to shuffle the list before dividing.

    Returns:
        list: List of sublists divided by ratios.
    """
    assert abs(sum(ratios) - 1) < 0.001, "The sum of the ratios must be 1."
    total_length = len(original)
    indices = [int(r * total_length) for r in ratios]

    if shuffle:
        random.shuffle(original)
    
    indices[-1] = total_length - sum(indices[:-1])
    
    divided_lists = []
    current_index = 0
    
    for count in indices:
        divided_lists.append(original[current_index:current_index + count])
        current_index += count
    
    logger.info("Divided list into {} parts with ratios {}", len(divided_lists), ratios)
    return divided_lists

def get_sublists_from_n_parts(original: list, n_parts: int, shuffle=True) -> list:
    """
    Divide the original list into n parts.

    Args:
        original (list): The original list to be divided.
        n_parts (int): Number of parts to divide into.
        shuffle (bool): Whether to shuffle the list before dividing.

    Returns:
        list: List of sublists divided into n parts.
    """
    return get_sublists_from_ratios(original, turn_parts_into_ratios(n_parts), shuffle)

def get_sublists_from_named_parts(original: list, named_parts: list, ratios=[], shuffle=True) -> list:
    """
    Divide the original list into named parts using the given ratios.

    Args:
        original (list): The original list to be divided.
        named_parts (list): Names for each part.
        ratios (list): Ratios to divide the list by.
        shuffle (bool): Whether to shuffle the list before dividing.

    Returns:
        list: List of sublists divided into named parts.
    """
    if not ratios:
        ratios = turn_parts_into_ratios(len(named_parts))

    assert len(ratios) == len(named_parts), "Number of ratios must match number of named parts."

    logger.info("Dividing list into named parts {} with ratios {}", named_parts, ratios)
    return get_sublists_from_ratios(original, ratios, shuffle)

def get_dataset_by_named_parts_ratios(original: list, named_parts: list, ratios: list, shuffle=True) -> dict:
    """
    Create a dataset divided into named parts using given ratios.

    Args:
        original (list): The original list to be divided.
        named_parts (list): Names for each part.
        ratios (list): Ratios to divide the list by.
        shuffle (bool): Whether to shuffle the list before dividing.

    Returns:
        dict: Dictionary with named parts as keys and sublists as values.
    """
    parts_lists = get_sublists_from_named_parts(original, named_parts, ratios, shuffle)
    named_parts_list = zip(named_parts, parts_lists)
    
    return {part: lst for part, lst in named_parts_list}

def write_files(new_dataset_path: Path, part: str, set_type: str, element: str, file_paths_list: list):
    """
    Write files to the new dataset structure on disk.

    Args:
        new_dataset_path (Path): Path to the new dataset.
        part (str): Part name.
        set_type (str): Set type (e.g., train, val, test).
        element (str): Element type (e.g., images, labels).
        file_paths_list (list): List of file paths to write.
    """
    logger.info("Writing files to new dataset path at {}", new_dataset_path)
    for file_path in file_paths_list:
        file_name = Path(file_path).name
        dest_path = new_dataset_path / part / set_type / element / file_name
        shutil.copyfile(file_path, dest_path)

def partition_dataset(original_dataset_path: str, n_parts: int, test_set_val_size: list, write_path='', structure_order=['parts', 'set_types', 'elements'], shuffle=True) -> dict:
    """
    Partition the dataset into specified parts and optionally write to disk.

    Args:
        original_dataset_path (str): Path to the original dataset.
        n_parts (int): Number of parts to divide into.
        test_set_val_size (list): Ratios for dividing test/validation sets.
        write_path (str): Path to write the new dataset structure.
        structure_order (list): Order in which to nest the structure.
        shuffle (bool): Whether to shuffle the dataset before partitioning.

    Returns:
        dict: Dictionary representing the new dataset structure.
    """
    original_dataset_path = Path(original_dataset_path)
    write_path = Path(write_path) if write_path else ''

    logger.info("Partitioning dataset from {} into {} parts", original_dataset_path, n_parts)

    images_labels = get_images_labels(original_dataset_path)
    dataset = build_dataset_structure(n_parts, SET_TYPES, ELEMENTS, structure_order)

    if write_path:
        with Pool() as p:
            p.starmap(build_dataset_structure_on_disk, [(write_path, n_parts)])

    for element in ELEMENTS:
        for part, sublist in enumerate(get_sublists_from_n_parts(images_labels[element], n_parts, shuffle)):
            part = str(part + 1)
            for set_type, files_paths in get_dataset_by_named_parts_ratios(sublist, SET_TYPES, test_set_val_size, shuffle).items():
                dataset[part][set_type][element] = files_paths  

                if write_path:
                    with Pool() as p:
                        p.starmap_async(write_files, [(write_path, part, set_type, element, files_paths)])

    logger.info("Dataset partitioning complete")
    return dataset
