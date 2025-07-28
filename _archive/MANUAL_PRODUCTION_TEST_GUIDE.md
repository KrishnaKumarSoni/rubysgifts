# Manual Production Testing Guide - OpenAI Integration

**For use once authentication access is available**

## Quick Test Scenarios

### Scenario 1: Basic Functionality Test (5 minutes)

1. **Navigate** to: https://rubysgifts-ph21dum8d-krishnas-projects-cc548bc4.vercel.app
2. **Click** "Start" button
3. **Complete questionnaire** with these answers:
   - What do you call them? → Select "friend" chip + type ", Sarah"
   - Relationship? → Select "best friend" chip
   - Previous gifts? → Select "chocolate" and "books" chips
   - What they hate? → Type "spiders, loud music"
   - Complaints? → Select "work stress" chip
   - Complain about them? → Select "always late" chip
   - Budget? → Select "under 1000₹" chip
   - Limitations? → Select "eco-friendly" chip

4. **Submit** and wait for results

**✅ Success Criteria:**
- All questions completed without errors
- Submit button becomes active after all required fields filled
- Loading indicator appears during API call
- 3 gift cards appear with titles, descriptions, starters, and reactions
- Gift suggestions are relevant to the input provided
- No JavaScript errors in browser console

### Scenario 2: Chip-Only Interaction (3 minutes)

1. **Start fresh questionnaire**
2. **Use only chip selections** (no manual typing):
   - Select 2-3 chips per question
   - Verify chips auto-populate the text area
   - Ensure selected chips show orange background

**✅ Success Criteria:**
- Chip selections automatically sync to text areas
- Visual feedback (orange background) for selected chips
- Can deselect chips by clicking again
- Final answers contain all selected chip text

### Scenario 3: Manual Text Only (3 minutes)

1. **Start fresh questionnaire**
2. **Type custom answers** (ignore chips):
   - Use detailed, personalized responses
   - Test textarea functionality
   - Verify character limits (if any)

**✅ Success Criteria:**
- Can type freely in text areas
- Text persists when navigating between questions
- Submit works with custom text only

### Scenario 4: Error Handling (2 minutes)

1. **Try to submit** with empty required fields
2. **Test navigation** with incomplete questions
3. **Check network error handling** (disconnect wifi briefly during submit)

**✅ Success Criteria:**
- Clear error messages for missing required fields
- Cannot proceed to next question without completing current
- Graceful error handling for network issues
- Retry functionality works

## Detailed Validation Checklist

### OpenAI Response Quality
Check each generated gift for:
- [ ] **Relevance**: Matches relationship type and budget
- [ ] **Personalization**: Incorporates specific details from answers
- [ ] **Avoidance**: Doesn't suggest items mentioned in "hate" field
- [ ] **Completeness**: Has title, description, starter, and reaction
- [ ] **Creativity**: Not generic responses like "they will love this"

### Technical Validation
- [ ] **Response time**: < 30 seconds for gift generation
- [ ] **No errors**: Check browser console for JavaScript errors
- [ ] **Proper loading**: Loading states during API calls
- [ ] **Accessibility**: Tab navigation works through questions
- [ ] **Mobile responsive**: Test on phone/tablet if possible

### Edge Cases to Test
- [ ] **Very long answers**: Test with detailed 200+ character responses
- [ ] **Special characters**: Include emojis, accents, symbols
- [ ] **Unicode text**: Test with non-English characters
- [ ] **Browser back/forward**: Navigation doesn't break state
- [ ] **Page refresh**: During questionnaire (should show warning)

## Quick API Test (Advanced)

If you have browser dev tools access:

```javascript
// Open browser console and run:
fetch('/generate_gifts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    call_them: "friend",
    relationship: "best friend", 
    previous_gifts: "chocolate, books",
    hate: "spiders, loud music",
    complaints: "work stress",
    complain_about_them: "always late",
    budget: "under 1000₹",
    limitations: "eco-friendly"
  })
})
.then(r => r.json())
.then(data => console.log('API Response:', data))
.catch(err => console.error('API Error:', err));
```

**Expected Response:**
```json
{
  "success": true,
  "gift_ideas": [
    {
      "title": "Some Creative Gift Name",
      "description": "Detailed explanation...",
      "starter": "How to present it...",
      "reaction": "Expected reaction..."
    }
    // 2 more similar objects
  ],
  "timestamp": "2025-07-26T..."
}
```

## Performance Benchmarks

| Metric | Target | Notes |
|--------|--------|-------|
| Page Load | < 3 seconds | Initial landing page |
| Question Navigation | < 500ms | Between questions |
| Chip Selection | < 200ms | Visual feedback |
| API Response | < 30 seconds | OpenAI generation |
| Search Filter | < 300ms | Chip filtering |

## Issues to Watch For

### Critical Issues ❌
- No gift cards generated
- JavaScript errors preventing submission
- Infinite loading states
- API errors (500, 401, etc.)

### Medium Issues ⚠️
- Slow response times (>30s)
- Poor gift quality/relevance
- Chip selection bugs
- Mobile layout issues

### Minor Issues ℹ️
- Typos in generated content
- Minor UI inconsistencies
- Non-critical console warnings

## Reporting Template

```
## Test Session Report
**Date**: [DATE]
**Browser**: [Chrome/Firefox/Safari + version]
**Device**: [Desktop/Mobile/Tablet]

### Scenarios Completed:
- [ ] Basic Functionality Test
- [ ] Chip-Only Interaction  
- [ ] Manual Text Only
- [ ] Error Handling

### OpenAI Integration Results:
- Response Time: [X seconds]
- Gift Quality: [Excellent/Good/Poor]
- Personalization: [High/Medium/Low]
- Issues Found: [List any problems]

### Sample Generated Gift:
**Title**: [Gift title]
**Description**: [First 100 chars of description]
**Relevance**: [How well it matched the input]

### Overall Assessment:
✅ Production Ready / ⚠️ Issues Found / ❌ Critical Problems

### Recommendations:
[Any suggestions for improvement]
```

## Contact Information

If issues are found during testing:
1. **Screenshot** the problem
2. **Copy** any error messages
3. **Note** the exact steps to reproduce
4. **Check** browser console for technical errors
5. **Test** on different browsers if possible

This guide should enable comprehensive manual validation of the OpenAI integration once production access is available.