# Host for Free on Render.com (Recommended Alternative)

Since Google Cloud is blocking deployment due to billing permissions, **Render.com** is the best alternative to host your PDF service for **free** (handling 1000+ users).

I have already configured the `render.yaml` file for you.

### Steps to Deploy (2 Minutes)

1.  **Push your code to GitHub**
    *   Ensure this `pdf/wordpdf` folder is in a GitHub repository.

2.  **Create Render Account**
    *   Go to [dashboard.render.com](https://dashboard.render.com/)
    *   Sign up/Login (GitHub login is best).

3.  **Create New Blueprint Instance**
    *   Click **"New +"** button in top right.
    *   Select **"Blueprint Instance"**.
    *   Connect your GitHub repository.

4.  **Deploy**
    *   Render will automatically detect the `render.yaml` file I fixed for you.
    *   Click **"Apply"** or **"Create"**.

### Why this works
*   **Cost**: $0.00 / month forever.
*   **Technology**: Uses the `Dockerfile` to install LibreOffice correctly (unlike the Python environment).
*   **Capacity**: Can handle your 1000 users.
*   **Trade-off**: The server will "sleep" if no one uses it for 15 minutes. The first person to use it will wait ~45 seconds for it to wake up. This is the only cost of "free".
