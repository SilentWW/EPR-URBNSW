#!/usr/bin/env python3
"""
Email sender script - runs as subprocess to avoid async issues
"""
import sys
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(config):
    """Send email with given configuration"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = config["subject"]
        msg["From"] = f"{config.get('from_name', 'ERP System')} <{config['from_email']}>"
        msg["To"] = config["to_email"]
        
        if config.get("body_text"):
            msg.attach(MIMEText(config["body_text"], "plain"))
        msg.attach(MIMEText(config["body_html"], "html"))
        
        context = ssl.create_default_context()
        
        if config.get("use_tls", True):
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=60) as server:
                server.starttls(context=context)
                server.login(config["smtp_user"], config["smtp_pass"])
                server.sendmail(config["from_email"], config["to_email"], msg.as_string())
        else:
            with smtplib.SMTP_SSL(config["smtp_host"], config["smtp_port"], context=context, timeout=60) as server:
                server.login(config["smtp_user"], config["smtp_pass"])
                server.sendmail(config["from_email"], config["to_email"], msg.as_string())
        
        print(json.dumps({"success": True}))
        return True
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
        send_email(config)
    else:
        print(json.dumps({"success": False, "error": "No config provided"}))
