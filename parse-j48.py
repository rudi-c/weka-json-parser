#!/usr/bin/python
# Parses the output of weka.classifiers.trees.J48
# Made by Rudi Chen (Advecticity), 2014
#
# Usage : ./parse-j48.py [input_filename]
# If no input file is given, the input will be read from stdin.
#
# Sample input :

# J48 pruned tree
# ------------------
 
# outlook = sunny
# |   humidity <= 75: yes (2.0)
# |   humidity > 75: no (3.0)
# outlook = overcast: yes (4.0)
# outlook = rainy
# |   windy = TRUE: no (2.0)
# |   windy = FALSE: yes (3.0)
# outlook = custom
# |   humidity = '(-inf--1.0]': no (4.0)
# |   humidity = '(-1.0-5.0]': yes (1.0)
# |   humidity = '(5.0-inf)': no (2.0)


# Sample output :
# ["outlook", 
#   [["=", "sunny", ["humidity", 
#                       [["<=", "75", "yes"], 
#                       [">", "75", "no"]]]], 
#   ["=", "overcast", "yes"], 
#   ["=", "rainy", ["windy", 
#                       [["=", "TRUE", "no"], 
#                       ["=", "FALSE", "yes"]]]], 
#   ["=", "custom", ["humidity", 
#                       [["=", [-Infinity, -1.0], "no"], 
#                       ["=", [-1.0, 5.0], "yes"], 
#                       ["=", [5.0, Infinity], "no"]]]]]]


# The output is printed to screen - use output redirection to save to file.

import json
import re
import os
import sys

re_head = re.compile("J48 (un)?pruned tree")
re_divider_line = re.compile("^-*\n$")
re_blank_line = re.compile("^[ \t\n]*$")
re_splitter = re.compile("[ :]")
re_range = re.compile(
    "^'\(" \
    "(-inf|-?[0-9]+(\.[0-9]+)?)" \
    "-" \
    "(-?[0-9]+(\.[0-9]+)?\]|inf\))" \
    "'$")

def parse_value(token):
    """Returns an float if the token represents a number, a range if the token
    represents a range of numbers, otherwise return the token as is."""
    try:
        return float(token)
    except ValueError:
        # Look for ranges of the form '(start-end]', ' included
        if re_range.match(token):
            range_str = token[2:-2]

            # Careful not to use a minus sign as a dash.
            separator_dash = range_str.find("-", 1)
            return (parse_value(range_str[:separator_dash]), 
                    parse_value(range_str[separator_dash+1:]))
        else:
            # Not a number or range - so it must be nominal, leave it as it.
            return token


def parse_line(line):
    """Split the line into a tuple
    (depth, feature, comparator, value, classification/None)"""
    # Avoid empty strings from double whitespaces and the likes.
    split = [ l for l in re_splitter.split(line) if len(l) > 0 ]
    depth = 0
    for part in split:
        if part == "|":
            depth += 1 
        else:
            break
    return (depth, split[depth], split[depth + 1], 
            parse_value(split[depth + 2]),
            split[depth + 3] if len(split) > depth + 3 else None)


def parse_tree(lines):
    """Parses input lines into a Node, a recursive data structure."""
    current_index = [0] # need mutable container because of closure limitations
    def parse(current_depth):
        node_feature = None
        children = []
        while current_index[0] < len(lines):
            line = lines[current_index[0]]
            depth, feature, comparator, value, classif = parse_line(line)
            if depth < current_depth:
                # Finished parsing this node.
                break
            elif depth == current_depth:
                if node_feature is None:
                    node_feature = feature
                elif node_feature != feature:
                    raise Exception("Error : Feature mismatch - expected %s" \
                        "but got : \n%s" \
                          % (node_feature, line))

                # Another branch
                current_index[0] += 1
                if classif is None:
                    children.append((comparator, value, 
                                     parse(current_depth + 1)))
                else:
                    children.append((comparator, value, classif))
            else:
                raise Exception("Error : Input jumps two levels at once\n%s." \
                                % line)

        return (node_feature, children)

    return parse(0)


def get_tree_lines(lines):
    """Return the lines of the input that correspond to the tree."""
    tree_lines = []
    for i in range(0, len(lines) - 2):
        if re_head.match(lines[i]):
            assert re_divider_line.match(lines[i + 1]) and \
                   re_blank_line.match(lines[i + 2]), \
                   "Input not in expected format."
            for l in lines[i+3:]:
                if re_blank_line.match(l):
                    return tree_lines
                else:
                    tree_lines.append(l[:-1]) # remove newline at the end

    raise Exception("Error : Failed to find tree in input.")


def main(argv):

    if len(argv) > 0:
        input_filename = argv[0]
        if os.path.isfile(input_filename):
            f = open(input_filename)
            lines = f.readlines()
            f.close()
        else:
            raise Exception("Error : File %s not found!" % input_filename)
    else:
        lines = sys.stdin.readlines()

    if len(lines) == 0:
        raise Exception("Error : Empty input!")

    tree_lines = get_tree_lines(lines)
    tree = parse_tree(tree_lines)
    print json.dumps(tree)


main(sys.argv[1:])