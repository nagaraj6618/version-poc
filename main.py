import os

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


def update_test_status(test_key, status="PASS"):
    print(f"📌 Updating test {test_key} to {status}...")

    # Xray test execution API endpoint
    url = f"{jira_url}/rest/raven/1.0/import/execution"

    payload = {
        "testExecutionKey": test_key,
        "info": {
            "summary": "Automated test execution from Jenkins",
            "description": "Updated by Jenkins pipeline after main() run",
            "version": versionName,
            "user": jira_email
        },
        "tests": [
            {
                "testKey": test_key,
                "status": status
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        auth=HTTPBasicAuth(jira_email, jira_api_token)
    )

    if response.status_code == 200:
        print("✅ Test case updated successfully!")
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