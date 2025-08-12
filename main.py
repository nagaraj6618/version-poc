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

JENKINS_EXCE_TEST_KEY = "MTSD-87"

def update_test_status(test_key, status="PASSED"):
    print(f"📌 Updating test {test_key} to {status}...")

    # Step 1: Authenticate with Xray to get token
    auth_payload = {
        "client_id": xray_client_id,
        "client_secret": xray_client_secret
    }
    auth_response = requests.post(
        "https://xray.cloud.getxray.app/api/v2/authenticate",
        json=auth_payload
    )

    if auth_response.status_code != 200:
        print(f"❌ Failed to authenticate with Xray: {auth_response.status_code}")
        print(auth_response.text)
        return

    auth_token = auth_response.json()

    # Step 2: Send GraphQL mutation to update test status
    graphql_url = "https://xray.cloud.getxray.app/api/v2/graphql"

    mutation = f"""
    mutation {{
      updateTestRunStatus(
        issueId: "{test_key}",
        status: {status}
      ) {{
        warnings
        errors
      }}
    }}
    """

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        graphql_url,
        json={"query": mutation},
        headers=headers
    )

    if response.status_code == 200:
        print("✅ Test case updated successfully!")
        print(response.json())
    else:
        print(f"❌ Failed to update test: {response.status_code}")
        print(response.text)


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
    update_test_status(JENKINS_EXCE_TEST_KEY, "PASS")

if __name__ == "__main__":
    main()