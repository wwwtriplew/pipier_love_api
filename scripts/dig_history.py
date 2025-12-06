import subprocess
import sys
import os

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def dig():
    print("Digging for the 'old fast version'...")
    
    # Get all commits
    commits = run_command("git log --format='%h'").split('\n')
    print(f"Found {len(commits)} commits.")
    
    current_head = run_command("git rev-parse HEAD")
    
    found_candidate = False
    
    try:
        for i, commit in enumerate(commits):
            # Checkout magic_bitboards.py from that commit
            # We don't need to checkout the whole repo, just read the file
            try:
                content = run_command(f"git show {commit}:src/magic_bitboards.py")
            except:
                continue
                
            if content:
                # Check for slow bit counting
                if "bin(bb).count" not in content and "def count_bits" in content:
                    print(f"\n[CANDIDATE] Commit {commit} (Index {i})")
                    print("  - Does NOT use bin(bb).count('1')")
                    
                    # Check what it uses
                    if "fast_ops" in content:
                        print("  - Imports from fast_ops")
                    elif "bit_count" in content:
                        print("  - Uses .bit_count()")
                    else:
                        print("  - Uses custom implementation")
                        
                    # Get commit message
                    msg = run_command(f"git log -1 --format='%s' {commit}")
                    print(f"  - Message: {msg}")
                    found_candidate = True
                    
                    # We found one, let's stop or ask user?
                    # Let's find the *latest* one that matches this criteria
                    # Since we iterate from HEAD backwards, the first one we find is the latest "good" one (if we assume it broke recently)
                    # But user said "very very old".
                    
    finally:
        # Ensure we are back to HEAD (though we didn't change HEAD, just read files)
        pass

    if not found_candidate:
        print("\nNo obvious candidates found (all versions seem to use bin().count or lack count_bits).")
    else:
        print("\nDigging complete. Try checking out one of the candidates above.")

if __name__ == "__main__":
    dig()
