import os
import random

import yaml

random.seed(42)
import logging
import shutil
from pathlib import Path

import ruamel.yaml
from loguru import logger

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

############
# variables
SET_TYPES = ["test", "train", "valid"] 
ELEMENTS = ["images", "labels"]
############

def replace_first_char_in_files(directory):
    # Loop through each file in the given directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if the file is a text file
        if os.path.isfile(file_path) and filename.endswith('.txt'):
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # Modify lines where the first character is '0'
            modified_lines = []
            for line in lines:
                if line.strip() and line[0] == '0':
                    modified_lines.append('1' + line[1:])
                else:
                    modified_lines.append(line)

            # Write the modified lines back to the file
            with open(file_path, 'w') as file:
                file.writelines(modified_lines)


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

    try:
        shutil.rmtree(new_dataset_path)
    except OSError as e:
        logger.info("Couldn't remove dir %s. %s" % (new_dataset_path, e.strerror))

        pass

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


def turn_size_into_ratios(total_size: int, size:int):
    assert total_size > 0

    size_ratio = size / total_size
    n_parts = total_size // size
    
    ratios = [size_ratio for i in range(1, n_parts + 1)] + [1 - n_parts * size_ratio]
    return ratios




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
    for ratio in ratios:
        assert (ratio > 0) & (ratio <= 1 )


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


def get_sublists_from_size(original: list, size: list, shuffle=True) -> list:
    """
    Divide the original list into named parts using the given ratios.

    Args:
        original (list): The original list to be divided.
        size (int): Max size of the parts.
        ratios (list): Ratios to divide the list by.
        shuffle (bool): Whether to shuffle the list before dividing.

    Returns:
        list: List of sublists divided into named parts.
    """
    assert len(original) > 0

    ratios = turn_size_into_ratios(len(original), size)

    assert abs(1 - sum(ratios)) < 0.1 # "Number of ratios must match number of named parts."

    logger.info("Dividing list into {} parts of {} elements max.", size, ratios)
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


def get_dataset_by_named_parts_ratios(original: list, named_parts_ratios:dict, shuffle=True) -> dict:
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
    parts_name = named_parts_ratios.keys()
    parts_ratio = [named_parts_ratios[part_name] for part_name in parts_name]
    parts_lists = get_sublists_from_named_parts(original, parts_name, parts_ratio, shuffle)
    named_parts_list = zip(parts_name, parts_lists)
    
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



def partition_dataset_by_n_parts(original_dataset_path: str, n_parts: int, test_set_val_size:dict, write_path='', structure_order=['parts', 'set_types', 'elements'], shuffle=True) -> dict:
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
    assert len(images_labels["images"]) > 0

    dataset = build_dataset_structure(n_parts, SET_TYPES, ELEMENTS, structure_order)

    if write_path:
            build_dataset_structure_on_disk(write_path, n_parts)

    for element in ELEMENTS:
        for part, sublist in enumerate(get_sublists_from_n_parts(images_labels[element], n_parts, shuffle)):
            part = str(part + 1)
            for set_type, files_paths in get_dataset_by_named_parts_ratios(sublist, test_set_val_size, shuffle).items():
                dataset[part][set_type][element] = files_paths  

                if write_path:
                    write_files(write_path, part, set_type, element, files_paths)

    logger.info("Dataset partitioning complete")
    return dataset




def partition_dataset_by_size(original_dataset_path:str, size:int, test_set_val_size:dict, write_path='', structure_order=['parts', 'set_types', 'elements'], shuffle=True) -> dict:
    """
    Partition the dataset into specified parts and optionally write to disk.

    Args:
        original_dataset_path (str): Path to the original dataset.
        size (int): Maximum number of elements in one part.
        test_set_val_size (list): Ratios for dividing test/validation sets.
        write_path (str): Path to write the new dataset structure.
        structure_order (list): Order in which to nest the structure.
        shuffle (bool): Whether to shuffle the dataset before partitioning.

    Returns:
        dict: Dictionary representing the new dataset structure.
    """
    original_dataset_path = Path(original_dataset_path)
    write_path = Path(write_path) if write_path else ''

    images_labels = get_images_labels(original_dataset_path)
    assert len(images_labels["images"]) > 0

    index = get_sublists_from_size(images_labels["images"], size, shuffle)
    parts = len(index)
    logger.info("Partitioning dataset from {} into {} parts of {} elements.", original_dataset_path, parts, size)
    
    dataset = build_dataset_structure(parts, SET_TYPES, ELEMENTS, structure_order)

    if write_path:
            build_dataset_structure_on_disk(write_path, parts)

    for element in ELEMENTS:
        for part, sublist in enumerate(get_sublists_from_size(images_labels[element], size, shuffle)):
            part = str(part + 1)
            for set_type, files_paths in get_dataset_by_named_parts_ratios(sublist, test_set_val_size, shuffle).items():
                dataset[part][set_type][element] = files_paths

                if write_path:
                        write_files(write_path, part, set_type, element, files_paths)

    logger.info("Dataset partitioning complete")
    return dataset


