from dataclasses import dataclass
import os
import time
import json
import base64
import requests
from typing import Optional
from enum import Enum
from junitparser import JUnitXml, Skipped, Failure, Error
import yaml
import re
import string
import random
from threading import Thread


class UnitTestStatus(str, Enum):
    SKIPPED = "skipped"
    FAILED = "failed"
    PASSED = "passed"
    ERROR = "error"


def parse_xml(xml_string: str):
    junit_xml = JUnitXml.fromstring(xml_string)
    test_to_status = {}
    name_to_case = {}
    for suite in junit_xml:
        for case in suite:
            full_test_name = f"{case.classname}::{case.name}"
            if case.result:
                result = case.result[0]
                if isinstance(result, Skipped):
                    test_to_status[full_test_name] = UnitTestStatus.SKIPPED
                elif isinstance(result, Failure):
                    test_to_status[full_test_name] = UnitTestStatus.FAILED
                elif isinstance(result, Error):
                    test_to_status[full_test_name] = UnitTestStatus.ERROR
                else:
                    raise Exception(f"Unknown status for case result: {result}")
            else:
                test_to_status[full_test_name] = UnitTestStatus.PASSED
            name_to_case[full_test_name] = case
    return test_to_status


def parse_run_command_output(log: str):
    log_lines = log.split("\n")
    new_lines = []
    for line in log_lines:
        new_line = re.sub(r"\[[^\]]+\]\s+\|", "", line).strip()
        new_lines.append(new_line)
    new_log = "\n".join(new_lines)
    prefix = "\n!==================================!\nCustom command output:\n!==================================!\n"
    prefix_index = new_log.index(prefix)
    suffix = "!!============================!!"
    suffix_index = new_log.index(suffix, prefix_index + len(prefix), len(new_log))
    return new_log[prefix_index + len(prefix) : suffix_index]


def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def unique_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=4))


def create_run_id(repo, workflow_index, workflow_name):
    safe_chars = (
        ["|", "-", "&", "^", "%", "$", "#", "(", ")", "{", "}", "[", "]", ";", "<", ">"]
        + [c for c in string.ascii_lowercase]
        + [c for c in string.digits]
    )
    run_id = f"ces-{repo.lower()}-{'wfn' if workflow_name else 'wfc'}-{workflow_index}-{unique_id()}"
    return "".join([c if c in safe_chars else "-" for c in run_id])


