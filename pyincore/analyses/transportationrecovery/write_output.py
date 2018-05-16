import os


def write_output(output, path):
    """
    output the result
    :param output: the data set of output
    :param path: the relative path of output file
    :return: path and path length
    """


    # create Output folder if it does not exist
    if not os.path.exists('Output'):
        os.makedirs('Output')

    output.to_csv(os.path.join("Output", path), index=False)
    return None
