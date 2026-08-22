import subprocess
import sys
import os

GIT_PATHS = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
]

def find_git():
    for p in GIT_PATHS:
        if os.path.exists(p):
            return p
    # try PATH
    try:
        r = subprocess.run(["git", "--version"], capture_output=True, shell=True)
        if r.returncode == 0:
            return "git"
    except:
        pass
    return None

def run_git(*args, cwd=None):
    git = find_git()
    if not git:
        print("ERROR: git not found. Please install git from https://git-scm.com/")
        sys.exit(1)
    cmd = [git] + list(args)
    print(f"Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    print(r.stdout)
    if r.returncode != 0:
        print("STDERR:", r.stderr)
        return False
    return True

if __name__ == "__main__":
    cwd = r"D:\Antigravity_Work\latest_news_collection_and_distribution"
    print(f"Git found at: {find_git()}")
    ok = run_git("add", "static/latest_news.json", "news_database.db", cwd=cwd)
    if ok:
        ok = run_git("diff", "--staged", "--stat", cwd=cwd)
    if ok:
        ok = run_git("commit", "-m", "Manual export: update static JSON with 1045 articles", cwd=cwd)
    if ok:
        run_git("push", cwd=cwd)
