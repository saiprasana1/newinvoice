# Deployment Requirements & Costs

Complete list of services, licenses, and infrastructure needed to deploy the Invoice Generation System to production.

---

## 🔴 Required Services (Must Have)

### 1. **OpenAI API** (LLM & Audio Transcription)
**Purpose**: AI-powered data extraction and natural language commands

**What it's used for**:
- Excel/CSV file data extraction
- Natural language command processing ("add all details from dataset")
- Audio transcription (voice commands)

**Models used**:
- `gpt-4.1-mini` or `gpt-4.1-nano` - Text processing
- `whisper-1` - Audio transcription

**Pricing** (as of 2024):
- GPT-4 Mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Whisper: ~$0.006 per minute of audio

**Estimated monthly cost**: $50-200 (depending on usage)

**How to get**:
- Sign up at https://platform.openai.com
- Get API key from API Keys section
- Set environment variable: `OPENAI_API_KEY=sk-...`

---

### 2. **MongoDB** (Database)
**Purpose**: Store master data (banks, clients, companies, terms & conditions)

**What's stored**:
- Bank accounts (name, account number, IFSC, branch)
- Client companies (name, address, GSTIN)
- Parent companies (company info)
- Terms & conditions templates

**Options**:

#### Option A: MongoDB Atlas (Cloud - Recommended)
- **Free Tier**: 512MB storage, shared cluster
- **Paid Tier**: Starts at $9/month (2GB storage, dedicated)
- **Setup**: https://www.mongodb.com/cloud/atlas
- **Connection**: Set `MONGODB_URI=mongodb+srv://...`

#### Option B: Self-Hosted MongoDB
- **Cost**: Server costs only
- **Setup**: Install on your server
- **Connection**: Set `MONGODB_URI=mongodb://localhost:27017`

**Estimated monthly cost**: $0-50 (Free tier sufficient for small scale)

**Required collections**:
```
invoice_app/
├── parent_companies
├── client_companies
├── bank_accounts
└── terms_and_conditions
```

---

### 3. **Python 3.11+** (Runtime)
**Purpose**: Run the application

**Cost**: Free (open source)

**Installation**:
- Ubuntu: `apt install python3.11`
- Windows: Download from python.org
- Docker: `python:3.11-slim`

---

### 4. **Playwright Browsers** (PDF/PNG Export)
**Purpose**: Render HTML to PDF and PNG

**Cost**: Free (open source)

**Installation**:
```bash
pip install playwright
playwright install chromium
```

**Storage**: ~300MB for Chromium browser

---

## 🟡 Infrastructure (Deployment Platform)

Choose ONE of the following:

### Option A: **AWS (Amazon Web Services)**

**Services needed**:
1. **EC2** (Virtual Server)
   - t3.small or larger (2 vCPU, 2GB RAM minimum)
   - Cost: ~$15-30/month

2. **S3** (Optional - File Storage)
   - Store generated PDFs/PNGs
   - Cost: ~$0.023 per GB/month

3. **Route 53** (Optional - DNS)
   - Custom domain
   - Cost: ~$0.50/month per hosted zone

**Total AWS cost**: $20-50/month

---

### Option B: **DigitalOcean**

**Services needed**:
1. **Droplet** (Virtual Server)
   - Basic: $12/month (2GB RAM, 1 vCPU)
   - Recommended: $24/month (4GB RAM, 2 vCPU)

2. **Spaces** (Optional - File Storage)
   - S3-compatible storage
   - Cost: $5/month (250GB)

**Total DigitalOcean cost**: $12-30/month

---

### Option C: **Google Cloud Platform (GCP)**

**Services needed**:
1. **Compute Engine** (Virtual Server)
   - e2-small: ~$15/month
   - e2-medium: ~$30/month

2. **Cloud Storage** (Optional)
   - Cost: ~$0.020 per GB/month

**Total GCP cost**: $20-40/month

---

### Option D: **Heroku** (Easiest)

**Services needed**:
1. **Dyno** (Container)
   - Basic: $7/month
   - Standard: $25/month

2. **Add-ons**:
   - MongoDB Atlas (free tier via Heroku)

**Total Heroku cost**: $7-25/month

---

### Option E: **Self-Hosted / On-Premise**

