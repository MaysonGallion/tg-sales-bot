# tg-sales-bot/messages/pl.py
# Centralne teksty PL (wersjonowane tam, gdzie potrzebne)

# --- WERSJE PRAWNE ---
LEGAL_CONSENT_VERSION = "2025-08-20-1"

# --- OŚWIADCZENIE / REGULAMIN (ADMIN) ---
LEGAL_CONSENT_SHORT = (
    "🛡️ <b>Oświadczenie zgodności (administrator)</b>\n\n"
    "Korzystając z panelu administratora, oświadczasz, że:\n"
    "• Dodajesz wyłącznie <b>legalne</b> towary i treści zgodne z prawem RP i UE.\n"
    "• Nie wykorzystujesz bota do działań sprzecznych z prawem.\n"
    "• Ponosisz pełną odpowiedzialność za ofertę, sprzedaż i realizację.\n\n"
    "<i>Autorzy oprogramowania dostarczają narzędzie techniczne i nie są stroną sprzedaży, "
    "nie weryfikują ofert ani płatności i nie ponoszą odpowiedzialności za treści dodane przez administratorów.</i>"
)

LEGAL_CONSENT_FULL = (
    "📜 <b>Oświadczenie i warunki korzystania z panelu administratora</b>\n"
    f"Wersja: {LEGAL_CONSENT_VERSION}\n\n"
    "1) <b>Charakter usługi</b>: Bot jest wyłącznie narzędziem technicznym. Nie jest platformą marketplace, "
    "nie pośredniczy w płatnościach i nie sprzedaje produktów.\n\n"
    "2) <b>Odpowiedzialność administratora</b>: Wyłączną odpowiedzialność za ofertę, treści, ceny, zdjęcia, dostępność, "
    "realizację zamówień oraz zgodność z prawem ponosi administrator.\n\n"
    "3) <b>Zakazane treści/towary</b>: w szczególności zabronione są: narkotyki i substancje kontrolowane, "
    "broń i materiały wybuchowe, pornografia nielegalna, dane osobowe bez podstawy prawnej, dobra kradzione i podróbki, "
    "leki na receptę bez uprawnień, usługi nielegalne, treści nawołujące do nienawiści i przemocy.\n\n"
    "4) <b>Zgodność z prawem</b>: Administrator zobowiązuje się działać zgodnie z prawem RP i UE, w tym z przepisami "
    "dot. sprzedaży konsumenckiej, ochrony danych i własności intelektualnej.\n\n"
    "5) <b>Logi</b>: System może gromadzić podstawowe logi techniczne. W razie prawnego zobowiązania, dane mogą zostać "
    "udostępnione organom zgodnie z obowiązującym prawem.\n\n"
    "6) <b>Wyłączenie odpowiedzialności twórców</b>: Twórcy oprogramowania nie odpowiadają za szkody powstałe w wyniku użycia bota, "
    "w tym za treści wprowadzone przez administratorów.\n\n"
    "Korzystając z panelu, <b>akceptujesz powyższe warunki</b>."
)

LEGAL_CONSENT_PROMPT = (
    "Zanim przejdziesz do panelu administratora, potwierdź oświadczenie zgodności.\n\n"
    f"{LEGAL_CONSENT_SHORT}\n\n"
    "Czy akceptujesz?"
)

# --- UŻYTKOWNIK: MENU/NAWIGACJA ---
USER_MENU_CHOOSE_PAYMENT = "💳 <b>Wybierz metodę płatności:</b>"
USER_MENU_MAIN = "🏠 Wróciłeś do menu głównego. Wybierz opcję:"
USER_BACK = "🔙 Wróć"
USER_HOME = "🏠 Menu główne"

# --- PŁATNOŚCI: BLIK ---
PAYMENT_BLIK_STEP1_TITLE = "📲 <b>Informacje do płatności BLIK</b>"
PAYMENT_BLIK_NUMBER_PREFIX = "Numer BLIK: "
PAYMENT_BLIK_INSTR = (
    "➡️ Wykonaj przelew BLIK.\n"
    "⚠️ <b>WAŻNE:</b> prześlij <b>potwierdzenie jako zdjęcie</b> i wpisz <b>adres dostawy</b> w podpisie zdjęcia.\n"
    "Jeśli Twój bank blokuje zrzuty ekranu: \n"
    "• zrób zdjęcie potwierdzenia innym telefonem <u>lub</u>\n"
    "• wyeksportuj potwierdzenie do <b>PDF</b> i prześlij jako dokument.\n\n"
    "❗ <b>Nie wysyłaj teraz potwierdzenia.</b> Najpierw kliknij „Opłacone, przejdź dalej”."
)
PAYMENT_BLIK_BUTTON_PAID = "✅ Opłacone, przejdź dalej"

PAYMENT_BLIK_STEP2_PROMPT = (
    "📤 Wyślij teraz <b>potwierdzenie płatności</b>:\n"
    "• jako <b>zdjęcie</b> <i>lub</i> dokument <b>PDF</b>/obraz,\n"
    "• z <b>adresem dostawy</b> w podpisie.\n\n"
    "Bez potwierdzenia i adresu zamówienie <b>nie zostanie</b> przyjęte."
)

PAYMENT_BLIK_ERR_NEED_PHOTO_OR_DOC = (
    "❌ To nie wygląda na potwierdzenie.\n"
    "Wyślij proszę <b>zdjęcie</b> lub <b>PDF/obraz</b> z potwierdzeniem."
)
PAYMENT_BLIK_ERR_NEED_CAPTION = (
    "❌ Brakuje adresu dostawy w podpisie.\n"
    "Dodaj adres w podpisie do zdjęcia/dokumentu i wyślij ponownie."
)
PAYMENT_BLIK_OK = "✅ Twoje dane zostały przesłane. Dziękujemy! Zamówienie trafiło do obsługi."
PAYMENT_CASH_PROMPT = (
    "📦 Podaj <b>adres dostawy</b> (np. Gdańsk, ul. Długa 5/2).\n\n"
    "💡 Uwaga: kierowca nie wydaje reszty. Przygotuj odliczoną kwotę.\n"
    "Jeśli zapłacisz więcej — problemu nie będzie. 😊"
)
PAYMENT_CASH_OK = "✅ Adres został zapisany. Dziękujemy za zamówienie!"

# --- NAGŁÓWKI / SZABLONY POWIADOMIEŃ DLA ADMINÓW ---
ADMIN_ORDER_NEW_HEADER = "🛒 <b>Nowe zamówienie:</b>"
ADMIN_ORDER_DETAILS = (
    "🏙️ Miasto: <b>{city}</b>\n"
    "📂 Kategoria: <b>{category}</b>\n"
    "🛍️ Produkt: <b>{product_name}</b>\n"
    "💰 Cena: <b>{price} zł</b>"
)
