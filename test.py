def txt_to_list(path):
    sentences = []
    with open("path", "r") as a_file:
        for line in a_file:
            stripped_line = line.strip()
            sentences.append(stripped_line)
    return sentences
