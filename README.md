# email auto-responder 
~ made by praneet

just a quick little python script that checks your inbox for today's unread emails, uses gemini (`gemini-2.5-flash`) to draft a smart reply, sends it out, and drops a text log into a local `record secret` folder so you have receipts. it automatically skips `noreply` addresses too, so it only talks to actual people.

### before you start
make sure you have:
- python installed on your machine
- a google **app password** (you need 2-step verification turned on for your google account)
- a free **gemini api key** from google ai studio

### how to run it

if you use git, just open your terminal and run:

```bash
git clone https://github.com/patrapraneet27-collab/gmail-bot.git
cd gemini-gmail-bot-v1
run_responder.bat
