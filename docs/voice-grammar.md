# EFL Agent Assistant Voice Command Grammar

## Overview

This document describes the voice command grammar and natural language understanding capabilities of the EFL Agent Assistant, with specific focus on West African English pronunciation patterns and logistics terminology commonly used in Nigerian shipping and terminal operations.

## Core Voice Commands

### Container Tracking Commands

#### Standard English
```
"Track container EFLU7896543"
"I want to check container status for EFLU7896543"
"What's the status of container number EFLU7896543?"
```

#### West African English Variations
```
"Track containah EFLU7896543"
"Check containah seven eight nine six five four three"
"Find containah EFLU seven eight nine six five four three"
```

### Bill of Lading Tracking Commands

#### Standard English
```
"Track BL ABC1234567"
"Check bill of lading ABC1234567"
"What's the status of shipment ABC1234567?"
```

#### West African English Variations
```
"Track bill of laden ABC1234567"
"Check BL number ABC one two three four five six seven"
"Find shipment ABC1234567"
```

### Status Inquiry Commands

#### Standard English
```
"What is the current status?"
"Where is the container located?"
"What is the next step?"
"When will it arrive?"
```

#### West African English Variations
```
"Wetin be the status?"
"Where the containah dey now?"
"What be the next step?"
"When e go reach?"
```

## Supported Intents

### Primary Intents

1. **TrackContainer**
   - Purpose: Track container by container number
   - Confidence: High (specific container ID format)

2. **TrackBL**
   - Purpose: Track shipment by Bill of Lading number
   - Confidence: High (specific BL format)

3. **CheckStatus**
   - Purpose: Get current status of previously mentioned item
   - Confidence: Medium (context-dependent)

4. **GetLocation**
   - Purpose: Get current location of container/shipment
   - Confidence: Medium

5. **GetNextStep**
   - Purpose: Get next action required
   - Confidence: High

6. **Clarify**
   - Purpose: Handle unclear or ambiguous requests
   - Confidence: Low (fallback intent)

### Secondary Intents

1. **HelpRequest**
   - Purpose: Request help or guidance
   - Confidence: High (clear help indicators)

2. **Confirmation**
   - Purpose: Confirm previous action or information
   - Confidence: Medium

3. **Cancellation**
   - Purpose: Cancel current operation
   - Confidence: High

## Entity Recognition

### Container ID Entities

**Format**: `EFLU` + 7 digits (e.g., EFLU7896543)

**Pronunciation Variations**:
- Standard: "E-F-L-U seven eight nine six five four three"
- West African: "EFLU seven eight nine six five four three"
- Alternative: "EFLU seven eight nine, six five four three"

**Recognition Patterns**:
```
EFLU[digits:7]
EFLU [digits:7]
E F L U [digits:7]
```

### Bill of Lading Entities

**Format**: 3-4 letters + 7-10 digits/letters

**Common Patterns**:
- `ABC1234567` (3 letters + 7 digits)
- `ABCD1234567` (4 letters + 7 digits)
- `CMA123456789` (3 letters + 9 digits)

**Pronunciation Variations**:
- Standard: "A-B-C one two three four five six seven"
- West African: "ABC one two three four five six seven"
- Alternative: "ABC one two three, four five six seven"

### Location Entities

**Terminal Locations**:
- "EFL Terminal Ikorodu"
- "Lagos Port Complex"
- "Tin Can Island Port"
- "Lekki Deep Seaport"

**Pronunciation Variations**:
- "EFL terminah Ikorodu"
- "Lagos Port Complex"
- "Tin Can Island Port"
- "Lekki Deep Seaport"

### Status Entities

**Container Status Terms**:
- "in transit"
- "at terminal"
- "cleared for exam"
- "under examination"
- "released"
- "on hold"
- "delivered"

**West African Variations**:
- "in transit" (same)
- "for terminah" (at terminal)
- "cleared for exam" (same)
- "dey examine" (under examination)
- "released" (same)
- "for hold" (on hold)
- "delivered" (same)

## Grammar Patterns

### Basic Command Structure

```
[Intent] [Entity] [Qualifier]*
```

**Examples**:
- "Track [container EFLU7896543]"
- "Check [status] for [container EFLU7896543]"
- "Get [location] of [BL ABC1234567]"

### Complex Commands with Modifiers

```
[Intent] [Entity] [Preposition] [Time/Location] [Qualifier]*
```

**Examples**:
- "Track container EFLU7896543 at terminal"
- "Check status for BL ABC1234567 from yesterday"
- "Get location of shipment ABC1234567 in Lagos"

### Question Patterns

```
[QuestionWord] [Intent] [Entity] [Qualifier]*
```

**Examples**:
- "What is the status of container EFLU7896543?"
- "Where is BL ABC1234567 located?"
- "When will container EFLU7896543 arrive?"

