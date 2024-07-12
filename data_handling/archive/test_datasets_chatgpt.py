import os
import shutil
from pathlib import Path

import pytest
from dataset_partition import (ELEMENTS, SET_TYPES, build_dataset_structure,
                               build_dataset_structure_on_disk,
                               get_dataset_by_named_parts_ratios,
                               get_dataset_paths_by_elements,
                               get_images_labels, get_sublists_from_n_parts,
                               get_sublists_from_named_parts,
                               get_sublists_from_ratios, partition_dataset,
                               turn_parts_into_ratios, write_files)

# Define dummy paths and data
DUMMY_DATASET_PATH = Path("dummy_dataset")
DUMMY_NEW_DATASET_PATH = Path("new_dummy_dataset")

@pytest.fixture
def setup_dummy_dataset():
    # Create a dummy dataset structure
    DUMMY_DATASET_PATH.mkdir(exist_ok=True)
    for set_type in SET_TYPES:
        set_type_path = DUMMY_DATASET_PATH / set_type
        set_type_path.mkdir()
        for element in ELEMENTS:
            element_path = set_type_path / element
            element_path.mkdir()
            # Create dummy files
            for i in range(10):
                (element_path / f"{element}_{i}.txt").write_text(f"{element} content {i}")

    yield
    
    # Cleanup
    shutil.rmtree(DUMMY_DATASET_PATH)
    if DUMMY_NEW_DATASET_PATH.exists():
        shutil.rmtree(DUMMY_NEW_DATASET_PATH)

def test_build_dataset_structure():
    structure = build_dataset_structure(3, SET_TYPES, ELEMENTS)
    assert '1' in structure and 'train' in structure['1'] and 'images' in structure['1']['train']

def test_build_dataset_structure_on_disk(setup_dummy_dataset):
    build_dataset_structure_on_disk(DUMMY_NEW_DATASET_PATH, 3)
    assert DUMMY_NEW_DATASET_PATH.exists()
    for part in range(1, 4):
        assert (DUMMY_NEW_DATASET_PATH / str(part)).exists()

def test_get_dataset_paths_by_elements(setup_dummy_dataset):
    paths = get_dataset_paths_by_elements(DUMMY_DATASET_PATH)
    assert isinstance(paths, dict) and 'train' in paths and 'images' in paths['train']

def test_get_images_labels(setup_dummy_dataset):
    data = get_images_labels(DUMMY_DATASET_PATH)
    assert 'images' in data and len(data['images']) == 30

def test_turn_parts_into_ratios():
    ratios = turn_parts_into_ratios(3)
    assert sum(ratios) == 1

def test_get_sublists_from_ratios():
    original_list = list(range(100))
    ratios = [0.2, 0.3, 0.5]
    sublists = get_sublists_from_ratios(original_list, ratios)
    assert len(sublists) == 3
    assert sum(len(sublist) for sublist in sublists) == 100

def test_get_sublists_from_n_parts():
    original_list = list(range(100))
    sublists = get_sublists_from_n_parts(original_list, 3)
    assert len(sublists) == 3
    assert sum(len(sublist) for sublist in sublists) == 100

def test_get_sublists_from_named_parts():
    original_list = list(range(100))
    named_parts = ['part1', 'part2', 'part3']
    named_sublists = get_sublists_from_named_parts(original_list, named_parts)
    assert len(named_sublists) == 3

def test_get_dataset_by_named_parts_ratios():
    original_list = list(range(100))
    named_parts = ['part1', 'part2', 'part3']
    ratios = [0.2, 0.3, 0.5]
    dataset = get_dataset_by_named_parts_ratios(original_list, named_parts, ratios)
    assert len(dataset) == 3

def test_write_files(setup_dummy_dataset):
    files_to_write = [DUMMY_DATASET_PATH / 'train' / 'images' / f'images_{i}.txt' for i in range(5)]
    write_files(DUMMY_NEW_DATASET_PATH, '1', 'train', 'images', files_to_write)
    for i in range(5):
        assert (DUMMY_NEW_DATASET_PATH / '1' / 'train' / 'images' / f'images_{i}.txt').exists()

def test_partition_dataset(setup_dummy_dataset):
    dataset = partition_dataset(DUMMY_DATASET_PATH, 3, [0.2, 0.3, 0.5], write_path=DUMMY_NEW_DATASET_PATH)
    assert '1' in dataset and 'train' in dataset['1'] and 'images' in dataset['1']['train']
    assert DUMMY_NEW_DATASET_PATH.exists()
    for part in range(1, 4):
        assert (DUMMY_NEW_DATASET_PATH / str(part)).exists()