class CESClient:
    def __init__(
        self,
        repo,
        workflow_index=None,
        workflow_name=None,
        workflow_content=None,
        version=None,
        base_url="http://localhost:5000",
        language=None,
        bearer_token_provider=None,
        use_workflow_as_is=False,
        docker_image_id=None,
        http_request_timeout=600,
    ):
        assert (
            workflow_name or workflow_content
        ), "Either workflow name or content must be provided"
        
        self.repo = repo
        self.language = language
        self.workflow_name = workflow_name
        self.workflow_content = (
            yaml.dump(workflow_content)
            if type(workflow_content) == dict
            else workflow_content
        )
        self.version = version
        self.base_url = base_url.rstrip("/")
        self.init_result = None
        self.end_result = None
        self.use_workflow_as_is = use_workflow_as_is
        self.docker_image_id = docker_image_id
        self.headers = {"Content-Type": "application/json"}
        self.bearer_token_provider = bearer_token_provider
        self.http_request_timeout = http_request_timeout
        self.heartbeat_alive = False
        self.heartbeat_thread = None
        self.run_id = create_run_id(repo, workflow_index, workflow_name)

        # self.add_install_packages_step()
        
    @property
    def short_id(self):
        return self.run_id
    
    @property
    def status(self):
        if self.heartbeat_alive:
            return "running"
        return "stopped"

    @property
    def install_packages_steps(self) -> list:
        result = []
        if self.language is None or self.language.lower() == "go":
            result.extend(
                [
                    {
                        "name": "Set up Go",
                        "uses": "actions/setup-go@v5",
                        "with": {"go-version": "stable"},
                    },
                    {"run": "go version"},
                ]
            )
        if self.language is None or self.language.lower() in [
            "javascript",
            "js",
            "typescript",
            "ts",
            "nodejs",
            "node",
        ]:
            result.extend(
                [
                    {
                        "name": "Set up Node.js",
                        "uses": "actions/setup-node@v4",
                        "with": {"node-version": "latest"},
                    },
                    {
                        "run": "node --version",
                    },
                ]
            )
        if self.language is None or self.language.lower() in ["rust"]:
            result.extend(
                [
                    {
                        "name": "Set up Rust",
                        "uses": "dtolnay/rust-toolchain@stable",
                    },
                    {
                        "run": "rustc --version",
                    },
                ]
            )
        return result

    def add_install_packages_step(self) -> str:
        workflow_content = yaml.safe_load(self.workflow_content)
        workflow_jobs = workflow_content["jobs"]
        setup_job_name = next(iter(workflow_jobs))
        # workflow_jobs[setup_job_name]["steps"].insert(0, {"run": self.install_packages_command})
        workflow_jobs[setup_job_name]["steps"] = (
            self.install_packages_steps + workflow_jobs[setup_job_name]["steps"]
        )
        self.workflow_content = yaml.dump(workflow_content)

    def setup_heartbeat(self) -> dict:
        # Make sure that init call has been made before pinging
        time.sleep(60)
        while self.heartbeat_alive and self.run_id:
            try:
                self.ping()
            except Exception as e:
                print(f"Failed to send heartbeat: {e}")
            time.sleep(60)

    def __enter__(self):
        url = f"{self.base_url}/api/ces/repo/initRun"
        data = {}
        if self.version:
            data["repoVersion"] = self.version
        if self.workflow_content:
            data["workflowContent"] = encode_base64(self.workflow_content)

        # Start heartbeat thread
        self.heartbeat_alive = True
        self.heartbeat_thread = Thread(target=self.setup_heartbeat)
        self.heartbeat_thread.start()
        failures = 0
        while True:
            try:
                if self.init_result is None:
                    self.init_result = self._send_and_raise_status(url=url, data=data)
                    if (
                        "InitSucceeded" not in self.init_result
                        or not self.init_result["InitSucceeded"]
                    ):
                        error = self.init_result.get("Log", self.init_result)
                        raise Exception(f"Failed to initialize workflow: {error}")

                # Install tree package
                self.run_command("apt-get install tree")
                break
            except Exception as e:
                failures += 1
                if (
                    "failed to invoke session because maximum alive sessions count"
                    in repr(e)  # 400 error
                    or "failed to allocate session from session pool"
                    in repr(e)  # 409 error
                    or "failed to invoke session because the session was failed to be invoked"
                    in repr(e)  # 409 error
                    or "Exception: HTTPError('5" in repr(e)  # 500 error
                ) and failures < 5:
                    print(
                        f"Failed to initialize session: {repr(e)}. Failure counter: {failures}. Retrying..."
                    )
                    # Wait a bit since session pool might be busy
                    if self.init_result is None:
                        time.sleep(60)
                else:
                    self.end_run()
                    raise e
        return self.run_id

    def __del__(self):
        return self.end_run()

    def __exit__(self, exc_type, exc_value, traceback):
        result = self.end_run()
        if exc_type:
            print(f"Exception occurred: {exc_value}")
            raise exc_value
        return result

    def end_run(self) -> str:
        if self.heartbeat_alive or self.heartbeat_thread is not None:
            self.heartbeat_alive = False
            self.heartbeat_thread.join()
            self.heartbeat_thread = None

        failures = 0
        while failures < 3:
            try:
                url = f"{self.base_url}/api/ces/repo/endRun"
                self.end_result = self._send_and_raise_status(url=url)
                print(f"End run result: {self.end_result}")
                break
            except Exception as e:
                failures += 1
                print(f"Failed to end run: {e}")

        return self.run_id

    def apply_patch(self, patch: str) -> dict:
        return self.run_command(
            command="\n",
            patch=patch,
        )

    def reset_file_state(self) -> dict:
        url = f"{self.base_url}/api/ces/repo/resetFileState"
        return self._send_and_raise_status(url=url)

    def run_tests_base(self, patch: str = None) -> dict:
        url = f"{self.base_url}/api/ces/repo/runTests"
        data = {}
        if self.workflow_content:
            data["workflowContent"] = encode_base64(self.workflow_content)
        if patch:
            data["patchContent"] = base64.b64encode(patch.encode()).decode()
        return self._send_and_raise_status(url=url, data=data)

    def run_tests(self, patch: str = None, report_location: str = None) -> dict:
        """Applies an optional patch, runs tests, and returns structured test output."""
        test_results = self.run_tests_base(patch=patch)

        structured_test_results = None
        report_location_contents = None
        if report_location:
            report_location_contents, parsed = self.gather_tests_output(report_location)
            for rlc, p in zip(report_location_contents, parsed):
                if not p:
                    continue
                try:
                    structured_test_result = parse_xml(rlc)
                    if structured_test_results is None:
                        structured_test_results = structured_test_result
                    else:
                        structured_test_results.update(structured_test_result)
                except Exception as e:
                    print(f"Failed to parse XML: {e}")
        return test_results, report_location_contents, structured_test_results

    def run_command(self, command: str, patch: str = None) -> dict:
        url = f"{self.base_url}/api/ces/repo/runCommand"
        data = {"command": encode_base64(command)}
        if patch:
            data["patchContent"] = encode_base64(patch)
        return self._send_and_raise_status(url=url, data=data)

    def run_and_parse_command(self, command: str, patch: str = None) -> str:
        return parse_run_command_output(self.run_command(command, patch)["Log"])

    def ping(self) -> dict:
        url = f"{self.base_url}/api/ces/repo/pingSession"
        return self._send_and_raise_status(
            url=url, method="get", params=["delayMilliseconds=30000"], stream=False
        )

    def _send_and_raise_status(
        self,
        url: str,
        data: Optional[dict] = None,
        method="post",
        params: Optional[list] = None,
        stream=True,
    ) -> dict:
        if params is None:
            params = []
        if self.repo:
            params.append(f"repo={self.repo}")
        if self.run_id:
            params.append(f"runId={self.run_id}")
        if self.workflow_name:
            params.append(f"workflowName={self.workflow_name}")
        # TODO: Add docker image id
        # if self.docker_image_id:
        #     params.append(f"imageId={self.docker_image_id}")
        params.append("sessionPoolId=graysand")
        url = f"{url}?{'&'.join(params)}"
        print(f"Sending {method} request to {url}, data: {json.dumps(data)}")

        if self.bearer_token_provider:
            headers = {
                **self.headers,
                "Authorization": "Bearer " + self.bearer_token_provider(),
            }
        else:
            headers = self.headers

        req_start_time = time.time()
        if method == "post":
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(data) if data else None,
                # 5 seconds to connect, custom timeout for the read operation
                timeout=(5, self.http_request_timeout),
                stream=stream,
            )
        elif method == "get":
            response = requests.get(
                url,
                headers=headers,
                data=json.dumps(data) if data else None,
                # 5 seconds to connect, custom timeout for the read operation
                timeout=(5, self.http_request_timeout),
                stream=stream,
            )
        else:
            raise Exception(f"Unknown method: {method}")

        response_content = ""
        if stream:
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                if chunk:
                    # Here you can parse the chunk (if it's valid JSON) and check for completion
                    if not '{"Message":"Request still in progress"}' in chunk.decode(
                        "utf-8"
                    ):
                        response_content += chunk.decode("utf-8")
                    else:
                        time.sleep(5)  # Wait for the next periodic update
                else:
                    break

        req_end_time = time.time()
        print(f"Request took {req_end_time - req_start_time} seconds")
        if stream:
            try:
                response_content = json.loads(response_content)
            except Exception as e:
                raise Exception(
                    f"Failed to send {method} request to {url}: {response_content}.\nException: {repr(e)}"
                )
        else:
            try:
                response_content = response.json()
            except Exception as e:
                response_content = response.text
        try:
            response.raise_for_status()
        except Exception as e:
            raise Exception(
                f"Failed to send {method} request to {url}: {response_content}.\nException: {repr(e)}"
            )

        if (
            stream
            and response_content
            and "Error" in response_content
            and response_content["Error"]
        ):
            raise Exception(
                f"Failed to send {method} request to {url}: {response_content}.\nError: {response_content['Message']}"
            )
        return response_content

    def list_files(self, path=None) -> list:
        try:
            if path:
                result = self.run_command(command=f"tree -J {path}")
            else:
                result = self.run_command(command="tree -J")
            return json.loads(re.sub("\n", "", parse_run_command_output(result["Log"])))
        except Exception as e:
            raise Exception(f"Failed to list files: {e}, raw output: {result}")
        
    def create_repro_patch(self, filename, contents):
        # Split the contents into lines
        lines = contents.split('\n')
        line_count = len(lines)
        patch_lines = [
            f"diff --git a/{filename} b/{filename}",
            f"new file mode 100644",
            f"--- /dev/null",
            f"+++ b/{filename}",
            f"@@ -0,0 +1,{line_count} @@",
        ]

        for line in lines:
            patch_lines.append(f"+{line}")

        return "\n".join(patch_lines) + "\n"
    
    def create_file(self, path: str, contents: str) -> dict:
        patch = self.create_repro_patch(path, contents)
        result = self.apply_patch(patch)
        retrieved_contents, _ = self.view_file(path)
        if "No such file or directory" in retrieved_contents:
            raise Exception(f"Failed to create script file: {retrieved_contents}")
        elif retrieved_contents.strip() != contents.strip():
            raise Exception(f"Script contents do not match: {retrieved_contents}")
        return result

    def execute_custom_script(
        self, command: str, script_path: str = None, script_contents: str = None
    ) -> dict:
        if script_path:
            self.create_file(script_path, script_contents)

        self.run_command(command=f"chmod +x {script_path}")
        result = parse_run_command_output(self.run_command(command=command)["Log"])
        return result

    def gather_tests_output(self, filepath: str) -> str:
        if filepath.endswith(".xml"):
            report_location_contents, parsed = self.view_file(filepath)
            return [report_location_contents], [parsed]
        else:
            files = self.list_files(filepath)
            files = [
                f["name"] for f in files[0]["contents"] if f["name"].endswith(".xml")
            ]

        report_location_contents_merged, parsed_merged = [], []
        for file in files:
            report_location_contents, parsed = self.view_file(
                os.path.join(filepath, file)
            )
            report_location_contents_merged.append(report_location_contents)
            parsed_merged.append(parsed)
        return report_location_contents_merged, parsed_merged

    def view_file(self, filepath: str) -> str:
        result = self.run_command(command=f"cat {filepath}")
        try:
            return parse_run_command_output(result["Log"]), True
        except Exception as e:
            return result["Log"], False
        
    def exec_run(self, cmd: str, *args, **kwargs) -> str:
        @dataclass
        class ExecResult:
            exit_code: int
            output: str
        
        output=self.run_and_parse_command(command=cmd)
        exit_code = self.run_and_parse_command(command="echo $?")
        return ExecResult(
            exit_code=int(exit_code),
            output=output.encode('utf-8'),
        )
        
    def put_archive(self, path: str, contents: str) -> str:
        result = self.run_command(command=f"echo $'{contents}' > {path}")
        return result
    
    def stop(self) -> str:
        self.__exit__(None, None, None)
        
    def remove(self) -> str:
        self.__exit__(None, None, None)
