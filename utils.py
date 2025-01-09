import os
import json
import logging


def get_logger(file_name):
    log_format = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
    logger = logging.getLogger(file_name)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger.handlers = [console_handler]

    return logger


def load_jsonl(file_path):
    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]


def write_jsonl(data, file_path):
    with open(file_path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def find_jsonl_files(data_dir):
    return [f for f in os.listdir(data_dir) if f.endswith(".jsonl")]


def is_test_file(filename):
    return any(
        test_word in filename for test_word in ["test", "tests", "e2e", "testing"]
    )


def make_patch_from_prfiles(prfiles, *, test, modified_only=False):
    lines = []
    for prfile in prfiles:
        if "patch" not in prfile:
            # TODO: this happens with added files, we only have a content url
            continue
        status = prfile["status"]
        if status == "added":
            previous_filename = "dev/null"
            filename = prfile["filename"]
            if modified_only:
                continue
        elif status == "removed":
            previous_filename = prfile.get("previous_filename", prfile.get("filename"))
            filename = "dev/null"
            if modified_only:
                continue
        else:
            filename = prfile.get("filename")
            previous_filename = prfile.get("previous_filename", filename)

        if test != any(is_test_file(name) for name in (filename, previous_filename)):
            continue

        hunks = prfile["patch"]
        if status == "added":
            lines.append(
                f"""diff --git a/{filename} b/{filename}
new file mode 100644
--- /dev/null
+++ b/{filename}
{hunks}\n"""
            )
        elif status == "removed":
            lines.append(
                f"""diff --git a/{previous_filename} b/{previous_filename}
deleted file mode 100644
--- a/{previous_filename}
+++ /dev/null
{hunks}\n"""
            )
        else:
            lines.append(
                f"""diff --git a/{previous_filename} b/{filename}
--- a/{previous_filename}
+++ b/{filename}
{hunks}\n"""
            )

    return "\n".join(lines)


logger = get_logger(__name__)
