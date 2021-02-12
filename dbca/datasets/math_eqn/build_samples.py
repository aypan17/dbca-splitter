from pathlib import Path
import string
import networkx as nx
import numpy as np
import ast
from tqdm import tqdm
import os
import io

from dbca.datasets.math_eqn.equation_sample import EquationSample
from dbca.sample_set import SampleSet
from dbca.storage import SampleStore


UNA_OPS = {'inv', 'pow2', 'pow3', 'pow4', 'pow5', 'sqrt', 'exp', 'ln', 'abs', 'sign', 'ten', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan', 'acot', 'asec', 'acsc', 'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch', 'asinh', 'acosh', 'atanh', 'acoth', 'asech', 'acsch', 'f'}
BIN_OPS = {'add', 'sub', 'mul', 'div', 'pow', 'rac', 'derivative', 'g'}
DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
COUNTER = {'<s>': 0, '</s>': 0, '<pad>': 0, '(': 0, ')': 0, '<SPECIAL_5>': 0, '<SPECIAL_6>': 0, '<SPECIAL_7>': 0, '<SPECIAL_8>': 0, '<SPECIAL_9>': 0, 'pi': 0, 'E': 0, 'x': 0, 'y': 0, 'z': 0, 't': 0, 'a0': 0, 'a1': 0, 'a2': 0, 'a3': 0, 'a4': 0, 'a5': 0, 'a6': 0, 'a7': 0, 'a8': 0, 'a9': 0, 'abs': 0, 'acos': 0, 'acosh': 0, 'acot': 0, 'acoth': 0, 'acsc': 0, 'acsch': 0, 'add': 0, 'asec': 0, 'asech': 0, 'asin': 0, 'asinh': 0, 'atan': 0, 'atanh': 0, 'cos': 0, 'cosh': 0, 'cot': 0, 'coth': 0, 'csc': 0, 'csch': 0, 'derivative': 0, 'div': 0, 'exp': 0, 'f': 0, 'g': 0, 'inv': 0, 'ln': 0, 'mul': 0, 'pow': 0, 'pow2': 0, 'pow3': 0, 'pow4': 0, 'pow5': 0, 'rac': 0, 'sec': 0, 'sech': 0, 'sign': 0, 'sin': 0, 'sinh': 0, 'sqrt': 0, 'sub': 0, 'tan': 0, 'tanh': 0, 'ten': 0, 'I': 0, 'INT': 0, 'FLOAT': 0, '-': 0, '.': 0, '10^': 0, 'Y': 0, "Y'": 0, "Y''": 0, '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0}


# Given a list of tokens in prefix form, convert to a list of NetworkX graphs.
def prefix_to_tree(token_list):
    samples = []
    num_extra_tokens = []
    for i in range(len(token_list)):
        tree = nx.DiGraph()
        counter = dict(COUNTER)
        _, idx = _prefix_to_tree(token_list[i], counter, tree)
        assert idx == len(token_list[i])
        samples.append(EquationSample(tree, f's_{i}'))
    return samples

def _prefix_to_tree(tokens, counter, tree, idx=0):
    """
    Performs a preorder traversal of tokens to build a tree.

    Parameters
    ----------
    tokens
        A list of the tokens in the tree formed from preorder traversal 
    counter
        A dictionary of {Symbol_name: # occurrences}
    tree
        A networkX DiGraph object for storing the tree
    
    Returns
    -------
    root
        The string of the current node
    idx
        The idx of the next token.
    """
    token = tokens[idx]
    idx += 1
    if token in BIN_OPS or token in UNA_OPS:
        counter[token] += 1
        num = f'_{counter[token]}' if counter[token] > 9 else f'_0{counter[token]}'
        root = token + num
        tree.add_node(root)
        left, idx = _prefix_to_tree(tokens, counter, tree, idx=idx)         
        tree.add_edge(root, left)

        if token in BIN_OPS:
            right, idx = _prefix_to_tree(tokens, counter, tree, idx=idx)
            tree.add_edge(root, right)

    elif token in COUNTER or token in ['INT+', 'INT-']:
        token = 'INT' if token in ['INT+', 'INT-'] else token
        counter[token] += 1
        num = f'_{counter[token]}' if counter[token] > 9 else f'_0{counter[token]}'
        root = token + num
        tree.add_node(token)

        # Ignore numbers
        if token == 'INT':
            while idx < len(tokens) and tokens[idx] in DIGITS:
                idx += 1

    else:
        print(tokens)
        print(idx)
        print(token)
        assert False

    return root, idx


def build_samples(path, logger):
    assert os.path.isfile(path)
    logger.info(f"Loading data from {path} ...")
    with io.open(path, mode='r', encoding='utf-8') as f:
        lines = [line.rstrip().split('|') for line in f]
    data = [xy.split('\t') for _, xy in lines]
    data = [xy[0].split()[2:] for xy in data if len(xy) == 2]
    logger.info(f"Loaded {len(data)} equations from the disk.")
    return prefix_to_tree(data)