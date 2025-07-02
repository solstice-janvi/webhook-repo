**action-repo**

This is a dummy GitHub repository created to demonstrate and test webhook functionality. It is configured to send webhook events for push and pull_request actions to a specified endpoint.

**Setup Instructions**
Follow these steps to set up this repository and configure its webhooks:

**Create a New GitHub Repository:**

Go to GitHub.

Enter action-repo as the Repository name.

Choose "Public" or "Private" as per your preference.

Check "Add a README file".

Click "Create repository".

Add a Dummy File (Optional but Recommended):

Once the repository is created, click "Add file" -> "Create new file".

Name the file dummy.txt.

Add some content like "This is a dummy file."

Commit the new file. This will trigger a push event.

Configure Webhooks:

Navigate to your action-repo on GitHub.

Click on Settings (usually located near the top right, below your repository name).

In the left sidebar, click on Webhooks.

Click the Add webhook button.

**Webhook Configuration Details:**

**Payload URL:** This is the URL where GitHub will send the webhook events.

If running webhook-repo locally: You will need to expose your local Flask server to the internet using a tool like ngrok. Once ngrok is running (e.g., ngrok http 5000), it will provide a public URL (e.g., https://your-random-subdomain.ngrok-free.app). Your Payload URL will be https://your-random-subdomain.ngrok-free.app/webhook.

If webhook-repo is deployed: Use the public URL of your deployed Flask application (e.g., https://your-app-name.render.com/webhook).

Content type: Select application/json.

**Secret:** Leave this empty for this demonstration. In a production environment, you would use a secret to verify the authenticity of GitHub's requests.

Which events would you like to trigger this webhook?

Select "Let me select individual events."

**Check the boxes for:**

Pushes

Pull requests

(Note: Merge events are implicitly handled by the pull_request event when its action is "closed" and merged is true.)

**Active:** Ensure this checkbox is ticked.

Click the Add webhook button.

Testing Webhook Events
Once your webhook-repo is running and its URL is configured as the webhook payload URL, you can test the events:

**Push Event:**

Make a small change to dummy.txt (or any file) in your action-repo.

Commit and push the changes.

Check the "Recent Deliveries" section under your webhook settings on GitHub to see if the delivery was successful (green checkmark).

Check your webhook-repo frontend to see the new push event.

**Pull Request Event:**

Create a new branch in your action-repo (e.g., git checkout -b feature-branch).

Make some changes in this new branch.

Push the feature-branch to GitHub.

Go to your action-repo on GitHub and create a new Pull Request from feature-branch to main (or master).

Check your webhook-repo frontend to see the new pull request event.

**Merge Event:**

After creating a Pull Request (as above), merge it into the base branch (e.g., main).

Check your webhook-repo frontend to see the new merge event.
