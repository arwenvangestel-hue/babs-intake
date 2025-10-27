app.py


-------------------------------------------------------------


MVP: "BABS Intake-assistent" – screenshot (oproep) → automatisch ingevulde intake + bericht + chatdossier


Stack: Streamlit (snelle MVP)


-------------------------------------------------------------


import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from io import BytesIO
from PIL import Image


Optioneel OCR (Tesseract)


try:
import pytesseract  # type: ignore
OCR_AVAILABLE = True
except Exception:
OCR_AVAILABLE = False


st.set_page_config(page_title="BABS Intake-assistent", page_icon="💍", layout="centered")


------------------------- State -------------------------


if "threads" not in st.session_state:
st.session_state["threads"] = {}


------------------------- Helpers -------------------------


def slugify(*parts: str) -> str:
base = "-".join(p.strip().lower().replace(" ", "-") for p in parts if p)
keep = "abcdefghijklmnopqrstuvwxyz0123456789-_."
return "".join(ch for ch in base if ch in keep)[:80] or f"paar-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


MONTHS = {
"januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
"juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
}


def parse_dutch_date(text: str) -> str | None:
m = re.search(r"\b(\d{1,2})-/-/\b", text)
if m:
d, mo, y = m.groups()
y = y if len(y) == 4 else ("20" + y)
return f"{int(d):02d}-{int(mo):02d}-{int(y)}"
m = re.search(r"\b(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})\b", text, flags=re.I)
if m:
d, mon, y = m.groups()
monn = MONTHS.get(mon.lower())
if monn:
return f"{int(d):02d}-{monn:02d}-{y}"
return None


def parse_email(text: str) -> str | None:
m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+.[A-Z]{2,}", text, flags=re.I)
return m.group(0) if m else None


def parse_phone(text: str) -> str | None:
m = re.search(r"(+31\s?6|06)[\s-]?(\d[\s-]?){8}\b", text)
return m.group(0) if m else None


def parse_location(text: str) -> str | None:
m = re.search(r"(locatie|plaats|trouwlocatie)\s*[:-]?\s*(.+)", text, flags=re.I)
if m:
return m.group(2).strip().splitlines()[0][:80]
return None


def parse_names(text: str) -> tuple[str | None, str | None]:
m = re.search(r"(?:groeten|groet|hartelijke groet|liefs)[\s,:-]\n?\s([A-Za-zÀ-ÿ'-]+)\s*(?:&|en)\s*([A-Za-zÀ-ÿ'-]+)", text, flags=re.I)
if m:
return m.group(1), m.group(2)
m = re.search(r"wij\s+zijn\s+([A-Za-zÀ-ÿ'-]+)\s*(?:&|en)\s*([A-Za-zÀ-ÿ'-]+)", text, flags=re.I)
if m:
return m.group(1), m.group(2)
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
caps = [ln for ln in lines if re.match(r"^[A-ZÀ-Ý][A-Za-zÀ-ÿ'-]+(\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'-]+)?$", ln)]
if len(caps) >= 2:
return caps[0].split()[0], caps[1].split()[0]
return None, None


STYLE_SIG = (
"💍 Arwen van Gestel\n"
"Trouwambtenaar / BABS\n"
"📧 arwenvangestel@gmail.com\n"
)


VOORWAARDEN = (
"Voorwaarden (samenvatting):\n"
"• Vergoeding: € 690\n"
"• Reiskosten: € 0,15 per km vanaf Roosendaal (per factuur)\n"
"• Betaling: uiterlijk 10 dagen vóór de ceremonie\n"
"• Overmacht (beide partijen): bedrag retour, m.u.v. 10% gemaakte kosten\n"
"• Annulering door jullie binnen 3 maanden voor de huwelijksdatum: 50%\n"
)


------------------------- UI -------------------------


st.title("💍 BABS Intake‑assistent")
st.caption("Upload de oproep/screenshot van het bruidspaar → automatische invulling + berichten + chatdossier.")