def replace_category(input_file, replacement_dict):
    """
    Replace values in the first column of a space-separated file based on a replacement dictionary.
    The new file will be created in the original directory, and the old file will be moved to a new 'old_' directory.

    Args:
        input_file (str or Path): Path to the input file.
        replacement_dict (dict): Dictionary mapping old values to new values.

    Returns:
        tuple: A tuple containing two integers - number of lines modified and total lines processed.
    """
    lines_modified = 0
    total_lines = 0
    
    # Convert to Path object if it's not already
    input_file = Path(input_file)
    
    # Get the directory and filename
    input_dir = input_file.parent
    filename = input_file.name
    old_dir = input_dir.parent / f"old_{input_dir.name}"
    
    # Create the 'old_' directory if it doesn't exist
    old_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths for the new file and the old file
    new_file = input_file
    old_file = old_dir / filename
    temp_file = new_file.with_suffix(new_file.suffix + '.temp')
    
    # logger.info(f"Starting to process file: {input_file}")
    # logger.info(f"New file will be created at: {new_file}")
    # logger.info(f"Original file will be moved to: {old_file}")
    
    try:
        with input_file.open('r') as infile, temp_file.open('w') as outfile:
            for line in infile:
                total_lines += 1
                columns = line.strip().split()
                if columns:
                    original_value = columns[0]
                    # Replace the first column if it's in the replacement dictionary
                    new_value = replacement_dict.get(original_value, original_value)
                    columns[0] = new_value
                    
                    if new_value != original_value:
                        lines_modified += 1
                        logger.info(f"Line {total_lines}: Replaced '{original_value}' with '{new_value}'")
                    else:
                        # logger.debug(f"Line {total_lines}: No replacement for '{original_value}'")
                        pass
                # Write the modified (or original) line to the output file
                outfile.write(' '.join(columns) + '\n')
        
        # Move the original file to the 'old_' directory
        shutil.move(str(input_file), str(old_file))
        
        # Rename the temporary file to the original filename
        temp_file.rename(new_file)
        
        # logger.info(f"Finished processing file: {input_file}")
        # logger.info(f"Total lines processed: {total_lines}")
        # logger.info(f"Lines modified: {lines_modified}")
        # logger.info(f"Original file moved to: {old_file}")
        # logger.info(f"New file created at: {new_file}")
        
        return lines_modified, total_lines
    
    except IOError as e:
        logger.error(f"Error processing file {input_file}: {str(e)}")
        raise


def modify_yaml_and_map_positions(yaml_file: str, remove_dict: dict) -> dict:
    """
    Modify the YAML file by removing elements that are keys in the provided dictionary,
    and create a mapping of old positions to new positions.

    Args:
        yaml_file (str): Path to the YAML file.
        remove_dict (dict): Dictionary whose keys will be removed from the YAML file.

    Returns:
        dict: A dictionary mapping old positions to new positions.
    """
    logger.info(f"Starting to process YAML file: {yaml_file}")

    try:
        # Read the YAML file
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        if 'names' not in data:
            raise KeyError("'names' key not found in the YAML file")

        original_names = data['names']
        logger.info(f"Original names: {original_names}")

        # Remove elements that are keys in remove_dict
        new_names = [name for name in original_names if name not in remove_dict]
        logger.info(f"New names after removal: {new_names}")

        # Create mapping of old positions to new positions
        position_map = {}
        for old_pos, name in enumerate(original_names):
            if name in new_names:
                new_pos = new_names.index(name)
                position_map[old_pos] = new_pos
                logger.info(f"Mapped: {name} from position {old_pos} to {new_pos}")
            else:
                logger.info(f"Removed: {name} from position {old_pos}")

        # Update the YAML file
        # data['names'] = new_names
        # with open(yaml_file, 'w') as file:
        #     yaml.dump(data, file)

        logger.info(f"Updated YAML file with new names")
        logger.info(f"Position mapping: {position_map}")

        position_map = {str(key):str(value) for key,value in position_map.items()}

        return position_map

    except Exception as e:
        logger.error(f"An error occurred while processing {yaml_file}: {str(e)}")
        raise


