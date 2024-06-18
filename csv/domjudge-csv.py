#!/usr/bin/env python3

import argparse, csv, requests

parser = argparse.ArgumentParser()
parser.add_argument("URL", type=str, help="DOMjudge root URL")
parser.add_argument("CID", type=str, help="The contest ID")
parser.add_argument("-a", "--auth", type=str, help="Basic authorization header value")
args = parser.parse_args()

URL = args.URL
CID = args.CID
auth = args.auth

headers = {"accept": "application/json"}
if auth:
    headers.update({"Authorization": f"Basic {auth}"})

contest_url = f"{URL}/api/v4/contests/{CID}/scoreboard"
contest_params = {"strict": "false"}
results = requests.get(contest_url, headers=headers, params=contest_params).json()[
    "rows"
]

outputs = []
for result in results:
    output = {}

    team_id = result["team_id"]
    team_url = f"{URL}/api/v4/teams/{team_id}"
    team_name = requests.get(team_url, headers=headers).json()["name"]
    output["Team Name"] = team_name

    problems = result["problems"]
    score_total = 0
    participation = False
    for problem in problems:
        if problem["solved"]:
            output[problem["label"]] = 1
        else:
            if problem["num_judged"]:
                output[problem["label"]] = 0
            else:
                output[problem["label"]] = ""
        if problem["num_judged"]:
            participation = True

    if participation:
        output["Total"] = result["score"]["num_solved"]
    else:
        output["Total"] = ""

    outputs.append(output)

fields = outputs[0].keys()
with open("output.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()
    for output in outputs:
        writer.writerow(output)
