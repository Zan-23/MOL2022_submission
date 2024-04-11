import os
import re
from time import sleep


def capture_command_output(command, log_command_output=False):
    """
    Function stores the input that would otherwise be written to stdout
    """
    stream = os.popen(command)
    output = stream.read().strip()
    if log_command_output:
        print("Job submitted successfully")
    return output


def submit_job(sequence: str, email: str = None, log_command_output: bool = False) -> str:
    print("Submitting job to JPred")
    base_command = f"python -m jpredapi submit --mode=single --format=raw --seq={sequence}"
    if email:
        base_command += f" --email={email}"

    command_output = capture_command_output(base_command)
    assert len(command_output) > 0, "Command output is empty"
    if log_command_output:
        print(f"Command output:\n{command_output}")

    # regex to capture href content, job links look like this
    # <a href="job/JPRED4_20210827142626">job/JPRED4_20210827142626</a>
    job_id = re.search(r'href="http://www.compbio.dundee.ac.uk/(.*?)">', command_output).group(1)
    job_id = job_id.split("/")[-1].split("?")[1].strip()
    print(f"Job ID: {job_id}")
    return job_id


def check_job_finished(job_id: str, log_command_output: bool = False) -> bool:
    print(f"Checking job status for job ID: {job_id}")
    base_command = f"python -m jpredapi status --jobid={job_id}"
    command_output = capture_command_output(base_command)

    assert len(command_output) > 0, "Command output is empty"
    if log_command_output:
        print(f"Job status: {command_output}")

    # check if this string is present in the output
    finished_job = f"Job {job_id} finished. Results available at the following URL:".lower()
    if finished_job in command_output.lower():
        return True
    else:
        return False


def save_results(job_id: str, result_dir: str = "jpred_files/query_results/"):
    print(f"Saving results for job ID: {job_id} to {result_dir}{job_id}")
    base_command = f"python -m jpredapi get_results --jobid={job_id} --results={result_dir} --extract"
    command_output = capture_command_output(base_command)

    assert len(command_output) > 0, "Command output is empty"
    print(f"Results saved successfully")
    return result_dir


def submit_job_and_retrieve_results(sequence: str, email: str = None, log_command_output: bool = False) -> str:
    job_id = submit_job(sequence, email, log_command_output)

    for i in range(10):
        if check_job_finished(job_id, log_command_output):
            break

        sleep_val = 5 + i
        if log_command_output:
            print(f"Job not finished yet, waiting for {sleep_val} seconds")
        sleep(sleep_val)

    print("Job finished, retrieving results")
    saved_path = save_results(job_id)
    return job_id, saved_path


def load_jal_view(filename: str) -> list:
    print(f"Loading jalview for file: {filename}")
    with open(filename, "r") as file:
        data = file.read()
    assert "JNETCONF" in data, "JNETCONF not found in the file"
    jnet_conf = [line for line in data.split("\n") if "JNETCONF" in line][0]
    conf_values = jnet_conf.split("Confidence of Jnet prediction 0 (low) -> 9 (high)")[1].strip()
    conf_list = [[j, int(i)] for j, i in enumerate(conf_values.split("|"))]

    return conf_list