def modify_yaml_and_merge_labels(yaml_file: str, remove_dict: dict) -> dict:
    """
    Modify the YAML file by removing elements that are keys in the provided dictionary,
    preserve the file format, and create a mapping of old positions to new positions.

    Args:
        yaml_file (str): Path to the YAML file.
        remove_dict (dict): Dictionary whose keys will be removed from the YAML file.

    Returns:
        dict: A dictionary mapping old positions to new positions.
    """
    logger.info(f"Starting to process YAML file: {yaml_file}")

    try:
        # Initialize ruamel.yaml
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        # Read the YAML file
        with open(yaml_file, 'r') as file:
            data = yaml.load(file)

        if 'names' not in data:
            raise KeyError("'names' key not found in the YAML file")

        original_names = data['names']
        logger.info(f"Original names: {original_names}")

        # Remove elements that are keys in remove_dict
        new_names = [name for name in original_names if name not in remove_dict]
        logger.info(f"New names after removal: {new_names}")

        # Create mapping of old positions to new positions
        position_map = {}
        for old_pos, name in enumerate(original_names):
            if name in new_names:
                new_pos = new_names.index(name)
                position_map[old_pos] = new_pos
                logger.info(f"Mapped: {name} from position {old_pos} to {new_pos}")
            else:
                logger.info(f"Removed: {name} from position {old_pos}")

        # Update the YAML file
        data['names'] = new_names
        data['nc'] = len(new_names)  # Update the number of classes

        with open(yaml_file, 'w') as file:
            yaml.dump(data, file)

        logger.info(f"Updated YAML file with new names")

        position_map_swapped_str = {str(key):str(value) for key,value in position_map.items()}
        logger.info(f"Position mapping: {position_map_swapped_str}")

        return position_map_swapped_str


    except Exception as e:
        logger.error(f"An error occurred while processing {yaml_file}: {str(e)}")
        raise


import logging
import os
from typing import Dict

import ruamel.yaml


def map_yaml_positions_and_add_new_labels(
    original_file: str, destination_file: str, new_file_name: str = "merged.yaml"
) -> dict:
    """
    Maps positions between two YAML files of a specific shape, merges unique new elements
    from destination to original while maintaining alphabetical order,
    and creates a new YAML file with the merged results.

    Args:
        original_file (str): Path to the original YAML file.
        destination_file (str): Path to the destination YAML file.
        new_file_name (str, optional): Name for the new merged YAML file. Defaults to "merged.yaml".

    Returns:
        dict: A dictionary mapping original positions to destination positions (or -1 for added elements).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing YAML files: {original_file}, {destination_file}")

    try:
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True

        # Load YAML files
        with open(original_file, "r") as f_orig, open(destination_file, "r") as f_dest:
            original_data = yaml.load(f_orig)
            print(original_data)
            destination_data = yaml.load(f_dest)
            print(destination_data)

        # Extract and validate names
        original_names = original_data.get("names", [])
        destination_names = destination_data.get("names", [])
        if not isinstance(original_names, list) or not isinstance(destination_names, list):
            raise ValueError("'names' key must be a list in both YAML files.")

        # Combine, de-duplicate, and sort names alphabetically
        merged_names = sorted(set(original_names + destination_names))

        # Create position map
        position_map = {}
        for dest_idx, name in enumerate(destination_names):
            try:
                orig_idx = original_names.index(name)
                position_map[orig_idx] = merged_names.index(name)  # Map to new position
            except ValueError:
                # Name not in original, so it's a new addition
                position_map[dest_idx] = -1  # Indicate added element

        # Update original data (for the new file)
        new_data = original_data.copy()
        new_data["names"] = merged_names
        new_data["nc"] = len(merged_names)

        # Create new file path in the same directory as the original
        new_file_path = os.path.join(os.path.dirname(original_file), new_file_name)

        # Write the merged data to the new file
        with open(new_file_path, "w") as f_new:
            yaml.dump(new_data, f_new)

        logger.info(f"Created new YAML file: {new_file_path}")

        position_map = {str(key):str(value) for key,value in position_map.items()}
        logger.info(f"Position mapping: {position_map}")

        return position_map

    except (FileNotFoundError, KeyError, ValueError, ruamel.yaml.YAMLError) as e:
        logger.error(f"Error processing YAML files: {e}")
        raise