with st.expander("1) Upload screenshot van de oproep (oproep van bruidspaar)"):
up = st.file_uploader("Upload een afbeelding (PNG/JPG)", type=["png", "jpg", "jpeg"])
ocr_txt = ""
if up is not None:
img = Image.open(up).convert("RGB")
st.image(img, caption="Screenshot van oproep", use_column_width=True)
if OCR_AVAILABLE and st.checkbox("Probeer tekst extraheren (OCR)"):
try:
ocr_txt = pytesseract.image_to_string(img).strip()
st.text_area("Gevonden tekst (bewerken mag)", value=ocr_txt, height=200, key="ocr_box")
if st.checkbox("Auto-invullen vanaf screenshot"):
parsed_datum = parse_dutch_date(ocr_txt)
parsed_mail = parse_email(ocr_txt)
parsed_tel = parse_phone(ocr_txt)
parsed_loc = parse_location(ocr_txt)
pn1, pn2 = parse_names(ocr_txt)
st.session_state["auto_fill"] = {
"n1": pn1, "n2": pn2, "datum": parsed_datum,
"locatie": parsed_loc, "mail": parsed_mail, "tel": parsed_tel
}
st.success("Velden zijn vooringevuld. Controleer en pas aan waar nodig.")
except Exception as e:
st.warning(f"OCR niet beschikbaar op deze host: {e}")


st.markdown("### 2) Intakegegevens")
cols = st.columns(2)
state_fill = st.session_state.get("auto_fill", {})
with cols[0]:
n1 = st.text_input("Naam partner 1", value=state_fill.get("n1") or "", placeholder="Voornaam / volledige naam")
datum = st.text_input("Trouwdatum", value=state_fill.get("datum") or "", placeholder="bijv. 06-06-2025")
mail = st.text_input("E‑mail", value=state_fill.get("mail") or "", placeholder="Contact e‑mail")
with cols[1]:
n2 = st.text_input("Naam partner 2", value=state_fill.get("n2") or "", placeholder="Voornaam / volledige naam")
locatie = st.text_input("Trouwlocatie / Plaats", value=state_fill.get("locatie") or "", placeholder="bijv. Schijndel")
tel = st.text_input("Telefoon", value=state_fill.get("tel") or "", placeholder="06…")


toon = st.selectbox("Ceremonietoon", ["warm", "klassiek", "vrolijk"], index=0)
extra = st.text_area("Extra info / hun verhaal (optioneel)", value="", height=120)


------------------------- Teksten -------------------------


def bericht_eerste_contact(n1, n2, datum, locatie, toon, extra, telmail):
aanhef = f"Hoi {n1} en {n2}," if n1 and n2 else "Hoi!"
dl = " ".join(filter(None, [f"voor {datum}" if datum else None, f"in {locatie}" if locatie else None]))
zin_datum = f"Wat leuk dat jullie {dl} gaan trouwen! " if dl else "Wat leuk dat jullie gaan trouwen! "
tone = {
"warm": "Ik werk graag warm, oprecht en persoonlijk – met een vleugje humor.",
"klassiek": "Ik verzorg een persoonlijke, stijlvolle ceremonie met aandacht voor inhoud.",
"vrolijk": "We maken er een lichte, vrolijke en persoonlijke ceremonie van.",
}.get(toon or "warm")
cta = "Zullen we kort kennis maken? Stuur gerust een paar momenten die passen; een eerste kennismaking plan ik graag met jullie in."
body = f"""{aanhef}\n\n{zin_datum}{tone}\n{extra}\n\n{cta}\n\n{STYLE_SIG}{telmail}"""
return body.strip()


def bericht_bevestiging(n1, n2, datum, locatie, extra):
aanhef = f"Hoi {n1} en {n2}," if n1 and n2 else "Hoi!"
zin = f"Leuk dat we met elkaar aan de slag gaan! ({datum}, {locatie})"
uitleg = "Via de app stuur ik wat dataopties door; in de bijlage vinden jullie praktische info en de voorwaarden."
return f"""{aanhef}\n\n{zin}\n{extra}\n\n{uitleg}\n\n{STYLE_SIG}\n{VOORWAARDEN}"""


