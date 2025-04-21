import os
import sys
from datetime import date

# python retry_testing_tool tries sleep infix directory


def main():
    """
    Main function to handle retry logic for a testing tool.

    This function reads the maximum number of retries, an infix string, and a base directory
    from the command-line arguments. It creates or updates a file to track the number of retries
    and exits with a status code indicating whether the maximum retries have been reached.

    Command-line arguments:
        sys.argv[1] (int): Maximum number of retries allowed.
        sys.argv[2] (str): Infix string to include in the filename.
        sys.argv[3] (str): Base directory for the file (default is the current directory).

    Behavior:
        - Creates a file named `retry_testing_tool_<infix>-<date>-retries-<max_retry>` in the
          specified base directory.
        - Reads the current retry count from the file. If the file does not exist, it starts
          with a retry count of 1.
        - If the retry count reaches or exceeds the maximum retries, the file is deleted, and
          the program exits with a status code of 0.
        - Otherwise, it increments the retry count, updates the file, and exits with a status
          code of 1.

    Exceptions:
        - Handles `FileNotFoundError` when the file does not exist during read or delete operations.

    Exit codes:
        - 0: Maximum retries reached, or file successfully deleted.
        - 1: Retry count incremented and updated in the file.
    """
    max_retry = int(sys.argv[1])
    infix = sys.argv[2]
    base_dir = sys.argv[3] or "."

    filename = (
        f"{base_dir}/retry_testing_tool_{infix}-{date.today()}-retries-{max_retry}"
    )

    try:
        last_try = int(open(filename, "r").read())
    except FileNotFoundError:
        last_try = 1

    if last_try >= max_retry:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        sys.exit(0)

    print(f"{filename}: {last_try}/{max_retry}")
    open(filename, "w").write(str(last_try + 1))

    sys.exit(1)


if __name__ == "__main__":
    main()
