def output_file(path, data):
    with open(path, "a") as file:
        file.write(f"{data}\n")


def output(sink, **kwargs):
    print(kwargs)
