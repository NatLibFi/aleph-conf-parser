#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
 *
 * The following is the entire license notice for the Python code in this file.
 *
 * Parser for Aleph configuration files
 *
 * Copyright (C) 2017 University Of Helsinki (The National Library Of Finland)
 *
 * aleph-conf-parser program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * aleph-conf-parser is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * The above is the entire license notice
 * for the Python code in this file.
 *
'''

'''
- Check option checks if there are non-whitespace values in places where should be whitespace.
- Print option prints configuration files lines with column headers. Supports only files with values like "COL.  1" in the table key.
'''

import sys, re

# Read file, deletes newline, return list
def read_file(filename):
    with open(filename, 'r') as f:
        return [x.strip() for x in f]

# Drop comments, return list 
def drop_comments(data):
    comment_re = re.compile('^[^\!]')
    new_list = filter(comment_re.match,data)
    return new_list

# Read length of conf fields, return list 
def read_length(data):
    frame = []
    end = 0
    for i in data:
        if re.match('^!\s+[0-9]\s+[0-9]\s+[0-9]', i) or end == 1:
            if re.match('^!\s+[0-9]\s+[0-9]\s+[0-9]', i):
                frame.append(i)
                end = 1
                continue
            if end == 1:
                frame.append(i)
                return frame

# Check for sequence "!!" when not and end of line
def is_exclamation_was_not_line_not_last(data, index, latest_char):
    if data[index] == "!" and index != (len(data) - 1) and latest_char != "-":
        return True
    else:
        return False

# Check for sequence "-!" when not at end of line
def is_exclamation_was_line_not_last(data, index, latest_char):
    if data[index] == "!" and index != (len(data) - 1) and latest_char == "-":
        return True
    else:
        return False

# Check for sequence "!-"
def is_line_was_exclamation(data, index, latest_char):
    if data[index] == "-" and latest_char == "!":
        return True
    else:
        return False

# Check for sequence "--"
def is_line_was_line(data, index, latest_char):
    if data[index] == "-" and latest_char == "-":
        return True
    else:
        return False

# Check for ending sequence (line ends always with "!" or ">")
def is_ending(data, index):
    if (data[index] == "!" or data[index] == ">") and index == (len(data) - 1 ):
        return True
    else:
        return False

# Calculate configuration blocks, return list of tuples (block length, spaces between)
def calculate_blocks(data):
    latest_char = ""
    block_size = 0
    space_size = 0
    block_sizes = []
    space_sizes = []
    for i in range(len(data)):
        if is_exclamation_was_not_line_not_last(data, i, latest_char):
            block_size += 1
            latest_char = "!"
        elif is_exclamation_was_line_not_last(data, i, latest_char):
            space_sizes.append(space_size)
            space_size = 0
            block_size += 1
            latest_char = "!"
        elif is_ending(data, i):
            block_size += 1
            if increase_last_block_size == 1:
                block_sizes.append(100)
                space_sizes.append(space_size)
                space_sizes.append(0)
            else:
                block_sizes.append(block_size)
                space_sizes.append(space_size)
                space_sizes.append(0)
        elif is_line_was_exclamation(data, i, latest_char):
            space_size += 1
            block_sizes.append(block_size)
            block_size = 0
            latest_char = "-"
        elif is_line_was_line(data, i, latest_char):
            space_size += 1
        else:
            block_sizes.append(block_size)
            block_size = 0
    return zip(block_sizes, space_sizes)

# Use blocks to read values from data, return list of strings 
def parse_row(blocks, data):
    my_data = []
    current_index = 0
    for i in blocks:
        s = slice(current_index, (i[0] + current_index))
        current_index += i[0] + i[1]
        my_data.append(data[s])
    return my_data

# Get empty space index
def parse_empty(blocks):
    my_data = []
    my_empty = []
    current_index = 0
    for i in blocks:
        end = current_index + int(i[0])
        my_data.append((current_index, end))
        current_index += i[0] + i[1]
    for i in range(len(my_data) - 1):
        my_empty.append((my_data[i][1], my_data[i+1][0]))
    return my_empty

# Input: List of all rows, returns list of lists
def parse_all(blocks, data):
    my_data = []
    for i in data:
        my_data.append(parse_row(blocks, i))
    return my_data

# Print format '[title]: [data]'
def print_row_titles(titles, data, blocks):
    data = parse_row(blocks, data)
    titled = zip(titles, data)
    for (title, data) in titled:
        print (title + ": " + data)

# Print all values
def print_all_titles(titles, data, blocks):
    for i in data:
        print_row_titles(titles, i, blocks)
        print("\n")

# Read titles from config-file
def get_titles(data):
    my_titles = []
    re_title = re.compile('\!.*COL.*[0-9]\..*;')
    keep_next = 0
    for i in range(len(data)):
        if keep_next == 1:
            title = data[i]
            title = re.sub('[^0-9a-zA-Z ]', '', title)
            title = title.lstrip()
            my_titles.append(title)
            keep_next = 0
        if re.match(re_title, data[i]) is not None:
            keep_next = 1
    return my_titles

# Check empty spaces for invalid values
def check_errors(blocks, values):
    empty_index = parse_empty(blocks)
    for i in values:
        found = 0
        for j, h in empty_index:
            empty_block = i[j:h]
            empty_block = re.sub(r'\s+', '', empty_block)
            if (re.compile(r'\S').search(empty_block)) is not None:
                found = 1
        if found == 1:
            print("[ERROR] Empty block contains a value in following line:")
            print(i)

# Check if file is given in arguments
if len(sys.argv) != 3:
    print("Usage: $0 <file> <option>")
    print("Options: print/check")
    sys.exit()

filename = sys.argv[1]
option = sys.argv[2]
increase_last_block_size = 1 #Overrides last block size with 100
full_data = read_file(filename)
config_values = drop_comments(full_data)
block_headers = read_length(full_data)
data_blocks = calculate_blocks(block_headers[1])
configurations = parse_all(data_blocks, config_values)

# Aleph configs titles aren't consistent. Could make option for custom titles.
titles = get_titles(full_data)

if option == "print":

    # Printing file information
    print("File: " + filename)
    print("Lines: " + str(len(full_data)))
    print("Not commented lines: " + str(len(drop_comments(full_data))))
    print("Format: " + block_headers[1])
    print("Format (numbered): " + str(data_blocks) + "\n")

    # Printing data with titles
    print_all_titles(titles, config_values, data_blocks)

if option == "check":
    # Check for errors in empty spaces
    check_errors(data_blocks, config_values)