## West African English Patterns

### Pidgin English Commands

```
"I wan check containah EFLU7896543"
"I dey find bill of laden ABC1234567"
"Wetin be status for dis containah?"
```

### Cultural Communication Patterns

#### Politeness Indicators
```
"Please sir, track container EFLU7896543"
"Please ma, check this BL number"
"Thank you, what is the status?"
```

#### Indirect Requests
```
"Can you help me check container EFLU7896543?"
"I want to know about this shipment"
"Please, I need information on BL ABC1234567"
```

#### Repetition for Emphasis
```
"Yes, yes, track container EFLU7896543"
"Confirm, confirm, that's the right number"
```

### Pronunciation Confidence Boosters

The system applies confidence boosts for:
- West African pronunciation variations (+30%)
- Local terminology usage (+15%)
- Politeness markers (+5%)
- Cultural communication patterns (+10%)

## Error Recovery Patterns

### Mispronunciation Recovery

When speech recognition confidence is low, the system:
1. Applies West African pronunciation mappings
2. Checks for local terminology variants
3. Looks for cultural context clues
4. Requests clarification if needed

**Example**:
- Input: "Track containah seven eight nine six five four three"
- Recognition: "container 7896543" (confidence boosted +30%)
- System: "I heard container EFLU7896543. Is that correct?"

### Ambiguity Resolution

When multiple interpretations are possible:
1. Present most likely interpretation
2. Ask for confirmation
3. Provide alternatives if needed

**Example**:
- Input: "Track ABC1234567"
- Possible interpretations: Container or BL
- System: "I can track that as either a container or BL number. Which would you prefer?"

## Voice Response Guidelines

### Response Length Limits
- Maximum 20 seconds for voice responses
- Aim for 10-15 seconds for optimal user experience
- Break complex information into multiple responses

### Progressive Disclosure
1. Primary information first
2. Offer additional details
3. Ask if user wants more information

**Example**:
```
System: "Container EFLU7896543 is at the terminal, cleared for examination."
User: (silence)
System: "Would you like to know the next steps?"
```

### Confirmation Patterns

For critical information:
1. State the information
2. Ask for confirmation
3. Provide fallback if unclear

**Example**:
```
System: "I heard you say container EFLU7896543. Is that correct?"
User: "Yes"
System: "Thank you. Let me check the status for you."
```

## Testing Scenarios

### West African English Test Cases

1. **Container Tracking with Local Pronunciation**
   - Input: "Track containah EFLU seven eight nine six five four three"
   - Expected: Recognize as container EFLU7896543

2. **BL Tracking with Pidgin**
   - Input: "I wan check bill of laden ABC one two three four five six seven"
   - Expected: Recognize as BL ABC1234567

3. **Status Inquiry with Cultural Patterns**
   - Input: "Please sir, wetin be the status for dis containah?"
   - Expected: Provide status information with polite response

4. **Location Query with Local Terms**
   - Input: "Where the containah dey for Lagos?"
   - Expected: Provide location information

### Pronunciation Test Matrix

| Standard | West African | Recognition | Confidence Boost |
|----------|-------------|-------------|------------------|
| Container | Containah | Container | +30% |
| Terminal | Terminah | Terminal | +20% |
| Customs | Kustoms | Customs | +30% |
| Clearance | Clearans | Clearance | +25% |
| Examination | Examinashun | Examination | +30% |

## Implementation Notes

### Speech Recognition Tuning

- **Language Model**: Weighted towards West African English patterns
- **Acoustic Model**: Trained with Nigerian English speakers
- **Vocabulary**: Extended with local logistics terminology
- **Confidence Thresholds**: Lowered for known cultural patterns

### Natural Language Processing

- **Intent Classification**: Multi-model approach with cultural context
- **Entity Extraction**: Pattern-based with pronunciation normalization
- **Context Preservation**: Maintain conversation context across turns
- **Fallback Handling**: Graceful degradation for unrecognized patterns

### Cultural Adaptation Features

- **Politeness Detection**: Recognize and respond appropriately to cultural politeness
- **Indirect Communication**: Handle indirect requests common in West African culture
- **Relationship Building**: Maintain respectful, helpful tone throughout interaction
- **Local Business Practices**: Understand and accommodate local business communication norms

## Future Enhancements

### Extended Language Support
- Support for additional West African languages (Yoruba, Hausa, Igbo)
- Code-switching detection (mixing English with local languages)
- Multi-language voice responses

### Advanced Cultural Features
- Regional accent adaptation
- Industry-specific terminology expansion
- Cultural communication style learning
- Personalized interaction patterns

---

*This grammar documentation supports Integration Standard C6 for localisation and multi-language support in EFL terminal operations.*
