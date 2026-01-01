"""
Sandbox runners for isolated code execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict
import os
import subprocess
import sys
import tempfile


class SandboxProvider(Enum):
    LOCAL = "local"
    DOCKER = "docker"
    E2B = "e2b"


@dataclass
class SandboxResult:
    status: str
    stdout: str
    stderr: str
    returncode: int
    execution_mode: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "execution_mode": self.execution_mode,
        }


class SandboxRunner(ABC):
    @abstractmethod
    def run(self, script_content: str, timeout: int = 60) -> SandboxResult:
        pass


class LocalSandboxRunner(SandboxRunner):
    def __init__(self, working_dir: str = ".", env: Optional[Dict[str, str]] = None):
        self.working_dir = working_dir
        self.env = env

    def run(self, script_content: str, timeout: int = 60) -> SandboxResult:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=self.working_dir
        ) as temp_script:
            temp_script.write(script_content)
            temp_script_path = temp_script.name

        try:
            result = subprocess.run(
                [sys.executable, temp_script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir,
                env=self.env if self.env is not None else os.environ.copy(),
            )

            status = "success" if result.returncode == 0 else "failure"
            return SandboxResult(
                status=status,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                execution_mode=SandboxProvider.LOCAL.value,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                status="timeout",
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds.",
                returncode=-1,
                execution_mode=SandboxProvider.LOCAL.value,
            )
        except Exception as exc:
            return SandboxResult(
                status="error",
                stdout="",
                stderr=str(exc),
                returncode=-1,
                execution_mode=SandboxProvider.LOCAL.value,
            )
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)


class DockerSandboxRunner(SandboxRunner):
    def __init__(
        self,
        docker_image: str = "cesi-ptc:latest",
        workdir: str = "/sandbox",
        output_dir: Optional[str] = None,
        network: str = "none",
        memory: str = "256m",
        cpus: str = "0.5",
    ):
        self.docker_image = docker_image
        self.workdir = workdir
        self.output_dir = output_dir
        self.network = network
        self.memory = memory
        self.cpus = cpus

    def run(self, script_content: str, timeout: int = 60) -> SandboxResult:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_name = "agent_script.py"
            script_path = temp_path / script_name
            script_path.write_text(script_content, encoding="utf-8")

            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{temp_dir}:{self.workdir}:rw",
                "-w",
                self.workdir,
                "--network",
                self.network,
                "--memory",
                self.memory,
                "--cpus",
                self.cpus,
            ]

            if self.output_dir:
                abs_output_dir = os.path.abspath(self.output_dir)
                os.makedirs(abs_output_dir, exist_ok=True)
                cmd.extend(
                    [
                        "-v",
                        f"{abs_output_dir}:/sandbox/output:rw",
                        "-e",
                        "PTC_OUTPUT_DIR=/sandbox/output",
                    ]
                )

            cmd.extend(
                [
                    self.docker_image,
                    "python",
                    script_name,
                ]
            )

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                status = "success" if result.returncode == 0 else "failure"
                return SandboxResult(
                    status=status,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    execution_mode=SandboxProvider.DOCKER.value,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    status="timeout",
                    stdout="",
                    stderr=f"Docker execution timed out after {timeout} seconds.",
                    returncode=-1,
                    execution_mode=SandboxProvider.DOCKER.value,
                )
            except FileNotFoundError:
                return SandboxResult(
                    status="error",
                    stdout="",
                    stderr="Docker not found. Install Docker or use local sandbox.",
                    returncode=-1,
                    execution_mode=SandboxProvider.DOCKER.value,
                )
            except Exception as exc:
                return SandboxResult(
                    status="error",
                    stdout="",
                    stderr=str(exc),
                    returncode=-1,
                    execution_mode=SandboxProvider.DOCKER.value,
                )


class E2BSandboxRunner(SandboxRunner):
    def __init__(
        self,
        api_key: Optional[str] = None,
        template: str = "python",
    ):
        self.api_key = api_key or os.environ.get("E2B_API_KEY")
        if not self.api_key:
            raise RuntimeError("E2B_API_KEY is required for E2B sandbox.")

        self.template = template
        self._mode = None
        self._client = None

        try:
            from e2b_code_interpreter import CodeInterpreter

            self._mode = "code_interpreter"
            self._client = CodeInterpreter
        except ImportError:
            try:
                from e2b import Sandbox

                self._mode = "sandbox"
                self._client = Sandbox
            except ImportError as exc:
                raise ImportError(
                    "E2B SDK not installed. Install e2b or e2b-code-interpreter."
                ) from exc

    def run(self, script_content: str, timeout: int = 60) -> SandboxResult:
        if self._mode == "code_interpreter":
            return self._run_code_interpreter(script_content, timeout)
        return self._run_sandbox(script_content, timeout)

    def _run_code_interpreter(self, script_content: str, timeout: int) -> SandboxResult:
        sandbox = None
        try:
            sandbox = self._client(api_key=self.api_key)
            if hasattr(sandbox, "__enter__"):
                with sandbox as ctx:
                    return self._run_e2b_execution(ctx, script_content, timeout)
            return self._run_e2b_execution(sandbox, script_content, timeout)
        except Exception as exc:
            return SandboxResult(
                status="error",
                stdout="",
                stderr=str(exc),
                returncode=-1,
                execution_mode=SandboxProvider.E2B.value,
            )
        finally:
            if sandbox and hasattr(sandbox, "close"):
                sandbox.close()

    def _run_sandbox(self, script_content: str, timeout: int) -> SandboxResult:
        sandbox = None
        try:
            try:
                sandbox = self._client(self.template, api_key=self.api_key)
            except TypeError:
                sandbox = self._client(api_key=self.api_key, template=self.template)
            return self._run_e2b_execution(sandbox, script_content, timeout)
        except Exception as exc:
            return SandboxResult(
                status="error",
                stdout="",
                stderr=str(exc),
                returncode=-1,
                execution_mode=SandboxProvider.E2B.value,
            )
        finally:
            if sandbox and hasattr(sandbox, "close"):
                sandbox.close()

    def _run_e2b_execution(
        self,
        sandbox: object,
        script_content: str,
        timeout: int,
    ) -> SandboxResult:
        try:
            execution = sandbox.run_code(script_content, timeout=timeout)
        except TypeError:
            execution = sandbox.run_code(script_content)

        stdout = getattr(execution, "stdout", "") or ""
        stderr = getattr(execution, "stderr", "") or ""
        error = getattr(execution, "error", None)

        status = "success" if error is None else "failure"
        return SandboxResult(
            status=status,
            stdout=stdout,
            stderr=stderr or (str(error) if error else ""),
            returncode=0 if error is None else 1,
            execution_mode=SandboxProvider.E2B.value,
        )


def get_sandbox_runner(
    provider: str,
    *,
    docker_image: str = "cesi-ptc:latest",
    output_dir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    working_dir: str = ".",
    e2b_api_key: Optional[str] = None,
    e2b_template: str = "python",
) -> SandboxRunner:
    provider_value = provider.lower()
    if provider_value == SandboxProvider.DOCKER.value:
        return DockerSandboxRunner(
            docker_image=docker_image,
            output_dir=output_dir,
        )
    if provider_value == SandboxProvider.E2B.value:
        return E2BSandboxRunner(api_key=e2b_api_key, template=e2b_template)
    if provider_value == SandboxProvider.LOCAL.value:
        return LocalSandboxRunner(working_dir=working_dir, env=env)

    raise ValueError(f"Unknown sandbox provider: {provider}")
