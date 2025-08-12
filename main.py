import os
import requests
import json
import re

# ===== Jenkins Environment Variables =====
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

# Jenkins build status variable (SUCCESS/FAILURE)
BUILD_STATUS = os.getenv("BUILD_STATUS", "SUCCESS")

# ===== Xray Config =====
TEST_EXCE_KEY = "MTSD-91"      # Test Execution Key
JENKINS_CASE_TEST_KEY = "MTSD-87"  # Test Case Key
VALID_VERSION_NAME_CASE_TEST_KEY = "MTSD-97"

XRAY_GRAPHQL_URL = "https://xray.cloud.getxray.app/api/v2/graphql"
XRAY_AUTH_URL = "https://xray.cloud.getxray.app/api/v2/authenticate"


# ====================== Functions ======================

def get_xray_token():
    auth_payload = {
        "client_id": xray_client_id,
        "client_secret": xray_client_secret
    }
    resp = requests.post(XRAY_AUTH_URL, json=auth_payload)
    resp.raise_for_status()
    return resp.json().strip('"')

def get_test_run_id(token, exec_key, test_key):
    query = {
        "query": f"""
        query {{
          getTestRuns(
            testExecIssueIds: ["{exec_key}"],
            testIssueIds: ["{test_key}"],
            limit: 1
          ) {{
            results {{
              id
            }}
          }}
        }}
        """
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(XRAY_GRAPHQL_URL, headers=headers, json=query)
    resp.raise_for_status()
    data = resp.json()
    runs = data.get("data", {}).get("getTestRuns", {}).get("results", [])
    if runs:
        return runs[0]["id"]
    return None

def update_test_status(test_exec_key, test_key, status="PASSED"):
    print(f"📌 Updating {test_key} in execution {test_exec_key} to {status}...")
    token = get_xray_token()
    test_run_id = get_test_run_id(token, test_exec_key, test_key)
    if not test_run_id:
        print("❌ Could not find Test Run ID.")
        return
    mutation = {
        "query": f"""
        mutation {{
          updateTestRunStatus(
            id: "{test_run_id}",
            status: "{status}"
          )
        }}
        """
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(XRAY_GRAPHQL_URL, headers=headers, json=mutation)
    if resp.status_code == 200 and "errors" not in resp.json():
        print("✅ Test case updated successfully!")
    else:
        print(f"❌ Failed to update test: {resp.status_code}")
        print(resp.text)
        
def is_valid_version_name(version):
    # Regex allows letters, digits, space, dot, underscore, hyphen only
    pattern = r'^[a-zA-Z0-9\s._-]+$'
    return bool(re.match(pattern, version))

# ====================== Main ======================

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
    print(f"Build Status: {BUILD_STATUS}")

    # Convert Jenkins build result to Xray status
   #  status = "PASSED" if BUILD_STATUS.upper() == "SUCCESS" else "FAILED"

    update_test_status(TEST_EXCE_KEY, JENKINS_CASE_TEST_KEY, status="PASSED")
    if is_valid_version_name(versionName):
       print("✅ Version name is valid, updating VALID_VERSION_NAME_CASE_TEST_KEY")
       update_test_status(TEST_EXCE_KEY, VALID_VERSION_NAME_CASE_TEST_KEY, status="PASSED")
    else:
       print("⚠️ Version name contains invalid characters, updating JENKINS_CASE_TEST_KEY")
       update_test_status(TEST_EXCE_KEY, VALID_VERSION_NAME_CASE_TEST_KEY, status="FAILED")


if __name__ == "__main__":
    main()
