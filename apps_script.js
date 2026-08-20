/**
 * Google Apps Script - Web App to Append Summaries to Google Doc
 * 
 * Instructions:
 * 1. Open the Google Doc where you want to append summaries.
 * 2. Click Extensions > Apps Script.
 * 3. Delete any code in the editor and paste this code.
 * 4. Replace 'YOUR_DOCUMENT_ID_HERE' with your Google Doc's ID.
 * 5. Click Deploy > Manage Deployments > Edit (pencil icon) > Version: New version > Deploy.
 */

// Replace this with your Google Doc ID
const DOCUMENT_ID = 'YOUR_DOCUMENT_ID_HERE';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const paperTitle = data.title || 'Untitled Research Paper';
    const timestamp = data.timestamp || new Date().toLocaleString();
    const sender = data.sender || 'Unknown Sender';
    
    const studentSummary = data.studentSummary || '';
    const facultySummary = data.facultySummary || '';
    const phdSummary = data.phdSummary || '';
    const productSummary = data.productSummary || '';

    // Open the Document
    const doc = DocumentApp.openById(DOCUMENT_ID);
    const body = doc.getBody();
    
    // Add spacing from previous entry if body is not empty
    if (body.getText().trim().length > 0) {
      body.appendParagraph('\n\n');
      body.appendHorizontalRule();
    }
    
    // 1. Header & Title Section
    const titlePara = body.appendParagraph('📄 Research Paper Analysis');
    titlePara.setHeading(DocumentApp.ParagraphHeading.HEADING1);
    titlePara.setFontFamily('Arial');
    titlePara.setFontSize(18);
    titlePara.setBold(true);
    titlePara.setForegroundColor('#1a73e8'); // Google Blue
    
    // Paper Title
    const paperPara = body.appendParagraph(`Title: "${paperTitle}"`);
    paperPara.setFontSize(13);
    paperPara.setItalic(true);
    paperPara.setBold(true);
    paperPara.setForegroundColor('#202124');
    
    // Metadata (Timestamp & Sender)
    const metaPara = body.appendParagraph(`Analyzed on: ${timestamp} | Sent by: ${sender}`);
    metaPara.setFontSize(10);
    metaPara.setItalic(true);
    metaPara.setForegroundColor('#5f6368');
    
    body.appendParagraph('');
    
    // Helper function to append a styled section with bullet points
    function appendSection(title, content, headingColor) {
      const heading = body.appendParagraph(title);
      heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
      heading.setFontFamily('Arial');
      heading.setFontSize(13);
      heading.setBold(true);
      heading.setForegroundColor(headingColor);
      
      // Normalize content to an array of lines
      var lines = [];
      if (Array.isArray(content)) {
        lines = content;
      } else if (typeof content === 'string') {
        lines = content.split('\n');
      }
      
      for (var i = 0; i < lines.length; i++) {
        var rawLine = String(lines[i] || '').trim();
        // Remove leading dash, bullet, or asterisk
        rawLine = rawLine.replace(/^[-•*]\s*/, '').trim();
        if (rawLine.length === 0) continue;
        
        // Parse bold markers and calculate clean text offsets
        var cleanText = '';
        var boldRanges = [];
        var regex = /\*\*(.*?)\*\*/g;
        var lastIdx = 0;
        var match;
        
        while ((match = regex.exec(rawLine)) !== null) {
          cleanText += rawLine.substring(lastIdx, match.index);
          var bStart = cleanText.length;
          var bContent = match[1];
          cleanText += bContent;
          var bEnd = cleanText.length - 1;
          if (bEnd >= bStart) {
            boldRanges.push({start: bStart, end: bEnd});
          }
          lastIdx = regex.lastIndex;
        }
        cleanText += rawLine.substring(lastIdx);
        // Remove any orphan/unclosed asterisks (e.g. StateM**)
        cleanText = cleanText.replace(/\*\*/g, '').trim();
        
        if (cleanText.length === 0) continue;
        
        // Append bullet item directly with text (prevents empty element exception)
        var listItem = body.appendListItem(cleanText);
        listItem.setGlyphType(DocumentApp.GlyphType.BULLET);
        listItem.setFontFamily('Arial');
        listItem.setFontSize(11);
        listItem.setLineSpacing(1.2);
        listItem.setForegroundColor('#3c4043');
        
        // Apply bold formatting to the exact matched ranges
        if (boldRanges.length > 0) {
          var textElement = listItem.editAsText();
          textElement.setBold(false);
          for (var r = 0; r < boldRanges.length; r++) {
            var range = boldRanges[r];
            if (range.start < cleanText.length && range.end < cleanText.length) {
              textElement.setBold(range.start, range.end, true);
            }
          }
        }
      }
      
      body.appendParagraph('');
    }
    
    // Append the four summaries
    appendSection('🎓 1. Summary for Students', studentSummary, '#188038');      // Green
    appendSection('🔬 2. Summary for Faculty (PhD Candidates)', facultySummary, '#e37400'); // Orange
    appendSection('🧠 3. Summary for PhD Holders', phdSummary, '#a142f4');           // Purple
    appendSection('💼 4. Research Paper as a Product', productSummary, '#12b5cb');   // Cyan

    // Save and close
    doc.saveAndClose();

    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      message: 'Analysis successfully appended to Google Doc.',
      docId: DOCUMENT_ID
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
