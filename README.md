<div align="center">
  
# 🧹 DupeCleaner Pro
**A fast, visually-stunning, and intelligent duplicate file finder.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

[Features](#-features) • [Installation](#-installation) • [How to Use](#-how-to-use) • [Building the Executable](#-building-from-source)

</div>

---

DupeCleaner Pro is an intelligent desktop application designed to find and safely remove duplicate files (photos, videos, and documents) from your local directories. Instead of relying purely on file names or sizes, it uses powerful hashing algorithms to detect **visually similar** media, helping you reclaim wasted storage space quickly.

## ✨ Features
* 🎨 **Premium Modern GUI**: A beautiful, dark-themed interface built from the ground up using PyQt6.
* 🧠 **Intelligent Visual Matching**: 
  * Uses `imagehash` to detect visually identical photos (even if they are resized or compressed).
  * Uses `videohash` to find duplicate videos based on their actual visual frames.
  * Uses exact `SHA-256` matching for documents.
* ⚡ **Smart Auto-Select**: With one click, the app automatically selects all duplicate copies for deletion while safely preserving your original/oldest file.
* 🔒 **100% Local & Private**: No internet required. All processing is done locally on your machine.

---

## 🚀 Installation

There are two ways to get DupeCleaner Pro running on your machine:

### Option 1: The One-Click Executable (No Python Required)
If you just want to use the application without dealing with code, download the pre-compiled version!
1. Go to the [**Releases**](../../releases) tab on the right side of this GitHub page.
2. Download the `DupeCleanerPro-Win64.zip` file and extract it.
3. Double-click `DupeCleanerPro.exe` to run the app instantly!

### Option 2: Run from Source Code
If you are a developer or prefer running the source directly:
1. Clone this repository or download it as a ZIP.
2. Double-click the **`Run_DupeCleaner.bat`** file.
   * *This script automatically sets up a Python virtual environment, installs all necessary dependencies from `requirements.txt`, and launches the app!*

---

## 📖 How to Use

1. **Select a Directory**: Click the "Browse..." button to choose the folder you want to scan.
2. **Choose Filters**: Select which types of files you want to look for (Visual Photos, Visual Videos, or Documents).
3. **Start Scan**: Click the big blue **Start Scan** button. A progress bar will show the progress of the scanning and hashing phase.
4. **Smart Auto-Select**: Once the scan is complete, click **Smart Auto-Select** to instantly mark all duplicate copies for deletion, keeping the oldest original safe.
5. **Execute Deletion**: Click the red **Execute Deletion** button to permanently reclaim your disk space.

---

## 🛠️ Building from Source

If you want to modify the code and compile your own standalone `.exe` file to share with others:

1. Make sure you have [Python 3](https://www.python.org/downloads/) installed.
2. Clone this repository to your local machine.
3. Double click the **`build.bat`** script.
4. PyInstaller will automatically collect all dependencies and package the app. 
5. You will find your fully compiled application inside the newly generated `dist/DupeCleanerPro/` folder!

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! 
Feel free to check out the [issues page](../../issues).

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).
