#!/usr/bin/env python3

import argparse, csv, psutil, requests, subprocess
import os
import time

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("URL", type=str, help="DOMjudge root URL")
parser.add_argument("CID", type=str, help="The contest ID")
parser.add_argument("PROBLEM_ID", type=str, help="The problem ID")
parser.add_argument(
    "COMMAND", type=str, help="Command for each submission source to get output"
)
parser.add_argument("-a", "--auth", type=str, help="Basic authorization header value")
parser.add_argument(
    "-d", "--delay", type=float, default=0.05, help="Internal delay value in seconds"
)
parser.add_argument(
    "--save-temps", type=str, help="Directory path to save temporary files"
)
parser.add_argument(
    "-t", "--timeout", type=int, default=5, help="Timeout value in seconds"
)
args = parser.parse_args()

URL = args.URL
CID = args.CID
PROBLEM_ID = args.PROBLEM_ID
COMMAND = args.COMMAND
auth = args.auth
delay = args.delay
save_temps = args.save_temps
timeout = args.timeout

headers = {"accept": "application/json"}
if auth:
    headers.update({"Authorization": f"Basic {auth}"})

contest_url = f"{URL}/api/v4/contests/{CID}/submissions"
contest_params = {"strict": "false"}
submissions = [
    submission
    for submission in requests.get(
        contest_url, headers=headers, params=contest_params
    ).json()
    if submission["problem_id"] == PROBLEM_ID
]

print(f"There are {len(submissions)} submissions.")

for i, submission in enumerate(submissions):
    message = f"[Processing] Downloading submission #{i + 1}..."
    print(message, end="", flush=True)

    id = submission["id"]
    submission["proc"] = subprocess.Popen(
        f"curl -H 'Authorization: Basic {auth}' '{URL}/api/v4/submissions/{id}/files?strict=false' | busybox unzip -p -",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )    
    time.sleep(delay)

    print("\r" + " " * len(message), end="\r", flush=True)

for i, submission in enumerate(submissions):
    message = f"[Checking] Downloading submission #{i + 1}..."
    print(message, end="", flush=True)

    proc = submission["proc"]
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(f"Failed to download submission source (id = {submission["id"]}). Exiting...")
        print("[stdout] ", stdout)
        print("[stderr] ", stderr)
        exit(1)
    submission["src"] = stdout

    if save_temps:
        with open(os.path.join(save_temps, submission["id"]), 'w') as file:
            file.write(submission["src"])

    print("\r" + " " * len(message), end="\r", flush=True)

for i, submission in enumerate(submissions):
    message = f"[Processing] Judging submission #{i + 1}..."
    print(message, end="", flush=True)

    submission["output"] = {}
    team_id = submission["team_id"]
    team_url = f"{URL}/api/v4/teams/{team_id}"
    team_name = requests.get(team_url, headers=headers).json()["name"]
    submission["output"]["Team Name"] = team_name
    submission["output"]["Submission ID"] = submission["id"]

    if not save_temps:
        my_stdin = subprocess.PIPE
    else:
        my_stdin = open(os.path.join(save_temps, submission["id"]), 'r')
    proc = subprocess.Popen(
        COMMAND,
        shell=True,
        stdin=my_stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if not save_temps:
        proc.stdin.write(submission["src"])
        proc.stdin.close()
    submission["proc"] = proc

    print("\r" + " " * len(message), end="\r")

for i, submission in enumerate(submissions):
    message = f"[Checking] Judging submission #{i + 1}..."
    print(message, end="", flush=True)

    proc = submission["proc"]
    try:
        proc.wait(timeout=timeout)
        output = proc.stdout.read()
    except subprocess.TimeoutExpired:
        process = psutil.Process(proc.pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()
        output = ""
    submission["output"]["Output"] = output

    print("\r" + " " * len(message), end="\r")

with open("output.csv", "w", newline="") as csvfile:
    fields = submissions[0]["output"].keys()
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()
    outputs = [submission["output"] for submission in submissions]
    for output in outputs:
        writer.writerow(output)
