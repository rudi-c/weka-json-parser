#!/usr/bin/python
# Parses the output of weka.classifiers.trees.J48


import json
import re
import os
import sys

re_head = re.compile("J48 (un)?pruned tree")
re_divider_line = re.compile("^-*\n$")
re_blank_line = re.compile("^[ \t\n]*$")
re_splitter = re.compile("[ :]")

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
    return (depth, split[depth], split[depth + 1], split[depth + 2],
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
                    print "Error : Feature mismatch - expected %s but got :" \
                          % node_feature
                    print line
                    sys.exit(1)

                # Another branch
                current_index[0] += 1
                if classif is None:
                    children.append((comparator, value, 
                                     parse(current_depth + 1)))
                else:
                    children.append((comparator, value, classif))
            else:
                print "Error : Input jumps two levels at once."
                print line
                sys.exit(1)
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

    print "Error : Failed to find tree in input."
    sys.exit(1)


def main(argv):

    if len(argv) > 0:
        input_filename = argv[0]
        if os.path.isfile(input_filename):
            f = open(input_filename)
            lines = f.readlines()
            f.close()
        else:
            print "Error : File %s not found!" % input_filename
            sys.exit(1)
    else:
        lines = sys.stdin.readlines()

    if len(lines) == 0:
        print "Error : Empty input!"
        sys.exit(1)

    tree_lines = get_tree_lines(lines)
    tree = parse_tree(tree_lines)
    json.dumps(tree)


main(sys.argv[1:])