def bericht_whatsapp_kort(n1, n2, datum):
aanhef = f"Hoi {n1} en {n2}" if n1 and n2 else "Hoi!"
d = f" {datum}" if datum else ""
return f"{aanhef}! Superleuk dat jullie gaan trouwen{d}.\nZullen we kort kennis maken? Stuur 2–3 tijdstippen; dan prikken we iets.\nGroet, Arwen"


------------------------- Generator -------------------------


slug = slugify("babs", n1, n2, datum)
thread_title = f"BABS – {n1} & {n2}".strip(" – ")


st.markdown("---")
st.subheader("3) Genereer berichten")


colb = st.columns(3)
if colb[0].button("Eerste kennismail ✉️"):
st.session_state["last_text"] = bericht_eerste_contact(n1, n2, datum, locatie, toon, extra, tel)
if colb[1].button("Bevestiging + voorwaarden 📎"):
st.session_state["last_text"] = bericht_bevestiging(n1, n2, datum, locatie, extra)
if colb[2].button("WhatsApp kort 💬"):
st.session_state["last_text"] = bericht_whatsapp_kort(n1, n2, datum)


if "last_text" in st.session_state:
st.markdown("#### Voorbeeldtekst")
st.text_area("Kopieer/werk bij", value=st.session_state["last_text"], height=240, key="preview_text")
st.download_button("⬇️ Download als .txt", data=st.session_state["preview_text"].encode("utf-8"), file_name=f"{slug}.txt")


------------------------- Chatdossier -------------------------


st.markdown("---")
st.subheader("4) Chatdossier onder BABS")
if slug not in st.session_state["threads"]:
st.session_state["threads"][slug] = {
"title": thread_title or slug,
"meta": {"partner1": n1, "partner2": n2, "datum": datum, "locatie": locatie, "email": mail, "tel": tel, "slug": slug, "created": datetime.now().isoformat(timespec="seconds")},
"chat": [],
}


st.info(f"Chat aangemaakt onder: {st.session_state['threads'][slug]['title']}")


with st.form("chat_form"):
who = st.selectbox("Van wie is dit bericht?", ["Arwen", f"{n1 or 'Partner 1'}", f"{n2 or 'Partner 2'}", "Overig"])
msg = st.text_area("Bericht / notitie", height=120)
submitted = st.form_submit_button("Plaatsen in chat")


if submitted and msg.strip():
st.session_state["threads"][slug]["chat"].append({"ts": datetime.now().isoformat(timespec="seconds"), "from": who, "text": msg.strip()})


chat = st.session_state["threads"][slug]["chat"]
if chat:
for item in reversed(chat):
with st.chat_message("user" if item["from"] != "Arwen" else "assistant"):
st.markdown(f"{item['from']} · {item['ts']}\n\n{item['text']}")
else:
st.caption("Nog geen berichten. Gebruik het formulier hierboven om te starten.")


colx = st.columns(3)
if colx[0].button("➕ Voeg huidige tekst toe aan chat") and "preview_text" in st.session_state:
st.session_state["threads"][slug]["chat"].append({"ts": datetime.now().isoformat(timespec="seconds"), "from": "Arwen", "text": st.session_state["preview_text"]})
if colx[1].button("⬇️ Exporteer dossier (JSON)"):
b = BytesIO()
b.write(json.dumps(st.session_state["threads"][slug], ensure_ascii=False, indent=2).encode("utf-8"))
b.seek(0)
st.download_button(label="Download JSON", data=b, file_name=f"{slug}.json", mime="application/json")
if colx[2].button("⬇️ Exporteer chat (CSV)"):
df = pd.DataFrame(chat)
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", data=csv, file_name=f"{slug}-chat.csv", mime="text/csv")


st.markdown("---")
st.caption("© 2025 – BABS Intake‑assistent (oproepversie). Warm, oprecht, persoonlijk; subtiel assertief.")


requirements.txt


streamlit==1.38.0


pandas==2.2.2


pillow==10.4.0


pytesseract==0.3.10


