export type SupportedLanguage = 'en' | 'hi' | 'kn';

export interface Translations {
  appName: string;
  tagline: string;
  heroHeadline: string;
  heroSubheadline: string;
  tryDemo: string;
  howItWorks: string;
  sayItTitle: string;
  sayItDesc: string;
  checkItTitle: string;
  checkItDesc: string;
  shareItTitle: string;
  shareItDesc: string;
  tapToSpeak: string;
  listening: string;
  processing: string;
  doctorDiscussionGuide: string;
  emergencyNotice: string;
  callCaregiver: string;
  callEmergency: string;
  readToMe: string;
  textSize: string;
  highContrast: string;
  activeMedications: string;
  activeSafetyAlerts: string;
  noAlertsFound: string;
  askDoctorQuestion: string;
  sourcesLabel: string;
  disclaimer: string;
}

export const translations: Record<SupportedLanguage, Translations> = {
  en: {
    appName: "MedGuard",
    tagline: "Voice-first multilingual medication safety assistant for seniors.",
    heroHeadline: "Medicine safety, in your language.",
    heroSubheadline: "Speak or scan your medicines. MedGuard checks for clinical interactions, duplicate ingredients, and geriatric risks, producing a clear Doctor Discussion Guide.",
    tryDemo: "Try the Demo",
    howItWorks: "How it works",
    sayItTitle: "1. Say It",
    sayItDesc: "Simply speak your medicine names or upload a photo of the strip. MedGuard understands local Indian brand names and transliterations.",
    checkItTitle: "2. Check It",
    checkItDesc: "A deterministic clinical rules engine checks published geriatric safety criteria (Beers, STOPP/START, ACB) with zero AI hallucinations.",
    shareItTitle: "3. Share It",
    shareItDesc: "Download a structured 1-page Doctor Discussion Guide with questions ready for your next clinical visit.",
    tapToSpeak: "Tap to Speak",
    listening: "Listening...",
    processing: "Checking safety...",
    doctorDiscussionGuide: "Doctor Discussion Guide",
    emergencyNotice: "Decision support only. If experiencing severe symptoms, call 112 immediately.",
    callCaregiver: "Call Caregiver",
    callEmergency: "Call 112 (Emergency)",
    readToMe: "Read this to me",
    textSize: "Text Size",
    highContrast: "High Contrast",
    activeMedications: "Active Medications",
    activeSafetyAlerts: "Safety Discussion Points",
    noAlertsFound: "No high-risk interactions detected in your current list.",
    askDoctorQuestion: "Question for your doctor:",
    sourcesLabel: "Clinical Reference:",
    disclaimer: "MedGuard does not diagnose, prescribe, or direct anyone to stop or change medication. It empowers informed clinical conversations."
  },
  hi: {
    appName: "MedGuard",
    tagline: "वरिष्ठ नागरिकों के लिए आवाज-आधारित बहुभाषी दवा सुरक्षा सहायक।",
    heroHeadline: "दवाओं की सुरक्षा, आपकी अपनी भाषा में।",
    heroSubheadline: "अपनी दवाओं के नाम बोलें या फोटो दिखाएं। MedGuard हानिकारक प्रभावों और बुजुर्गों के जोखिमों की तुरंत जांच करता है।",
    tryDemo: "डेमो आजमाएं",
    howItWorks: "यह कैसे काम करता है",
    sayItTitle: "1. नाम बताएं",
    sayItDesc: "आराम से अपनी भाषा में दवा का नाम बोलें या पत्ते की तस्वीर खींचें। MedGuard भारतीय ब्रांड नामों को पहचानता है।",
    checkItTitle: "2. जांचें",
    checkItDesc: "स्थापित मेडिकल दिशानिर्देशों (Beers, STOPP/START) के आधार पर सुरक्षित नियम इंजन दवाओं की जांच करता है।",
    shareItTitle: "3. डॉक्टर से साझा करें",
    shareItDesc: "डॉक्टर चर्चा गाइड (PDF) प्राप्त करें ताकि आप अपने डॉक्टर से सही सवाल पूछ सकें।",
    tapToSpeak: "बोलने के लिए दबाएं",
    listening: "सुन रहे हैं...",
    processing: "सुरक्षा जांच जारी है...",
    doctorDiscussionGuide: "डॉक्टर चर्चा गाइड",
    emergencyNotice: "यदि तेज दर्द या गंभीर लक्षण हों, तो तुरंत 112 पर कॉल करें।",
    callCaregiver: "देखभालकर्ता को कॉल करें",
    callEmergency: "112 (आपातकालीन) कॉल",
    readToMe: "यह पढ़कर सुनाएं",
    textSize: "अक्षर का आकार",
    highContrast: "उच्च कंट्रास्ट",
    activeMedications: "वर्तमान दवाएं",
    activeSafetyAlerts: "डॉक्टर से पूछने योग्य बातें",
    noAlertsFound: "वर्तमान सूची में कोई गंभीर जोखिम नहीं मिला।",
    askDoctorQuestion: "डॉक्टर से पूछें:",
    sourcesLabel: "चिकित्सीय संदर्भ:",
    disclaimer: "MedGuard डॉक्टर नहीं है। यह किसी भी दवा को बदलने या बंद करने का निर्देश नहीं देता है।"
  },
  kn: {
    appName: "MedGuard",
    tagline: "ಹಿರಿಯ ನಾಗರಿಕರಿಗೆ ಧ್ವನಿ ಆಧಾರಿತ ಬಹುಭಾಷಾ ಔಷಧಿ ಸುರಕ್ಷತಾ ಸಹಾಯಕ.",
    heroHeadline: "ಔಷಧಗಳ ಸುರಕ್ಷತೆ, ನಿಮ್ಮದೇ ಭಾಷೆಯಲ್ಲಿ.",
    heroSubheadline: "ನಿಮ್ಮ ಔಷಧಿಗಳ ಹೆಸರನ್ನು ಮಾತನಾಡಿ ಅಥವಾ ಪಟ್ಟಿಯ ಫೋಟೋ ತೋರಿಸಿ. MedGuard ಅಪಾಯಕಾರಿ ಪರಿಣಾಮಗಳನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ.",
    tryDemo: "ಡೆಮೊ ಪ್ರಯತ್ನಿಸಿ",
    howItWorks: "ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ",
    sayItTitle: "1. ಹೆಸರು ಹೇಳಿ",
    sayItDesc: "ನಿಮ್ಮ ಔಷಧಿಗಳ ಹೆಸರನ್ನು ಸರಳವಾಗಿ ಮಾತನಾಡಿ. MedGuard ಸ್ಥಳೀಯ ಬ್ರ್ಯಾಂಡ್‌ಗಳನ್ನು ಗುರುತಿಸುತ್ತದೆ.",
    checkItTitle: "2. ಪರಿಶೀಲಿಸಿ",
    checkItDesc: "ಸ್ಥಾಪಿತ ಜೆರಿಯಾಟ್ರಿಕ್ ಮಾರ್ಗಸೂಚಿಗಳ ಆಧಾರದ ಮೇಲೆ ಸುರಕ್ಷತಾ ನಿಯಮಗಳ ಎಂಜಿನ್ ಪರೀಕ್ಷಿಸುತ್ತದೆ.",
    shareItTitle: "3. ವೈದ್ಯರೊಂದಿಗೆ ಹಂಚಿಕೊಳ್ಳಿ",
    shareItDesc: "ನಿಮ್ಮ ಮುಂದಿನ ಭೇಟಿಗಾಗಿ ವೈದ್ಯರ ಚರ್ಚಾ ಮಾರ್ಗದರ್ಶಿಯನ್ನು (PDF) ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.",
    tapToSpeak: "ಮಾತನಾಡಲು ಒತ್ತಿರಿ",
    listening: "ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದೆ...",
    processing: "ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    doctorDiscussionGuide: "ವೈದ್ಯರ ಚರ್ಚಾ ಮಾರ್ಗದರ್ಶಿ",
    emergencyNotice: "ತುರ್ತು ಪರಿಸ್ಥಿತಿ ಇದ್ದರೆ ತಕ್ಷಣ 112 ಗೆ ಕರೆ ಮಾಡಿ.",
    callCaregiver: "ಆರೈಕೆದಾರರಿಗೆ ಕರೆ ಮಾಡಿ",
    callEmergency: "112 (ತುರ್ತು ಕರೆ)",
    readToMe: "ಓದಿ ಕೇಳಿಸಿ",
    textSize: "ಅಕ್ಷರದ ಗಾತ್ರ",
    highContrast: "ಹೈ ಕಾಂಟ್ರಾಸ್ಟ್",
    activeMedications: "ಪ್ರಸ್ತುತ ಔಷಧಿಗಳು",
    activeSafetyAlerts: "ವೈದ್ಯರೊಂದಿಗೆ ಚರ್ಚಿಸಬೇಕಾದ ಅಂಶಗಳು",
    noAlertsFound: "ಯಾವುದೇ ಗಂಭೀರ ಅಪಾಯ ಕಂಡುಬಂದಿಲ್ಲ.",
    askDoctorQuestion: "ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕಾದ ಪ್ರಶ್ನೆ:",
    sourcesLabel: "ವೈದ್ಯಕೀಯ ಆಧಾರ:",
    disclaimer: "MedGuard ವೈದ್ಯರಲ್ಲ. ಯಾವುದೇ ಔಷಧಿಯನ್ನು ನಿಲ್ಲಿಸಲು ಅಥವಾ ಬದಲಾಯಿಸಲು ಸೂಚಿಸುವುದಿಲ್ಲ."
  }
};

