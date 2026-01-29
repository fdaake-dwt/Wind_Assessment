import streamlit as st
import pandas as pd
import json
from openai import OpenAI

# Seitentitel und Layout
st.set_page_config(page_title="Windenergie Assessment", page_icon="⚡")

st.title("⚡ Technisches Assessment: Windenergie")
st.write("Bitte beantworten Sie die folgenden technischen Fragen präzise.")

# API Key sicher holen
# Wenn lokal kein Secret da ist, zeige Fehler
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("Kein API Key gefunden. Bitte in Streamlit Secrets eintragen.")
    st.stop()

client = OpenAI(api_key=api_key)

# Session State initialisieren
if "answers" not in st.session_state:
    st.session_state["answers"] = {}

# Das Formular
with st.form("assessment_form"):
    name = st.text_input("Ihr Name:")
    
    st.subheader("1. Elektrotechnik / Umrichter")
    q1 = "Warum darf ein IGBT nicht unter Last geschaltet werden, wenn die Ansteuerung fehlt?"
    a1 = st.text_area(q1)

    st.subheader("2. Hydraulik / Pitch-System")
    q2 = "Woran erkennen Sie bei einer Sichtprüfung, dass ein hydraulischer Blasenspeicher defekt sein könnte?"
    a2 = st.text_area(q2)

    submitted = st.form_submit_button("Absenden & Prüfen")

if submitted and name:
    with st.spinner("Das System analysiert Ihre Antworten..."):
        
        fragen_katalog = [
            {"frage": q1, "antwort": a1, "muster": "Gefahr des 'Latching', Zerstörung durch unkontrolliertes Durchschalten."},
            {"frage": q2, "antwort": a2, "muster": "Pumpe läuft zu oft (kurze Zyklen), Druck fällt schlagartig ab, ruckartige Bewegung."}
        ]
        
        gesamtergebnis = []
        
        for item in fragen_katalog:
            prompt = f"""
            Du bist ein strenger technischer Auditor.
            Frage: "{item['frage']}"
            Muster: "{item['muster']}"
            Antwort: "{item['antwort']}"
            Bewerte nach Härteskala (0=Falsch, 100=Perfekt).
            Gib JSON: {{ "punkte": Zahl, "begruendung": "Kurzer Satz" }}
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                bewertung = json.loads(response.choices[0].message.content)
                
                gesamtergebnis.append({
                    "Frage": item['frage'],
                    "Punkte": bewertung['punkte'],
                    "Feedback": bewertung['begruendung']
                })
            except Exception as e:
                st.error(f"Fehler bei der Bewertung: {e}")

        # Ergebnis anzeigen
        st.success(f"Danke {name}. Hier ist Ihre Auswertung:")
        
        df = pd.DataFrame(gesamtergebnis)
        st.table(df)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SPEICHERN IN GOOGLE SHEETS ---
# Wir holen die Credentials aus den Secrets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = st.secrets["service_account"] # Das muss genau so in Secrets heißen
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client_gs = gspread.authorize(creds)

# Tabelle öffnen
sheet_name = "Wind_Ergebnisse" # MUSS EXAKT WIE DEINE DATEI HEISSEN
try:
    sheet = client_gs.open(sheet_name).sheet1
    
    # Wir fügen für jede Frage eine Zeile hinzu
    for ergebnis in gesamtergebnis:
        row = [
            name, 
            ergebnis['Frage'], 
            ergebnis['Punkte'], 
            ergebnis['Feedback']
        ]
        sheet.append_row(row)
        
    st.success("✅ Ergebnisse wurden erfolgreich in der Datenbank gespeichert!")
    
except Exception as e:
    st.error(f"Fehler beim Speichern: {e}")
