/**
 * Google Apps Script - Web App to Append Summaries to Google Doc
 * 
 * Instructions:
 * 1. Open the Google Doc where you want to append summaries.
 * 2. Click Extensions > Apps Script.
 * 3. Delete any code in the editor and paste this code.
 * 4. Replace 'YOUR_DOCUMENT_ID_HERE' with your Google Doc's ID (found in the Doc's URL).
 * 5. Click Deploy > New Deployment.
 * 6. Select type: Web App.
 * 7. Description: Telegram Chat Analyser
 * 8. Execute as: Me (your email)
 * 9. Who has access: Anyone
 * 10. Click Deploy, authorize permissions, and copy the Web App URL.
 * 11. Paste the URL into your python .env file as APPS_SCRIPT_URL.
 */

// Replace this with your Google Doc ID
const DOCUMENT_ID = 'abcdefg12345';

function doPost(e) {
  try {
    // Parse the incoming JSON payload
    const data = JSON.parse(e.postData.contents);
    const paperTitle = data.title || 'Untitled Research Paper';
    const timestamp = data.timestamp || new Date().toLocaleString();
    const sender = data.sender || 'Unknown Sender';
    
    const studentSummary = data.studentSummary || 'No student summary generated.';
    const facultySummary = data.facultySummary || 'No faculty summary generated.';
    const phdSummary = data.phdSummary || 'No PhD summary generated.';
    const productSummary = data.productSummary || 'No product summary generated.';

    // Open the Document
    const doc = DocumentApp.openById(DOCUMENT_ID);
    const body = doc.getBody();
    
    // Add spacing from previous entry if body is not empty
    if (body.getText().trim().length > 0) {
      body.appendParagraph('\n\n\n').setFontSize(11);
      // Append a horizontal line separator
      body.appendHorizontalRule();
    }
    
    // 1. Header & Title Section
    const titlePara = body.appendParagraph('📄 Research Paper Analysis');
    titlePara.setHeading(DocumentApp.ParagraphHeading.HEADING1);
    titlePara.setFontFamily('Arial');
    titlePara.setFontSize(20);
    titlePara.setBold(true);
    titlePara.setForegroundColor('#1a73e8'); // Google Blue
    
    // Paper Title
    const paperPara = body.appendParagraph(`Title: "${paperTitle}"`);
    paperPara.setFontSize(14);
    paperPara.setItalic(true);
    paperPara.setBold(true);
    paperPara.setForegroundColor('#202124');
    
    // Metadata (Timestamp & Sender)
    const metaPara = body.appendParagraph(`Analyzed on: ${timestamp} | Sent by: ${sender}`);
    metaPara.setFontSize(10);
    metaPara.setItalic(true);
    metaPara.setForegroundColor('#5f6368');
    
    body.appendParagraph(''); // Space
    
    // Helper function to append a styled section
    function appendSection(title, content, headingColor) {
      const heading = body.appendParagraph(title);
      heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
      heading.setFontFamily('Arial');
      heading.setFontSize(14);
      heading.setBold(true);
      heading.setForegroundColor(headingColor);
      
      // Parse content by newlines and append paragraphs nicely
      const paragraphs = content.split('\n');
      paragraphs.forEach(function(paraText) {
        const trimmed = paraText.trim();
        if (trimmed.length > 0) {
          const para = body.appendParagraph(trimmed);
          para.setFontFamily('Arial');
          para.setFontSize(11);
          para.setLineSpacing(1.15);
          para.setForegroundColor('#3c4043');
          
          // Apply basic markdown bold styling if present
          applyFormatting(para);
        }
      });
      
      body.appendParagraph(''); // spacing
    }
    
    // Simple parser for **bold** text in Apps Script
    function applyFormatting(paragraph) {
      const text = paragraph.getText();
      const boldRegex = /\*\*(.*?)\*\*/g;
      let match;
      let offset = 0;
      
      // We operate on a copy of the text to find offsets, but since we modify
      // the paragraph in place, we need to handle formatting ranges.
      // However, modifying characters changes offsets. Instead, we can do a simplified search:
      // A cleaner way is using paragraph.editAsText().
      const textElement = paragraph.editAsText();
      let formattedText = text;
      
      // Let's do a simple formatting pass:
      // Remove double asterisks and bold the text inside them
      while ((match = boldRegex.exec(text)) !== null) {
        const cleanContent = match[1];
        const matchStart = match.index;
        const matchEnd = match.index + match[0].length;
        
        // Find in clean text
        // To be simple and robust in Apps Script:
        // We find the index of "**" + cleanContent + "**" in the current element text.
        const currentText = textElement.getText();
        const startIdx = currentText.indexOf(match[0]);
        if (startIdx !== -1) {
          const endIdx = startIdx + match[0].length;
          textElement.deleteText(startIdx, startIdx + 1); // delete first *
          textElement.deleteText(startIdx, startIdx + 1); // delete second *
          
          // Now the text is shifted, cleanContent starts at startIdx and ends at startIdx + cleanContent.length - 1
          const boldEndIdx = startIdx + cleanContent.length - 1;
          if (boldEndIdx >= startIdx) {
            textElement.setBold(startIdx, boldEndIdx, true);
          }
        }
      }
    }
    
    // Append the four summaries
    appendSection('🎓 1. Summary for Students', studentSummary, '#188038');      // Green
    appendSection('🔬 2. Summary for Faculty (PhD Candidates)', facultySummary, '#e37400'); // Orange
    appendSection('🧠 3. Summary for PhD Holders', phdSummary, '#a142f4');           // Purple
    appendSection('💼 4. Research Paper as a Product', productSummary, '#12b5cb');   // Cyan

    // Save and close to apply changes immediately
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
