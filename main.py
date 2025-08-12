import os
import json
import requests
from requests.auth import HTTPBasicAuth

xray_client_id = os.getenv("xray_client_id")
xray_client_secret = os.getenv("xray_client_secret")

projectKey = os.getenv("projectKey")
issueKey = os.getenv("issueKey")
versionName = os.getenv("versionName")
ITProjectData = os.getenv("ITProjectData")
ITNSProjectData = os.getenv("ITNSProjectData")
ITNPProjectData = os.getenv("ITNPProjectData")

jira_url = os.getenv("jira_url")
jira_api_token = os.getenv("jira_api_token")
jira_email = "jananipriya.s@cprime.com"

TEST_EXCE_KEY = "MTSD-91"
JENKINS_CASE_TEST_KEY = "MTSD-87"

XRAY_GRAPHQL_URL = "https://xray.cloud.getxray.app/api/v2/graphql"
XRAY_AUTH_URL = "https://xray.cloud.getxray.app/api/v2/authenticate"


def get_xray_token():
    payload = {
        "client_id": xray_client_id,
        "client_secret": xray_client_secret
    }
    resp = requests.post(XRAY_AUTH_URL, json=payload)
    resp.raise_for_status()
    # The token is returned as a plain string, not JSON
    return resp.text.strip().strip('"')

def get_test_run_id(auth_token, test_exec_key, test_key):
    query = f"""
    query {{
      getTestRuns(jql: "testExecKey = '{test_exec_key}' AND testKey = '{test_key}'") {{
        id
      }}
    }}
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = requests.post(XRAY_GRAPHQL_URL, json={"query": query}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    runs = data.get("data", {}).get("getTestRuns", [])
    return runs[0]["id"] if runs else None

def update_test_status(test_exec_key, test_key, status="PASSED"):
    print(f"📌 Updating {test_key} in execution {test_exec_key} to {status}...")

    # Step 1: Authenticate
    auth_token = get_xray_token()

    # Step 2: Find the Test Run ID
    test_run_id = get_test_run_id(auth_token, test_exec_key, test_key)
    if not test_run_id:
        print("❌ Could not find Test Run ID for that test in this execution.")
        return

    # Step 3: Update the status
    mutation = f"""
    mutation {{
      updateTestRunStatus(
        id: "{test_run_id}",
        status: "{status}"
      )
    }}
    """
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(XRAY_GRAPHQL_URL, json={"query": mutation}, headers=headers)

    if resp.status_code == 200:
        print("✅ Test case updated successfully!")
        print(resp.json())
    else:
        print(f"❌ Failed to update test: {resp.status_code}")
        print(resp.text)

def main():
    print("✅ Reading variables from Jenkins...")
    print(f"Xray Client ID: {xray_client_id}")
    print(f"Xray Client Secret: {xray_client_secret}")
    print(f"Project Key: {projectKey}")
    print(f"Issue Key: {issueKey}")
    print(f"Version Name: {versionName}")
    print(f"ITProjectData: {ITProjectData}")
    print(f"ITNSProjectData: {ITNSProjectData}")
    print(f"ITNPProjectData: {ITNPProjectData}")
    print(f"Jira URL: {jira_url}")
    print(f"Jira API Token: {jira_api_token}")
    update_test_status(TEST_EXCE_KEY,JENKINS_CASE_TEST_KEY, "PASS")

if __name__ == "__main__":
    main()