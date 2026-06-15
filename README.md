# DupeCleaner Pro

DupeCleaner Pro is a fast, visually-stunning desktop application designed to find and safely remove duplicate files (photos, videos, and documents) from your local directories. It uses powerful hashing algorithms (like `imagehash` for photos, `videohash` for videos, and exact `SHA-256` matching for documents) to smartly auto-select the duplicates for deletion.

## Features
* **Modern GUI**: A beautiful, premium dark theme built with PyQt6.
* **Smart Auto-Select**: One click to automatically select all but the oldest/original copy of duplicate groups.
* **Intelligent Comparison**: Detects visually similar photos and videos, not just exact bit-for-bit copies.
* **Portable & Fast**: Runs entirely offline on your local machine.

## How to Run

### Method 1: Using the Executable (.exe)
1. Head over to the **Releases** tab on the right side of this GitHub page.
2. Download the `DupeCleanerPro.zip` file and extract it.
3. Double-click `DupeCleanerPro.exe` to run the app instantly!

### Method 2: Running from Source
If you prefer running the source code directly:
1. Clone this repository or download it as a ZIP.
2. Simply double-click the **`Run_DupeCleaner.bat`** file.
   * *This will automatically create a python environment, install dependencies, and launch the app for you!*

## Building the Executable Yourself
If you want to compile the `.exe` yourself from the source code:
1. Make sure you have Python installed.
2. Double-click **`build.bat`**.
3. PyInstaller will compile the app and output it to the `dist/DupeCleanerPro` folder.
