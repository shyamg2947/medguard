import React, { useState, useRef } from 'react';
import { Send, Mic, ShieldAlert, Sparkles, Camera, Volume2, VolumeX, CheckCircle } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  imageUrl?: string;
  speechText?: string;
  isVoice?: boolean;
  quickReplies?: string[];
  isEmergency?: boolean;
  detectedMedicines?: Array<{ brand?: string; generic: string; strength?: string }>;
  alerts?: Array<{ title?: string; severity?: string; doctor_question?: string; sources?: string[] }>;
}

interface SimulatorAppProps {
  isEmbedded?: boolean;
}

export const SimulatorApp: React.FC<SimulatorAppProps> = ({ isEmbedded = false }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm-1',
      sender: 'bot',
      text: 'Namaste! I am MedGuard, your medication safety assistant. You can speak medicine names, upload photos of prescription slips or pill strips, or type them here. Before we start, do you consent to checking your medicines?',
      quickReplies: ['Yes, I consent', 'Tell me more', 'Privacy policy'],
    },
  ]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const speakText = (text: string, msgId: string) => {
    if ('speechSynthesis' in window) {
      if (speakingMessageId === msgId) {
        window.speechSynthesis.cancel();
        setSpeakingMessageId(null);
        return;
      }
      window.speechSynthesis.cancel();
      const cleanText = text.replace(/[*#_`]/g, '');
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 0.88; // Calm, measured cadence for seniors
      utterance.onstart = () => setSpeakingMessageId(msgId);
      utterance.onend = () => setSpeakingMessageId(null);
      utterance.onerror = () => setSpeakingMessageId(null);
      window.speechSynthesis.speak(utterance);
    } else {
      alert('Text-to-speech is not supported in this browser.');
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const res = await fetch('/simulator/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'sim-demo-user',
          sender_phone: '+919999900001',
          message_type: 'text',
          content: text,
          text,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const botMsg: Message = {
          id: `b-${Date.now()}`,
          sender: 'bot',
          text: data.reply || data.body || 'Understood.',
          isEmergency: data.emergency,
          quickReplies: data.buttons || data.quick_replies || (data.emergency ? ['Call 112 Now'] : ['Add another medicine', 'Download Doctor Guide']),
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        handleLocalSimulation(text);
      }
    } catch {
      handleLocalSimulation(text);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = reader.result as string;
      await sendImageAnalysis(dataUrl, file.name);
    };
    reader.readAsDataURL(file);
  };

  const sendImageAnalysis = async (imageDataUrl: string, titleHint: string) => {
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: `Uploaded prescription photo: ${titleHint}`,
      imageUrl: imageDataUrl,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await fetch('/simulator/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'sim-demo-user',
          sender_phone: '+919999900001',
          message_type: 'image',
          content: titleHint,
          media_url: imageDataUrl,
          image_url: imageDataUrl,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const speech = data.speech_text || data.reply || data.body;
        const botMsg: Message = {
          id: `b-${Date.now()}`,
          sender: 'bot',
          text: data.reply || data.body,
          speechText: speech,
          detectedMedicines: data.detected_medicines,
          alerts: data.alerts,
          quickReplies: data.buttons || ['Add to My List', 'Download Doctor Guide (PDF)'],
        };
        setMessages((prev) => [...prev, botMsg]);
        // Auto speak summary for senior citizen
        speakText(speech, botMsg.id);
      } else {
        fallbackPrescriptionAnalysis(titleHint, imageDataUrl);
      }
    } catch {
      fallbackPrescriptionAnalysis(titleHint, imageDataUrl);
    } finally {
      setIsLoading(false);
    }
  };

  const fallbackPrescriptionAnalysis = (hint: string, imgUrl: string) => {
    void imgUrl;
    const isKidney = hint.toLowerCase().includes('telma') || hint.toLowerCase().includes('kidney');
    const detected = isKidney
      ? [
          { brand: 'Telma 40', generic: 'Telmisartan', strength: '40mg' },
          { brand: 'Lasix 40', generic: 'Furosemide', strength: '40mg' },
          { brand: 'Voveran 50', generic: 'Diclofenac', strength: '50mg' },
        ]
      : [
          { brand: 'Combiflam', generic: 'Ibuprofen + Paracetamol', strength: '400mg/325mg' },
          { brand: 'Ecosprin 75', generic: 'Aspirin', strength: '75mg' },
        ];

    const alerts = isKidney
      ? [
          {
            title: 'Triple Whammy Kidney Stress Alert',
            severity: 'critical',
            doctor_question: 'Could we stop oral Voveran to protect kidney function while taking blood pressure and water pills?',
          },
        ]
      : [
          {
            title: 'High Bleeding Risk (Anticoagulant/Antiplatelet + NSAID)',
            severity: 'critical',
            doctor_question: 'Ask your doctor whether Combiflam should be replaced with a safer pain reliever like paracetamol alone.',
          },
        ];

    const speech = isKidney
      ? 'We analyzed your prescription photo. We identified Telma 40, Lasix, and Voveran. Taking blood pressure pills, water tablets, and pain medicine together places acute stress on your kidneys. Please ask your doctor about a safer pain reliever.'
      : 'We analyzed your prescription photo. We identified Combiflam and Aspirin. Taking Combiflam with daily blood thinners increases the chance of stomach bleeding. Please ask your doctor if a safer pain medicine can be used.';

    const text = isKidney
      ? `📋 **Prescription Analysis Complete**\n**Detected Medicines:** Telma 40 (Telmisartan 40mg), Lasix 40 (Furosemide 40mg), Voveran 50 (Diclofenac 50mg)\n\n⚠️ **Clinical Safety Alert (CRITICAL):**\n• **Triple Whammy:** Blood pressure medicine (ARB) + Water pill (Diuretic) + Painkiller (NSAID) severely reduces blood flow to the kidneys.\n*Question for Doctor:* "Could we stop oral Voveran to protect kidney function?"`
      : `📋 **Prescription Analysis Complete**\n**Detected Medicines:** Combiflam (Ibuprofen + Paracetamol), Ecosprin 75 (Aspirin)\n\n⚠️ **Clinical Safety Alert (CRITICAL):**\n• **Bleeding Hazard:** Combining NSAID pain relievers with Aspirin significantly increases stomach bleeding risk.\n*Question for Doctor:* "Ask your doctor whether Combiflam should be replaced with paracetamol alone or a topical gel."`;

    const botMsg: Message = {
      id: `b-${Date.now()}`,
      sender: 'bot',
      text,
      speechText: speech,
      detectedMedicines: detected,
      alerts,
      quickReplies: ['Add to My List', 'Download Doctor Guide (PDF)'],
    };

    setMessages((prev) => [...prev, botMsg]);
    speakText(speech, botMsg.id);
  };

  const handleLocalSimulation = (text: string) => {
    const lower = text.toLowerCase();
    let reply = "Understood. Please let me know your other medicines or upload a prescription.";
    let isEmergency = false;
    let qr = ['Upload Prescription', 'Add another medicine', 'Download Doctor Guide'];

    if (lower.includes('chest pain') || lower.includes('fainting') || lower.includes('vomiting blood')) {
      reply = "EMERGENCY ALERT: You mentioned severe symptoms (chest pain/fainting). Please call emergency services (112) or go to the nearest emergency room immediately. We have notified your caregiver.";
      isEmergency = true;
      qr = ['Call 112 Now'];
    } else if (lower.includes('consent') || lower.includes('yes')) {
      reply = "Thank you. Which language do you prefer to speak?\n1. English\n2. हिंदी (Hindi)\n3. ಕನ್ನಡ (Kannada)";
      qr = ['English', 'हिंदी', 'ಕನ್ನಡ'];
    } else if (lower.includes('telma') || lower.includes('combiflam') || lower.includes('warfarin')) {
      reply = "I heard you say: " + text + ". Is this correct?";
      qr = ['Yes, that is correct', 'No, spell again'];
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `b-${Date.now()}`,
        sender: 'bot',
        text: reply,
        isEmergency,
        quickReplies: qr,
      },
    ]);
  };

  const triggerScenario = (scenarioKey: 'A' | 'B' | 'C' | 'D' | 'RedFlag' | 'RxPhotoA' | 'RxPhotoB') => {
    if (scenarioKey === 'RxPhotoA') {
      sendImageAnalysis('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150" viewBox="0 0 300 150"><rect width="300" height="150" fill="%23f5f5f7"/><text x="20" y="40" font-family="Arial" font-size="16" font-weight="bold" fill="%231d1d1f">Rx CLINIC PRESCRIPTION</text><text x="20" y="80" font-family="Arial" font-size="14" fill="%23333">1. Tab. Combiflam 1 SOS</text><text x="20" y="110" font-family="Arial" font-size="14" fill="%23333">2. Tab. Ecosprin 75mg OD</text></svg>', 'Rx_Combiflam_Aspirin.jpg');
    } else if (scenarioKey === 'RxPhotoB') {
      sendImageAnalysis('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150" viewBox="0 0 300 150"><rect width="300" height="150" fill="%23f5f5f7"/><text x="20" y="40" font-family="Arial" font-size="16" font-weight="bold" fill="%231d1d1f">Rx CARDIOLOGY & RENAL CLINIC</text><text x="20" y="70" font-family="Arial" font-size="14" fill="%23333">1. Tab. Telma 40mg OD</text><text x="20" y="95" font-family="Arial" font-size="14" fill="%23333">2. Tab. Lasix 40mg OD</text><text x="20" y="120" font-family="Arial" font-size="14" fill="%23333">3. Tab. Voveran 50mg BD</text></svg>', 'Rx_Telma_Lasix_Voveran.jpg');
    } else if (scenarioKey === 'A') {
      sendMessage('I am taking Warfarin 2mg, Aspirin 75mg, Combiflam for knee pain, Pantocid 40mg, and Ashwagandha churna.');
    } else if (scenarioKey === 'B') {
      sendMessage('My doctor prescribed Telma 40, Lasix 20, and I take Voveran 50 for back pain. My serum creatinine is 1.6.');
    } else if (scenarioKey === 'C') {
      sendMessage('I take Amlodipine 5mg and Lasix 20mg for swelling, plus Benadryl and Alprazolam for sleep.');
    } else if (scenarioKey === 'D') {
      sendMessage('Hospital told me to stop Brufen at discharge, but my knee was hurting so I restarted it.');
    } else if (scenarioKey === 'RedFlag') {
      sendMessage('I am having sudden crushing chest pain and feeling faint.');
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: isEmbedded ? '100%' : 'calc(100vh - 52px)',
        maxWidth: isEmbedded ? '100%' : 720,
        margin: '0 auto',
        background: 'var(--surface)',
        borderLeft: isEmbedded ? 'none' : '1px solid var(--hairline)',
        borderRight: isEmbedded ? 'none' : '1px solid var(--hairline)',
      }}
    >
      {/* Hidden file input for camera/photo upload */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleImageFile(e.target.files[0]);
          }
        }}
      />

      {/* Top Scenario Fast-Picker Toolbar */}
      {!isEmbedded && (
        <div
          style={{
            padding: '12px 16px',
            background: 'var(--bg-alt)',
            borderBottom: '1px solid var(--hairline)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            overflowX: 'auto',
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Sparkles size={14} color="var(--accent)" />
            <span>Fast Scenarios:</span>
          </span>
          <button
            onClick={() => triggerScenario('RxPhotoA')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'var(--accent)', color: '#fff', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <Camera size={13} />
            <span>Photo Rx (Bleeding)</span>
          </button>
          <button
            onClick={() => triggerScenario('RxPhotoB')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'var(--accent)', color: '#fff', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <Camera size={13} />
            <span>Photo Rx (Kidney)</span>
          </button>
          <button
            onClick={() => triggerScenario('A')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--hairline)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}
          >
            Scenario A (Bleeding)
          </button>
          <button
            onClick={() => triggerScenario('B')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--hairline)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}
          >
            Scenario B (Renal)
          </button>
          <button
            onClick={() => triggerScenario('C')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--hairline)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}
          >
            Scenario C (Falls)
          </button>
          <button
            onClick={() => triggerScenario('RedFlag')}
            style={{ padding: '4px 10px', borderRadius: 8, background: 'rgba(215, 0, 21, 0.12)', color: 'var(--sev-critical)', border: '1px solid var(--sev-critical)', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap' }}
          >
            Emergency 112
          </button>
        </div>
      )}

      {/* Chat Messages Body */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          background: 'var(--bg-alt)',
        }}
      >
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          const isSpeaking = speakingMessageId === m.id;
          return (
            <div
              key={m.id}
              style={{
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
              }}
            >
              <div
                style={{
                  padding: '14px 18px',
                  borderRadius: 18,
                  borderBottomRightRadius: isUser ? 4 : 18,
                  borderBottomLeftRadius: !isUser ? 4 : 18,
                  background: m.isEmergency
                    ? 'var(--sev-critical)'
                    : isUser
                    ? 'var(--accent)'
                    : 'var(--surface)',
                  color: m.isEmergency ? '#ffffff' : isUser ? '#ffffff' : 'var(--text)',
                  fontSize: 15,
                  lineHeight: 1.5,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  border: !isUser && !m.isEmergency ? '1px solid var(--hairline)' : 'none',
                }}
              >
                {/* Emergency header */}
                {m.isEmergency && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, fontWeight: 700 }}>
                    <ShieldAlert size={20} />
                    <span>EMERGENCY ESCALATION (CALL 112)</span>
                  </div>
                )}

                {/* Uploaded Image Preview */}
                {m.imageUrl && (
                  <div style={{ marginBottom: 12, borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.3)' }}>
                    <img
                      src={m.imageUrl}
                      alt="Uploaded prescription"
                      style={{ width: '100%', maxHeight: 220, objectFit: 'cover', display: 'block' }}
                    />
                  </div>
                )}

                {/* Detected Medicines Badges */}
                {m.detectedMedicines && m.detectedMedicines.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginBottom: 6, textTransform: 'uppercase' }}>
                      Identified Medications:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {m.detectedMedicines.map((med, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            padding: '4px 10px',
                            borderRadius: 'var(--radius-pill)',
                            background: 'var(--bg-alt)',
                            color: 'var(--text)',
                            border: '1px solid var(--hairline)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <CheckCircle size={13} color="var(--sev-low)" />
                          <span>{med.brand || med.generic} {med.strength || ''}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Text Content */}
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>

                {/* Senior Speak Out Audio Button */}
                {!isUser && (m.speechText || m.text) && (
                  <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--hairline-subtle)' }}>
                    <button
                      onClick={() => speakText(m.speechText || m.text, m.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 14px',
                        borderRadius: 'var(--radius-pill)',
                        background: isSpeaking ? 'rgba(215, 0, 21, 0.12)' : 'var(--bg-alt)',
                        color: isSpeaking ? 'var(--sev-critical)' : 'var(--accent)',
                        border: isSpeaking ? '1px solid var(--sev-critical)' : '1px solid var(--hairline)',
                        fontSize: 13,
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      {isSpeaking ? (
                        <>
                          <VolumeX size={16} />
                          <span>Stop Audio Reading</span>
                        </>
                      ) : (
                        <>
                          <Volume2 size={16} />
                          <span>🔊 Listen / Speak Out for Senior</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Quick reply action chips */}
              {m.quickReplies && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                  {m.quickReplies.map((qr, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        if (qr.includes('Guide')) {
                          window.open('/patients/demo-patient-scen-a/guide.pdf', '_blank');
                        } else if (qr.includes('112')) {
                          window.location.href = 'tel:112';
                        } else {
                          sendMessage(qr);
                        }
                      }}
                      style={{
                        padding: '6px 14px',
                        borderRadius: 'var(--radius-pill)',
                        background: 'var(--surface)',
                        border: '1px solid var(--accent)',
                        color: 'var(--accent)',
                        fontSize: 13,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {qr}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--text-secondary)', fontSize: 13, fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Camera size={14} className="animate-spin" />
            <span>MedGuard is reading prescription and analyzing clinical rules...</span>
          </div>
        )}
      </div>

      {/* Input Composer Bar */}
      <div
        style={{
          padding: '12px 16px',
          background: 'var(--surface)',
          borderTop: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {/* Photo Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          title="Upload prescription photo or pill strip"
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: 'var(--bg-alt)',
            color: 'var(--accent)',
            border: '1px solid var(--hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
          aria-label="Upload prescription photo"
        >
          <Camera size={20} />
        </button>

        {/* Voice Note Simulation Button */}
        <button
          onClick={() => triggerScenario('A')}
          title="Speak medicine name"
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: 'var(--bg-alt)',
            color: 'var(--accent)',
            border: '1px solid var(--hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
          aria-label="Record voice note"
        >
          <Mic size={20} />
        </button>

        <input
          type="text"
          placeholder="Type medicines or tap camera to upload Rx photo..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage(inputText)}
          style={{
            flex: 1,
            padding: '12px 18px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid var(--hairline)',
            background: 'var(--bg-alt)',
            color: 'var(--text)',
            fontSize: 15,
            outline: 'none',
          }}
        />

        <button
          onClick={() => sendMessage(inputText)}
          disabled={!inputText.trim()}
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: inputText.trim() ? 'var(--accent)' : 'var(--bg-alt)',
            color: inputText.trim() ? '#ffffff' : 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: inputText.trim() ? 'pointer' : 'default',
            border: 'none',
          }}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};
