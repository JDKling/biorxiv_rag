# bioRxiv TDM Pipeline — EC2 Setup & Dependencies

This README explains how to set up an EC2 instance in `us-east-1` and install everything needed to download, unpack, filter, and extract text from the bioRxiv requester-pays TDM S3 bucket (`s3://biorxiv-src-monthly`).

Target OS: Amazon Linux 2023 (recommended). Ubuntu 22.04 commands are included where they differ.

---

## 1) Prerequisites

- An AWS account with billing enabled.
- One of the following access methods:
  - EC2 Instance Connect (browser-based SSH).
  - Session Manager (no SSH keys; requires an instance role).
  - Classic SSH with a key pair.

- Permissions:
  - For the instance role: `AmazonS3ReadOnlyAccess` (to read S3) and `AmazonSSMManagedInstanceCore` if using Session Manager.
  - If you prefer using access keys on the instance, an IAM user with S3 read permissions is required.

---

## 2) Create or attach an IAM role (recommended)

1. Console: IAM → Roles → Create role.
2. Trusted entity: AWS service → EC2.
3. Attach policies:
   - `AmazonS3ReadOnlyAccess`
   - `AmazonSSMManagedInstanceCore` (only if you want Session Manager access).
4. Name it `ec2-s3-readonly` (or similar) and create.
5. Attach to your EC2 instance: EC2 → Instances → select instance → Actions → Security → Modify IAM role → choose the role.

This avoids storing credentials on disk and is best for automation.

---

## 3) Launch the EC2 instance

- Region: `us-east-1` (same as the bioRxiv bucket).
- AMI: Amazon Linux 2023 (or Ubuntu 22.04).
- Instance type: start with `t3.large` or `c7a.large`.
- Storage (EBS): 200–1000 GB depending on how many months you process per run.
- Security group: allow outbound HTTPS (default). If using SSH, allow SSH from your IP.
- IAM role: attach the role from step 2 if using roles.

### Connect options

**A. EC2 Instance Connect**
- EC2 → Instances → Connect → EC2 Instance Connect.

**B. Session Manager**
- Ensure role has `AmazonSSMManagedInstanceCore`.
- EC2 → Instances → Connect → Session Manager.

**C. Classic SSH**
- Create key pair in EC2 → Key pairs.
- Launch the instance with that key pair.
- Connect:
  ```bash
  chmod 400 ~/Downloads/my-key.pem
  ssh -i ~/Downloads/my-key.pem ec2-user@<ec2-public-dns>   # Amazon Linux
  # or
  ssh -i ~/Downloads/my-key.pem ubuntu@<ec2-public-dns>     # Ubuntu
  ```

---

## 4) Install dependencies

### Amazon Linux 2023
```bash
sudo dnf -y update
sudo dnf -y install unzip python3-pip
aws --version || sudo dnf -y install awscli
pip3 install --upgrade pip
pip3 install lxml beautifulsoup4
```

### Ubuntu 22.04
```bash
sudo apt-get update
sudo apt-get -y install unzip python3-pip awscli
pip3 install --upgrade pip
pip3 install lxml beautifulsoup4
```

---

## 5) Run the pipeline

```bash
bash aws_ec2_biorxiv_sync.sh
```

Behavior:
- Processes months one at a time to limit disk usage.
- Writes filtered XML/PDF under `~/biorxiv/filtered/<Month_YYYY>/`.
- Creates a `.DONE` marker per month to support safe resume.
- Deletes raw `.meca` and unpacked content for each month after filtering.

---

## 6) Optional: Convert XML to text for embedding

```bash
cd ~/biorxiv/filtered
find . -type f -name '*.xml' | while read -r x; do
  python3 - <<'EOF' "$x"
import sys
from bs4 import BeautifulSoup
p = sys.argv[1]
with open(p, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'lxml-xml')
txt = soup.get_text(separator="\n", strip=True)
out = p[:-4] + ".txt"
with open(out, 'w', encoding='utf-8') as o:
    o.write(txt)
print(out)
EOF
done
```

---

## 7) Troubleshooting

- Error: `Unable to locate credentials`  
  - Attach an IAM role with `AmazonS3ReadOnlyAccess` to the instance, or run `aws configure` with your IAM user keys.

- Error: AccessDenied or UnauthorizedOperation  
  - Ensure the instance role or user has S3 read permissions and, if using Session Manager, the role includes `AmazonSSMManagedInstanceCore`.

- Disk fills up quickly  
  - Increase EBS volume size or process fewer months per run. The pipeline cleans raw and unpacked data after each month to conserve space.

- Manifest differences  
  - The filter script is tolerant but can be extended if some months use different tag names. Adjust the XPath selectors as needed.
