import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.6-flash')

def generate_script():
    prompt = """
Act as a highly engaging political commentator for a Faceless YouTube Channel called "PakPoint News Hub". 
Your job is to write a thrilling, analytical, and engaging 3-5 minute YouTube video commentary script based on a recent video titled: "Khan Back in Jail - Khan Refused The Deal ? Pirzada & Gill".

The user specifically requested: "highlight the point Dr. Shahbaz Gill raised". Make sure this is the central focus of the commentary.

Context for the AI:
The user provided the exact summary of what Dr. Shahbaz Gill pointed out in the video:
"In his opinion, Gill pointed out that the establishment wanted to put a bill in the assembly for creating more provinces. The establishment convinced the current PTI leadership that they are on the same page regarding new provinces. But they needed Imran Khan to concrete this decision by accepting it. So, they managed to stage a game with the current PTI leadership: they would call Imran Khan to a hospital bed where he would be in an AC room, making it difficult for him to go back to the harsh jail environment, hoping he would agree to this and ask his leadership to vote in favor of creating more provinces. They took Imran Khan from Adiala jail and kept him in PIMS (rather than going to SHIFA International). However, Imran Khan refused to be part of any deal and this whole drama collapsed."

Script Requirements:
1. Start with a very strong, hook-driven intro that grabs attention within the first 5 seconds.
2. Weave these specific details naturally into a thrilling narrative. Detail the psychological game of moving him to an AC room in PIMS to break his resolve, the plot for new provinces, and his ultimate refusal.
3. Use a conversational, authoritative, and slightly dramatic tone.
4. Add bracketed visual cues for the video editor (e.g., [Show dramatic footage of PIMS hospital], [Show screenshot of Dr. Shahbaz Gill]).
5. End with a strong Call to Action (CTA) asking viewers to subscribe, like, and comment their opinion below.

Output purely the script in Markdown format. Do not include any other conversational filler text from the AI.
"""
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    print("Generating script based on video title and context...")
    script = generate_script()
    with open("youtube_scripts/shahbaz_gill_commentary.md", "w", encoding="utf-8") as f:
        f.write(script)
    print("Success! Script saved to youtube_scripts/shahbaz_gill_commentary.md")
