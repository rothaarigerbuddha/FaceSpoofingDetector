# Frontier Frontend - Getting Started Guide

Welcome to the Frontier Frontend repository! This guide is written specifically for beginners. Even if you have **no prior experience** with Next.js or Node.js, you will be able to get this project running on your local machine by following these step-by-step instructions.

---

## 🛠️ Prerequisites

Before running the project, you need to install a program called **Node.js**. Node.js is required to run modern web applications like this one.

### 1. Install Node.js
1. Go to the official Node.js website: [https://nodejs.org/](https://nodejs.org/)
2. Download the **LTS (Long Term Support)** version. (This is recommended for most users).
3. Run the downloaded installer and follow the standard installation steps (you can just click "Next" through all the default options).
4. *To verify the installation:* Open your computer's terminal (Command Prompt or PowerShell on Windows, or Terminal on Mac) and type:
   ```bash
   node -v
   ```
   If it prints out a version number (like `v20.11.0`), you are good to go!

---

## 🚀 Running the Project

Follow these steps to start the application on your computer.

### Step 1: Open the terminal in the project folder
1. Open the `frontier-frontend` folder on your computer.
2. Open a terminal inside this folder:
   - **Windows:** Click on the folder address bar at the top, type `cmd`, and press **Enter**.
   - **Mac:** Right-click the folder and select **New Terminal at Folder**.
   - Alternatively, open your code editor (like VS Code), go to **File > Open Folder**, select `frontier-frontend`, and then open the built-in terminal (**Terminal > New Terminal**).

### Step 2: Install dependencies
Modern web projects rely on external packages (libraries) to work. We need to download them first.
In your terminal, type the following command and press **Enter**:
```bash
npm install
```
*(Wait a minute or two for everything to download. You will see a progress bar or a list of packages being installed).*

### Step 3: Set up environment variables
The project needs to know where the backend API is located. We manage this using an environment file.
1. Look for a file named `.env.example` inside the `frontier-frontend` folder.
2. Duplicate this file and rename the copy to exactly **`.env`** (with the dot at the beginning).
   - *If you are using Windows and it doesn't let you start a file with a dot, just open `.env.example` in Notepad, click "Save As", change the "Save as type" to "All Files", and save it as `.env`.*
3. Open the new `.env` file. It should contain something like this:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:5160
   ```
   *(If you are running the backend locally on port 5160, leave it as is. If your backend is hosted online, replace the URL with your live backend API link).*

### Step 4: Start the application
Now, you are ready to run the website! Type the following command in your terminal and press **Enter**:
```bash
npm run dev
```

### Step 5: View it in your browser
Once you see a message in the terminal saying **"Ready in xxx ms"** or something similar, the app is running!
1. Open your web browser (Chrome, Firefox, Safari, etc.).
2. Go to the following address:
   **[http://localhost:3000](http://localhost:3000)**

🎉 **Congratulations! You should now see the Frontier website running locally!**

---

## 🛑 How to Stop the Project
When you are done testing the project, you need to turn off the local server.
1. Go back to the terminal where you ran `npm run dev`.
2. Press **`Ctrl + C`** on your keyboard.
3. If it asks "Terminate batch job (Y/N)?", type **`Y`** and press **Enter**.

---

## 📝 Frequently Asked Questions (FAQ)

**Q: I get an error saying `'npm' is not recognized as an internal or external command`.**
**A:** This means Node.js is not installed correctly, or your terminal hasn't recognized the installation yet. Try restarting your computer. If that doesn't work, try reinstalling Node.js.

**Q: The website loads, but it says "Network Error" or data isn't loading.**
**A:** This means the frontend cannot reach the backend API. Make sure your backend `.NET` project is actively running, and verify that the URL in your `.env` file (e.g., `http://localhost:5160`) matches the backend's actual URL.
