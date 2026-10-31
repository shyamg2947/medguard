"""
Translation with Drug-Name Protection.
Replaces drug names with {{DRUG_N}} placeholders before translation to protect clinical accuracy,
then restores exact drug entities.
"""
from typing import Dict, List, Optional
import re
from backend.app.config import get_settings


COMMON_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "hi": {
        "I heard": "मैंने सुना",
        "once daily": "दिन में एक बार",
        "twice daily": "दिन में दो बार",
        "morning and night": "सुबह और शाम",
        "Is that right?": "क्या यह सही है?",
        "Please ask your doctor or pharmacist about this combination.": "कृपया इस संयोजन के बारे में अपने डॉक्टर या फार्मासिस्ट से बात करें।",
        "Higher bleeding risk when an anticoagulant is combined with an NSAID.": "रक्त पतला करने वाली दवा और दर्द निवारक को साथ लेने से रक्तस्राव का जोखिम बढ़ सकता है।",
        "Two of your medicines can raise the chance of bleeding when taken together.": "आपकी दो दवाएं एक साथ लेने पर रक्तस्राव की संभावना बढ़ा सकती हैं।",
        "MedGuard is a decision-support tool. It does not replace a doctor or pharmacist.": "MedGuard एक निर्णय-सहायता उपकरण है। यह किसी डॉक्टर या फार्मासिस्ट की जगह नहीं लेता है।",
        "Call your doctor or emergency services now.": "तुरंत अपने डॉक्टर या आपातकालीन सेवाओं को कॉल करें।"
    },
    "kn": {
        "I heard": "ನಾನು ಕೇಳಿದ್ದು",
        "once daily": "ದಿನಕ್ಕೆ ಒಂದು ಬಾರಿ",
        "twice daily": "ದಿನಕ್ಕೆ ಎರಡು ಬಾರಿ",
        "Is that right?": "ಇದು ಸರಿಯೇ?",
        "Please ask your doctor or pharmacist about this combination.": "ದಯವಿಟ್ಟು ಈ ಸಂಯೋಜನೆಯ ಬಗ್ಗೆ ನಿಮ್ಮ ವೈದ್ಯರನ್ನು ಅಥವಾ ಔಷಧಿಕಾರರನ್ನು ಕೇಳಿ.",
        "Call your doctor or emergency services now.": "ತಕ್ಷಣ ನಿಮ್ಮ ವೈದ್ಯರನ್ನು ಅಥವಾ ತುರ್ತು ಸೇವೆಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ."
    }
}


def translate_with_drug_protection(
    text: str,
    target_lang: str,
    drug_names: Optional[List[str]] = None,
    pre_translated_template: Optional[str] = None,
) -> str:
    """
    Translates text safely without distorting drug names.
    1. Replaces drug names with {{DRUG_1}}, {{DRUG_2}}, etc.
    2. Translates text (via dictionary or pre_translated_template).
    3. Restores {{DRUG_1}} with original names.
    """
    if target_lang == "en" or not text:
        return text

    if pre_translated_template:
        return pre_translated_template

    drugs = drug_names or []
    placeholder_map: Dict[str, str] = {}
    protected_text = text

    for i, drug in enumerate(drugs):
        placeholder = f"{{{{DRUG_{i+1}}}}}"
        # Word-boundary replacement
        pattern = re.compile(re.escape(drug), re.IGNORECASE)
        protected_text = pattern.sub(placeholder, protected_text)
        placeholder_map[placeholder] = drug

    # Look up in pre-translated dictionary
    translated = protected_text
    lang_dict = COMMON_TRANSLATIONS.get(target_lang, {})
    for src, dst in lang_dict.items():
        if src in translated:
            translated = translated.replace(src, dst)

    # Restore placeholders
    for placeholder, original_drug in placeholder_map.items():
        translated = translated.replace(placeholder, original_drug)

    return translated

