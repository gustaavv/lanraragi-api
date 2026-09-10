import subprocess
import json
import time


def restart(container_name: str):
    subprocess.run(
        ["docker", "restart", container_name],
        capture_output=True,
        text=True,
        check=True,
    )


def wait_for_healthy(container_name, timeout=60, interval=1):
    """
    Wait until the specified Docker container becomes healthy.

    Args:
        container_name (str): Container name or ID.
        timeout (int): Maximum waiting time in seconds, default 60 seconds.
        interval (float): Interval between checks in seconds, default 2 seconds.

    Returns:
        bool: True if the container becomes healthy before timeout.

    Raises:
        Exception: If the container does not exist or docker inspect fails.
        TimeoutError: If the container does not become healthy within the given timeout.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Execute docker inspect to get container info
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                check=True,
            )
            container_info = json.loads(result.stdout)[0]
        except subprocess.CalledProcessError as e:
            # Container does not exist or docker command failed
            raise Exception(f"Docker inspect failed: {e.stderr.strip()}") from e
        except (json.JSONDecodeError, IndexError) as e:
            raise Exception(f"Failed to parse docker inspect output: {e}") from e

        # Extract health status
        health_status = container_info.get("State", {}).get("Health", {}).get("Status")

        if health_status == "healthy":
            return True

        # Wait for some time before retrying
        time.sleep(interval)

    # Timeout
    raise TimeoutError(
        f"Container '{container_name}' did not become healthy within {timeout} seconds."
    )
