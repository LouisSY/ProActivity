# Installing Python 3.10.11 (Embedded) in macOS Wineskin

This guide provides a step-by-step process to install and configure the **Python 3.10.11 Embeddable Package** within a Wineskin wrapper. This method is preferred for Wine environments as it avoids complex Windows installers.

---

## Prerequisites

1.  **Wineskin Wrapper**: A configured wrapper (Recommended Engine: `Wine12CX24.7_7` or newer).
2.  **Python Embeddable Zip**: Download `python-3.10.11-embed-amd64.zip` from [Python.org](https://www.python.org/downloads/windows/).

---

## Installation Steps

### 1. File Deployment
1.  Right-click your **Wineskin App** and select **Show Package Contents**.
2.  Navigate to `drive_c/`.
3.  Create a folder named `python310`.
4.  Extract all files from the downloaded `.zip` into `drive_c/python310/`.

### 2. Enable `pip` Support
By default, the embedded version ignores local site-packages. You must manually enable it:
1.  Open `drive_c/python310/python310._pth` with a text editor.
2.  **Uncomment** (remove the `#`) the last line:
    ```text
    import site
    ```
3.  Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) and place it in `drive_c/python310/`.
4.  Open **Wineskin Advanced > Tools > Command Prompt (CMD)** and run:
    ```cmd
    C:\python310\python.exe C:\python310\get-pip.py
    ```

### 3. Configure Environment Variables
To call `python` and `pip` from any directory:
1.  Open **Wineskin Advanced > Tools > Registry Editor (regedit)**.
2.  Navigate to:
    `HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment`
3.  Edit the **Path** string and append:
    ```text
    ;C:\python310;C:\python310\Scripts
    ```
4.  Restart the CMD tool to apply changes.


---

## 🛠 Usage & Verification

Verify the installation in the **Wineskin CMD**:
```cmd
python --version
pip --version
```
