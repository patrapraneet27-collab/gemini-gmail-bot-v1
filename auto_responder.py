from datetime import datetime
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import os
import smtplib
import uuid
from dotenv import load_dotenv
from google import genai


def check_and_create_env():
  if not os.path.exists(".env"):
    print("=" * 50)
    print("  EMAIL ASSISTANT - FIRST TIME SETUP")
    print("=" * 50)
    print("                        ~~Made By Praneet")
    email_val = input("Enter your Gmail Address: ").strip()
    pass_val = input("Enter your Gmail App Password (16 chars): ").strip()
    key_val = input("Enter your Gemini API Key: ").strip()

    if not email_val or not pass_val or not key_val:
      print(
          "[!] Error: All fields are required! Please restart and try again."
      )
      exit(1)

    with open(".env", "w") as f:
      f.write(f"EMAIL_USER={email_val}\n")
      f.write(f"EMAIL_PASS={pass_val}\n")
      f.write(f"GEMINI_API_KEY={key_val}\n")

    print("\n[+] Configuration saved successfully to .env file!\n" + "=" * 50)


check_and_create_env()

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
RECORD_DIR = "record secret"

if not os.path.exists(RECORD_DIR):
  os.makedirs(RECORD_DIR)


def decode_str(s):
  if not s:
    return ""
  decoded_list = decode_header(s)
  result = ""
  for text, encoding in decoded_list:
    if isinstance(text, bytes):
      result += text.decode(encoding or "utf-8", errors="ignore")
    else:
      result += text
  return result


def check_and_reply_emails():
  if not EMAIL_USER or not EMAIL_PASS or not GEMINI_API_KEY:
    print("[!] Error: Credentials missing in .env file.")
    return

  client = genai.Client(api_key=GEMINI_API_KEY)

  try:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    today_str = datetime.now().strftime("%d-%b-%Y")
    status, messages = mail.search(None, f"(UNSEEN SINCE {today_str})")
    if status != "OK":
      return

    email_ids = messages[0].split()
    if not email_ids:
      print("Inbox is up to date. No new unread messages from today.")
      mail.logout()
      return

    for e_id in email_ids:
      res, msg_data = mail.fetch(e_id, "(RFC822)")
      for response_part in msg_data:
        if isinstance(response_part, tuple):
          msg = email.message_from_bytes(response_part[1])
          subject = decode_str(msg["Subject"])
          sender = decode_str(msg["From"])
          msg_id = msg.get("Message-ID")

          if "noreply" in sender.lower() or "no-reply" in sender.lower():
            print(f"[-] Skipping automated notification from: {sender}")
            mail.store(e_id, "+FLAGS", "\\Seen")
            continue

          body = ""
          if msg.is_multipart():
            for part in msg.walk():
              if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(
                    errors="ignore"
                )
                break
          else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

          print(f"[-] Processing email from: {sender} | Subject: {subject}")

          prompt = (
              f"You are a helpful personal email assistant. Read the incoming"
              f" email below and write a professional, concise reply.\n\nSubject:"
              f" {subject}\nBody:\n{body}\n\nReply:"
          )

          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt
          )
          reply_body = response.text
          print(f"[-] Generated Reply:\n{reply_body}\n")

          reply_msg = MIMEMultipart()
          reply_msg["From"] = EMAIL_USER
          reply_msg["To"] = sender
          reply_msg["Subject"] = (
              f"Re: {subject}" if not subject.startswith("Re:") else subject
          )

          if msg_id:
            reply_msg["In-Reply-To"] = msg_id
            reply_msg["References"] = msg_id

          reply_msg.attach(MIMEText(reply_body, "plain"))

          with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, sender, reply_msg.as_string())

          record_id = str(uuid.uuid4())
          current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          record_filename = os.path.join(RECORD_DIR, f"record_{record_id}.txt")
          with open(record_filename, "w", encoding="utf-8") as rec_file:
            rec_file.write(f"Unique ID: {record_id}\n")
            rec_file.write(f"Customer Email: {sender}\n")
            rec_file.write(f"Timestamp: {current_time}\n")
            rec_file.write(f"Subject: {subject}\n")

          print(
              f"[+] Successfully replied to {sender} and saved record"
              f" [{record_id}]"
          )

      mail.store(e_id, "+FLAGS", "\\Seen")

    mail.logout()
  except Exception as e:
    print(f"[!] An error occurred: {e}")


if __name__ == "__main__":
  check_and_reply_emails()