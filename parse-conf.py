#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Aleph configuration files have two styles of defining column names. Currently this script supports only one of them.
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

# Calculate configuration blocks, return list of tuples (block length, spaces between)
def calculate_blocks(data):
    latest_char = ""
    block_size = 0
    space_size = 0
    block_sizes = []
    space_sizes = []
    for i in range(len(data)):
        if data[i] == "!" and i != (len(data) - 1) and latest_char != "-":
            block_size += 1
            latest_char = "!"
        elif data[i] == "!" and i != (len(data) - 1) and latest_char == "-":
            space_sizes.append(space_size)
            space_size = 0
            block_size += 1
            latest_char = "!"
        elif (data[i] == "!" or data[i] == ">") and i == (len(data) - 1 ):
            block_size += 1
            if increase_last_block_size == 1:
                block_sizes.append(100)
                space_sizes.append(space_size)
                space_sizes.append(0)
            else:
                block_sizes.append(block_size)
                space_sizes.append(space_size)
                space_sizes.append(0)
        elif data[i] == "-" and latest_char == "!":
            space_size += 1
            block_sizes.append(block_size)
            block_size = 0
            latest_char = "-"
        elif data[i] == "-" and latest_char == "-":
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

# Check if file is given in arguments
if len(sys.argv) != 2:
    print("Usage: $0 <file>")
    sys.exit()


filename = sys.argv[1]
increase_last_block_size = 1 #Overrides last block size with 100
full_data = read_file(filename)
config_values = drop_comments(full_data)
block_headers = read_length(full_data)
data_blocks = calculate_blocks(block_headers[1])
configurations = parse_all(data_blocks, config_values)

# Aleph configs titles aren't consistent. Could make option for custom titles.
titles = get_titles(full_data)


# Printing file information
print("File: " + filename)
print("Lines: " + str(len(full_data)))
print("Not commented lines: " + str(len(drop_comments(full_data))))
print("Format: " + block_headers[1])
print("Format (numbered): " + str(data_blocks) + "\n")

# Printing data with titles
print_all_titles(titles, config_values, data_blocks)