**Requirements**:
- Server with 4GB RAM, 2+ CPU cores
- Ubuntu 22.04 or similar
- Static IP or domain name
- SSL certificate (Let's Encrypt - free)

**Cost**: Hardware/electricity only

---

## 🟢 Optional Services (Nice to Have)

### 1. **Domain Name**
**Purpose**: Custom URL (invoice.yourcompany.com)

**Providers**:
- Namecheap, GoDaddy, Google Domains
- Cost: $10-15/year

---

### 2. **SSL Certificate**
**Purpose**: HTTPS encryption

**Options**:
- **Let's Encrypt**: Free
- **Paid SSL**: $50-200/year (not necessary)

---

### 3. **CDN (CloudFlare)**
**Purpose**: Faster loading, DDoS protection

**Cost**: Free tier available

---

### 4. **Email Service** (Future Feature)
**Purpose**: Send invoices via email

**Options**:
- SendGrid: 100 emails/day free
- AWS SES: $0.10 per 1000 emails
- Mailgun: 5000 emails/month free

**Cost**: $0-20/month

---

### 5. **Monitoring & Logging**
**Purpose**: Track errors, performance

**Options**:
- **Sentry** (Error tracking): Free tier available
- **Datadog** (Monitoring): Starts at $15/month
- **CloudWatch** (AWS): Pay as you go

**Cost**: $0-30/month

---

### 6. **Backup Service**
**Purpose**: Automated backups

**Options**:
- **MongoDB Atlas**: Automatic backups included
- **AWS Backup**: ~$0.05 per GB/month
- **Self-managed**: Cron jobs (free)

**Cost**: $0-10/month

---

## 📦 Python Packages (Already Included)

All listed in `requirements.txt`:

**Free & Open Source**:
- FastAPI (Web framework)
- Gradio (UI framework)
- Pandas (Data processing)
- OpenPyXL (Excel reading)
- Playwright (Browser automation)
- ReportLab, WeasyPrint (PDF generation)
- Pillow (Image processing)
- PyMongo (MongoDB driver)

**Installation**:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 💰 Total Cost Breakdown

### Minimum (Small Scale)
| Service | Cost |
|---------|------|
| OpenAI API | $50/month |
| MongoDB Atlas | $0 (free tier) |
| Heroku Dyno | $7/month |
| Domain (optional) | $1/month |
| **TOTAL** | **$58/month** |

### Recommended (Production)
| Service | Cost |
|---------|------|
| OpenAI API | $100/month |
| MongoDB Atlas | $9/month |
| AWS EC2 (t3.small) | $20/month |
| Domain + SSL | $2/month |
| Monitoring | $15/month |
| **TOTAL** | **$146/month** |

### Enterprise (High Scale)
| Service | Cost |
|---------|------|
| OpenAI API | $500/month |
| MongoDB Atlas | $50/month |
| AWS EC2 (t3.medium) | $40/month |
| AWS S3 | $10/month |
| Domain + SSL | $2/month |
| Monitoring + Logging | $50/month |
| Backups | $10/month |
| **TOTAL** | **$662/month** |

---

## 🔧 Environment Variables Needed

```bash
# Required
OPENAI_API_KEY=sk-...                    # From OpenAI platform
MONGODB_URI=mongodb+srv://...            # From MongoDB Atlas

# Optional (with defaults)
HOST=0.0.0.0                             # Server host
PORT=7860                                # Gradio UI port
API_SERVER_PORT=8000                     # FastAPI port
GRADIO_SHARE=false                       # Public Gradio link
DEBUG_INVOICE=false                      # Debug mode
OPENAI_TRANSCRIPTION_MODEL=whisper-1     # Audio model
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Get OpenAI API key
- [ ] Set up MongoDB Atlas account
- [ ] Create MongoDB database and collections
- [ ] Choose deployment platform (AWS/DigitalOcean/etc.)
- [ ] Register domain name (optional)

### Deployment
- [ ] Set up server/container
- [ ] Install Python 3.11
- [ ] Clone repository
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Install Playwright browsers: `playwright install chromium`
- [ ] Set environment variables
- [ ] Test connection to MongoDB
- [ ] Test OpenAI API
- [ ] Run application: `python api_server.py`

### Post-Deployment
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure firewall (allow ports 80, 443, 8000)
- [ ] Set up monitoring (Sentry/Datadog)
- [ ] Configure automated backups
- [ ] Test all endpoints
- [ ] Load test with expected traffic

### Security
- [ ] Add JWT authentication
- [ ] Restrict CORS to frontend domain
- [ ] Add rate limiting
- [ ] Enable HTTPS only
- [ ] Secure environment variables
- [ ] Set up firewall rules
- [ ] Regular security updates

---

## 🚀 Quick Start Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
export OPENAI_API_KEY=sk-...
export MONGODB_URI=mongodb+srv://...

# Run Gradio UI
python app.py

# OR Run FastAPI
python api_server.py
```

### Production (Ubuntu Server)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv -y

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
echo "export OPENAI_API_KEY=sk-..." >> ~/.bashrc
echo "export MONGODB_URI=mongodb+srv://..." >> ~/.bashrc
source ~/.bashrc

# Run with systemd (production)
sudo nano /etc/systemd/system/invoice-api.service
# Add service configuration
sudo systemctl enable invoice-api
sudo systemctl start invoice-api
```

---

## 📞 Support & Resources

**OpenAI**:
- Platform: https://platform.openai.com
- Docs: https://platform.openai.com/docs
- Pricing: https://openai.com/pricing

**MongoDB**:
- Atlas: https://www.mongodb.com/cloud/atlas
- Docs: https://docs.mongodb.com
- Pricing: https://www.mongodb.com/pricing

**Deployment Platforms**:
- AWS: https://aws.amazon.com
- DigitalOcean: https://www.digitalocean.com
- Heroku: https://www.heroku.com
- GCP: https://cloud.google.com

---

## 🔒 License Requirements

**Open Source (Free)**:
- Python (PSF License)
- FastAPI (MIT License)
- Gradio (Apache 2.0)
- Playwright (Apache 2.0)
- All other Python packages (various open source licenses)

**Commercial Services**:
- OpenAI API (Pay-as-you-go, no license fee)
- MongoDB Atlas (Pay-as-you-go, no license fee)
- Cloud providers (Pay-as-you-go)

**Your Application**:
- You own the code
- No licensing fees to third parties
- Can deploy commercially

---

## Summary

**Absolute Minimum to Deploy**:
1. ✅ OpenAI API Key ($50+/month)
2. ✅ MongoDB Atlas Free Tier ($0)
3. ✅ Server/Hosting ($7-20/month)

**Total Minimum**: ~$60/month

**No proprietary licenses needed** - all software is open source or pay-as-you-go cloud services.
