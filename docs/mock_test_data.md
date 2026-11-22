# SchedulerBot v4.4 - Comprehensive Mock Test Data Suite

This document contains ready-to-use JSON mock payloads for testing all APIs deployed at:
**`https://shivam-jha96--mockapi-server-fastapi-app.us-east.modal.run`**

---

## 1. Natural Language Schedule Parser (`POST /v1/parse-schedule`)

### Case A: Standard Future Schedule (Tomorrow Morning)
```json
{
  "message": "Remind Bob (+919123456789) tomorrow at 9:00 AM to bring the project slides",
  "timezone": "Asia/Kolkata"
}
```

### Case B: Specific Date and Time
```json
{
  "message": "Schedule message to Dr. Sharma (+919876500000) on 2026-11-25 at 16:30 for root canal follow-up",
  "timezone": "Asia/Kolkata"
}
```

### Case C: Missing Phone Number (Triggers Contact Card Request)
```json
{
  "message": "Remind John tomorrow at 10am to call the client",
  "timezone": "Asia/Kolkata"
}
```

---

## 2. Inbound Meta Webhooks (`POST /webhooks/whatsapp`)

### Case A: Alice Scheduling Request
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "15551234567"
            },
            "contacts": [
              {
                "profile": { "name": "Alice" },
                "wa_id": "919876543210"
              }
            ],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggMTAx...",
                "timestamp": "1795205400",
                "type": "text",
                "text": {
                  "body": "Remind Bob (+919123456789) tomorrow at 9:00 AM to bring the project slides"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case B: Profile Command (`NAME <Preferred Name>`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "15551234567"
            },
            "contacts": [{ "profile": { "name": "Alice Cooper" }, "wa_id": "919876543210" }],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggMTAy...",
                "timestamp": "1795205410",
                "type": "text",
                "text": { "body": "NAME Alice C." }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case C: Recipient Opt-In (`START` or `YES`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "15551234567"
            },
            "contacts": [{ "profile": { "name": "Bob" }, "wa_id": "919123456789" }],
            "messages": [
              {
                "from": "919123456789",
                "id": "wamid.HBgMOTE5MTIzNDU2Nzg5FQIAEhggMTAz...",
                "timestamp": "1795205420",
                "type": "text",
                "text": { "body": "START" }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case D: Global Opt-Out (`STOP`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "15551234567"
            },
            "contacts": [{ "profile": { "name": "Bob" }, "wa_id": "919123456789" }],
            "messages": [
              {
                "from": "919123456789",
                "id": "wamid.HBgMOTE5MTIzNDU2Nzg5FQIAEhggMTA0...",
                "timestamp": "1795205430",
                "type": "text",
                "text": { "body": "STOP" }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case E: Per-Sender Opt-Out (`UNSUBSCRIBE <Name>`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "15551234567"
            },
            "contacts": [{ "profile": { "name": "Bob" }, "wa_id": "919123456789" }],
            "messages": [
              {
                "from": "919123456789",
                "id": "wamid.HBgMOTE5MTIzNDU2Nzg5FQIAEhggMTA1...",
                "timestamp": "1795205440",
                "type": "text",
                "text": { "body": "UNSUBSCRIBE Alice" }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 3. Interactive Button Reply Webhooks (`POST /webhooks/whatsapp`)

### Case A: Alice Marks Message Sent Personally (`✅ I Sent It`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": { "display_phone_number": "15551234567", "phone_number_id": "15551234567" },
            "contacts": [{ "profile": { "name": "Alice" }, "wa_id": "919876543210" }],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggMTA2...",
                "timestamp": "1795205450",
                "type": "interactive",
                "interactive": {
                  "type": "button_reply",
                  "button_reply": {
                    "id": "SENT_VIA_PERSONAL:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "title": "✅ I Sent It"
                  }
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case B: Fast-Track Bot Delivery (`🤖 Send via Bot Now`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": { "display_phone_number": "15551234567", "phone_number_id": "15551234567" },
            "contacts": [{ "profile": { "name": "Alice" }, "wa_id": "919876543210" }],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggMTA3...",
                "timestamp": "1795205460",
                "type": "interactive",
                "interactive": {
                  "type": "button_reply",
                  "button_reply": {
                    "id": "BOT_RELAY:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "title": "🤖 Send via Bot Now"
                  }
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case C: Cancel Schedule (`❌ Cancel`)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": { "display_phone_number": "15551234567", "phone_number_id": "15551234567" },
            "contacts": [{ "profile": { "name": "Alice" }, "wa_id": "919876543210" }],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggMTA4...",
                "timestamp": "1795205470",
                "type": "interactive",
                "interactive": {
                  "type": "button_reply",
                  "button_reply": {
                    "id": "CANCEL_JOB:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "title": "❌ Cancel Schedule"
                  }
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 4. Message Status Update Webhooks (`POST /webhooks/whatsapp`)

### Case A: Delivered Status
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": { "display_phone_number": "15551234567", "phone_number_id": "15551234567" },
            "statuses": [
              {
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSQkE3...",
                "status": "delivered",
                "timestamp": "1795205480",
                "recipient_id": "919876543210"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Case B: Failed Status (Meta Error Code 131051 - Unsupported Message)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": { "display_phone_number": "15551234567", "phone_number_id": "15551234567" },
            "statuses": [
              {
                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSQkE3...",
                "status": "failed",
                "timestamp": "1795205490",
                "recipient_id": "919876543210",
                "errors": [
                  {
                    "code": 131051,
                    "title": "Message type not supported",
                    "message": "Template does not exist or has not been approved"
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 5. Account Quality Webhook (`POST /webhooks/whatsapp`)

### Circuit Breaker Trigger (Quality Rating -> RED)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ACCOUNT_ID",
      "changes": [
        {
          "field": "phone_number_quality_update",
          "value": {
            "display_phone_number": "15551234567",
            "event": "FLAGGED",
            "current_limit": "TIER_1K",
            "quality_rating": "RED"
          }
        }
      ]
    }
  ]
}
```

---

## 6. Outbound Meta WhatsApp Graph API v22.0 (`POST /v22.0/{phone_number_id}/messages`)

### Template 1: T-10m Advance Prep Nudge (`hybrid_notify_alice_v1`)
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "hybrid_notify_alice_v1",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Bob" },
          { "type": "text", "text": "8:50 AM" }
        ]
      }
    ]
  }
}
```

### Template 2: T_0 Primary Dispatch Card (`hybrid_dispatch_card_v1`)
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "hybrid_dispatch_card_v1",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Bob" },
          { "type": "text", "text": "9:00 AM" }
        ]
      },
      {
        "type": "button",
        "sub_type": "url",
        "index": "0",
        "parameters": [
          { "type": "text", "text": "919123456789?text=Bring%20the%20project%20slides" }
        ]
      }
    ]
  }
}
```

### Template 3: T+3m Escalation Nudge (`hybrid_escalation_v1`)
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "hybrid_escalation_v1",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Bob" },
          { "type": "text", "text": "7 minutes" }
        ]
      }
    ]
  }
}
```

### Template 4: T+10m Autonomous Bot Relay to Bob (`scheduled_relay_v1`)
```json
{
  "messaging_product": "whatsapp",
  "to": "919123456789",
  "type": "template",
  "template": {
    "name": "scheduled_relay_v1",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Alice (+91-98XXX-43210)" },
          { "type": "text", "text": "Bring the project slides" },
          { "type": "text", "text": "Alice" }
        ]
      }
    ]
  }
}
```

### Template 5: Cancellation Notice to Alice (`scheduled_cancelled_v1`)
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "scheduled_cancelled_v1",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Bob" },
          { "type": "text", "text": "recipient opted out" }
        ]
      }
    ]
  }
}
```

### Session Interactive Message (Buttons inside 24h Window)
```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "919876543210",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "✅ Scheduled for tomorrow at 9:00 AM!\n\nTo: Bob\nMessage: \"Bring the project slides\"\n\nAuto-Fallback is ON."
    },
    "action": {
      "buttons": [
        {
          "type": "reply",
          "reply": {
            "id": "TOGGLE_FALLBACK_OFF:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Disable Auto-Fallback"
          }
        },
        {
          "type": "reply",
          "reply": {
            "id": "CANCEL_JOB:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "title": "❌ Cancel"
          }
        }
      ]
    }
  }
}
```

---

## 7. Cloud KMS Cryptographic Services

### Generate Data Key (`POST /kms/generate-data-key`)
```json
{
  "key_spec": "AES_256"
}
```

### Encrypt Plaintext (`POST /kms/encrypt`)
*Note: `QnJpbmcgdGhlIHByb2plY3Qgc2xpZGVz` is base64 for `"Bring the project slides"`.*
```json
{
  "plaintext_b64": "QnJpbmcgdGhlIHByb2plY3Qgc2xpZGVz"
}
```

### Decrypt Ciphertext (`POST /kms/decrypt`)
*Takes the `ciphertext_b64` returned from `/kms/encrypt`.*
```json
{
  "ciphertext_b64": "<ciphertext_b64_from_encrypt_response>"
}
```

---

## 8. Developer Simulation Harness (`/mock/*`)

### Simulate Inbound Schedule (`POST /mock/simulate/inbound-schedule`)
```json
{
  "sender_wa_id": "919876543210",
  "sender_name": "Alice",
  "message": "Remind Bob (+919123456789) tomorrow at 9:00 AM to bring the project slides"
}
```

### Simulate Button Reply (`POST /mock/simulate/button-click`)
```json
{
  "sender_wa_id": "919876543210",
  "sender_name": "Alice",
  "button_id": "SENT_VIA_PERSONAL:job-12345",
  "button_title": "✅ I Sent It"
}
```

### Simulate Opt-Out (`POST /mock/simulate/opt-out`)
```json
{
  "sender_wa_id": "919123456789",
  "sender_name": "Bob",
  "action": "STOP"
}
```

### Set Phone Quality Rating (`POST /mock/set-quality`)
```json
{
  "phone_number_id": "15551234567",
  "quality_rating": "YELLOW"
}
```
