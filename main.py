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


if __name__ == "__main__":
    main()