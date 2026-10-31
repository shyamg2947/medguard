# WhatsApp Cloud API Message Templates

These pre-approved WhatsApp templates are used when communicating with users outside the 24-hour customer service window, including weekly check-ins and critical caregiver notifications.

## 1. Weekly Senior Check-in (`weekly_senior_checkin`)
- **Category**: UTILITY
- **Languages**: `en`, `hi`, `kn`
- **Body (en)**:
  "Hello {{1}}, this is MedGuard with your weekly medicine safety check-in. Have you experienced any dizziness, falls, stomach pain, bleeding, or unusual swelling this week? Reply 'No' or tell us what you felt."
- **Body (hi)**:
  "नमस्ते {{1}}, यह मेडगार्ड का साप्ताहिक स्वास्थ्य चेक-इन है। क्या आपको इस सप्ताह चक्कर, कमजोरी, पेट दर्द या सूजन महसूस हुई? हमें बताएं या 'नहीं' लिखकर उत्तर दें।"
- **Buttons**:
  - `QUICK_REPLY`: "All Good / सब ठीक है"
  - `QUICK_REPLY`: "Report Symptom / लक्षण बताएं"

## 2. Urgent Caregiver Critical Alert (`caregiver_critical_alert`)
- **Category**: UTILITY
- **Languages**: `en`, `hi`
- **Body (en)**:
  "URGENT MedGuard Notice: A critical medication safety alert was detected for {{1}} regarding {{2}}. Please review their discussion guide: {{3}}."
- **Body (hi)**:
  "अति आवश्यक मेडगार्ड सूचना: {{1}} के लिए {{2}} से संबंधित एक गंभीर दवा सुरक्षा चेतावनी दर्ज की गई है। कृपया रिपोर्ट देखें: {{3}}।"

## 3. Red Flag Emergency Notice (`caregiver_red_flag_alert`)
- **Category**: UTILITY
- **Languages**: `en`, `hi`
- **Body (en)**:
  "EMERGENCY: {{1}} just reported a red-flag symptom ({{2}}). Please check on them or call emergency services immediately."
- **Body (hi)**:
  "आपातकालीन सूचना: {{1}} ने आपातकालीन लक्षण ({{2}}) की सूचना दी है। कृपया तुरंत उनसे संपर्क करें या आपातकालीन सेवा को कॉल करें।"

